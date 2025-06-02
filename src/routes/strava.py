import os
import requests
from flask import Blueprint, request, jsonify, current_app, redirect, url_for, render_template
from src.models.user import db, User
from src.models.data_source import DataSource, UserDataSource, SyncLog
from src.models.activity import Activity
from datetime import datetime, timedelta
import logging
import json

strava_bp = Blueprint('strava', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Strava API endpoints
STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"

# Strava API credentials
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID', '12345')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET', 'your_client_secret')

@strava_bp.route('/auth', methods=['GET'])
def strava_auth():
    """Generate Strava authorization URL"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get or create Strava data source
    strava_source = DataSource.query.filter_by(name="Strava").first()
    if not strava_source:
        strava_source = DataSource(
            name="Strava",
            source_type="activity",
            api_endpoint=STRAVA_API_BASE,
            requires_oauth=True,
            oauth_url=STRAVA_AUTH_URL,
            description="Activity tracking for running, cycling, and more"
        )
        db.session.add(strava_source)
        db.session.commit()
    
    # Generate authorization URL with exact redirect URI
    # Use absolute URL to ensure it matches exactly what's registered in Strava
    redirect_uri = request.host_url.rstrip('/') + '/api/strava/callback'
    scope = 'read,activity:read_all'
    
    logger.info(f"Generated redirect URI: {redirect_uri}")
    
    auth_url = f"{STRAVA_AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope={scope}&state={user_id}"
    
    return jsonify({"auth_url": auth_url})

@strava_bp.route('/callback', methods=['GET'])
def strava_callback():
    """Handle Strava OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')  # This is the user_id
    error = request.args.get('error')
    
    # Log all incoming parameters for debugging
    logger.info(f"Strava callback received - code: {'present' if code else 'missing'}, state: {state}, error: {error}")
    
    if error:
        logger.error(f"Strava authorization error: {error}")
        return redirect('/#/data-sources?status=error&message=' + error)
    
    if not code or not state:
        logger.error("Missing code or state parameter")
        return redirect('/#/data-sources?status=error&message=Missing required parameters')
    
    # Get the exact redirect URI that was used in the authorization request
    redirect_uri = request.host_url.rstrip('/') + '/api/strava/callback'
    logger.info(f"Using redirect URI for token exchange: {redirect_uri}")
    
    # Exchange code for token using application/x-www-form-urlencoded content type
    try:
        # Prepare token request with all required parameters
        token_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': redirect_uri  # Include redirect_uri in token request
        }
        
        # Log the token request data (excluding client_secret)
        safe_log_data = token_data.copy()
        safe_log_data['client_secret'] = '[REDACTED]'
        logger.info(f"Token request data: {safe_log_data}")
        
        # Make the POST request with proper content type
        token_response = requests.post(
            STRAVA_TOKEN_URL, 
            data=token_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        # Log response status and headers
        logger.info(f"Token response status: {token_response.status_code}")
        logger.info(f"Token response headers: {token_response.headers}")
        
        # Check for successful response
        if token_response.status_code != 200:
            error_message = f"Failed to exchange code for token: {token_response.text}"
            logger.error(error_message)
            return redirect(f'/#/data-sources?status=error&message=Token exchange failed: {token_response.text}')
        
        # Parse token response
        try:
            token_data = token_response.json()
            logger.info("Successfully parsed token response")
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse token response: {str(e)}"
            logger.error(error_message)
            return redirect(f'/#/data-sources?status=error&message={error_message}')
        
        # Get or create user data source connection
        user = User.query.get(state)
        if not user:
            logger.error(f"User not found with ID: {state}")
            return redirect('/#/data-sources?status=error&message=User not found')
        
        strava_source = DataSource.query.filter_by(name="Strava").first()
        
        user_data_source = UserDataSource.query.filter_by(
            user_id=user.id, 
            data_source_id=strava_source.id
        ).first()
        
        if not user_data_source:
            user_data_source = UserDataSource(
                user_id=user.id,
                data_source_id=strava_source.id
            )
            db.session.add(user_data_source)
        
        # Update tokens
        user_data_source.access_token = token_data.get('access_token')
        user_data_source.refresh_token = token_data.get('refresh_token')
        user_data_source.token_expires_at = datetime.fromtimestamp(token_data.get('expires_at'))
        user_data_source.is_active = True
        
        db.session.commit()
        logger.info(f"Successfully stored Strava tokens for user {user.id}")
        
        # Redirect to frontend with success message
        return redirect('/#/data-sources?status=success&source=strava')
        
    except Exception as e:
        error_message = f"Exception during token exchange: {str(e)}"
        logger.error(error_message)
        return redirect(f'/#/data-sources?status=error&message={error_message}')

@strava_bp.route('/sync', methods=['POST'])
def sync_strava_data():
    """Manually sync Strava data for a user"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    logger.info(f"Starting Strava sync for user {user_id}")
    
    # Get user data source connection
    strava_source = DataSource.query.filter_by(name="Strava").first()
    if not strava_source:
        logger.error("Strava data source not configured")
        return jsonify({"error": "Strava data source not configured"}), 404
    
    user_data_source = UserDataSource.query.filter_by(
        user_id=user_id, 
        data_source_id=strava_source.id,
        is_active=True
    ).first()
    
    if not user_data_source:
        logger.error(f"User {user_id} not connected to Strava")
        return jsonify({"error": "User not connected to Strava"}), 404
    
    # Check if token is expired and refresh if needed
    if user_data_source.token_expires_at and user_data_source.token_expires_at < datetime.utcnow():
        logger.info(f"Refreshing expired Strava token for user {user_id}")
        refresh_result = refresh_strava_token(user_data_source)
        if not refresh_result['success']:
            logger.error(f"Failed to refresh Strava token: {refresh_result['error']}")
            return jsonify({"error": f"Failed to refresh Strava token: {refresh_result['error']}"}), 401
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=strava_source.id,
        sync_start_time=datetime.utcnow(),
        status="pending"
    )
    db.session.add(sync_log)
    db.session.commit()
    
    try:
        # Get activities from Strava
        logger.info(f"Fetching Strava activities for user {user_id}")
        activities_result = fetch_strava_activities(user_data_source.access_token)
        
        if not activities_result['success']:
            raise Exception(activities_result['error'])
            
        activities = activities_result['data']
        
        # Process and save activities
        logger.info(f"Processing {len(activities)} Strava activities for user {user_id}")
        items_synced = process_strava_activities(user_id, strava_source.id, activities)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update last sync time
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f"Successfully synced {items_synced} activities from Strava for user {user_id}")
        return jsonify({
            "success": True, 
            "message": f"Successfully synced {items_synced} activities from Strava"
        })
        
    except Exception as e:
        # Update sync log with error
        logger.error(f"Failed to sync Strava data for user {user_id}: {str(e)}")
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to sync Strava data: {str(e)}"}), 500

@strava_bp.route('/activities', methods=['GET'])
def get_activities():
    """Get Strava activities for a user"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get Strava data source
    strava_source = DataSource.query.filter_by(name="Strava").first()
    if not strava_source:
        return jsonify({"error": "Strava data source not configured"}), 404
    
    # Get activities
    activities = Activity.query.filter_by(
        user_id=user_id,
        source_id=strava_source.id
    ).order_by(Activity.start_time.desc()).all()
    
    # Convert to JSON
    activities_json = []
    for activity in activities:
        activities_json.append({
            "id": activity.id,
            "external_id": activity.external_id,
            "type": activity.activity_type,
            "name": activity.title,
            "description": activity.description,
            "start_date": activity.start_time.isoformat() if activity.start_time else None,
            "end_date": activity.end_time.isoformat() if activity.end_time else None,
            "elapsed_time": activity.duration,
            "distance": activity.distance,
            "calories": activity.calories,
            "average_heartrate": activity.average_heart_rate,
            "max_heartrate": activity.max_heart_rate,
            "total_elevation_gain": activity.elevation_gain
        })
    
    return jsonify({
        "success": True,
        "activities": activities_json
    })

@strava_bp.route('/status', methods=['GET'])
def get_status():
    """Get Strava connection status for a user"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get Strava data source
    strava_source = DataSource.query.filter_by(name="Strava").first()
    if not strava_source:
        return jsonify({"error": "Strava data source not configured"}), 404
    
    # Get user data source connection
    user_data_source = UserDataSource.query.filter_by(
        user_id=user_id, 
        data_source_id=strava_source.id
    ).first()
    
    if not user_data_source or not user_data_source.is_active:
        return jsonify({
            "connected": False,
            "message": "Not connected to Strava"
        })
    
    # Check if token is expired
    token_expired = user_data_source.token_expires_at and user_data_source.token_expires_at < datetime.utcnow()
    
    # Get last sync time
    last_sync = user_data_source.last_sync_at.isoformat() if user_data_source.last_sync_at else None
    
    # Get activity count
    activity_count = Activity.query.filter_by(
        user_id=user_id,
        source_id=strava_source.id
    ).count()
    
    return jsonify({
        "connected": True,
        "token_expired": token_expired,
        "last_sync": last_sync,
        "activity_count": activity_count
    })

def refresh_strava_token(user_data_source):
    """Refresh Strava access token"""
    try:
        # Prepare refresh token request
        refresh_data = {
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'refresh_token': user_data_source.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        # Log the refresh request (excluding client_secret)
        safe_log_data = refresh_data.copy()
        safe_log_data['client_secret'] = '[REDACTED]'
        logger.info(f"Token refresh request data: {safe_log_data}")
        
        # Make the POST request with proper content type
        token_response = requests.post(
            STRAVA_TOKEN_URL, 
            data=refresh_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        
        # Log response status
        logger.info(f"Token refresh response status: {token_response.status_code}")
        
        if token_response.status_code != 200:
            error_message = f"Failed to refresh token: {token_response.text}"
            logger.error(error_message)
            return {'success': False, 'error': error_message}
        
        # Parse token response
        try:
            token_data = token_response.json()
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse refresh token response: {str(e)}"
            logger.error(error_message)
            return {'success': False, 'error': error_message}
        
        # Update tokens in database
        user_data_source.access_token = token_data.get('access_token')
        user_data_source.refresh_token = token_data.get('refresh_token')
        user_data_source.token_expires_at = datetime.fromtimestamp(token_data.get('expires_at'))
        
        db.session.commit()
        logger.info("Successfully refreshed Strava token")
        return {'success': True}
        
    except Exception as e:
        error_message = f"Exception during token refresh: {str(e)}"
        logger.error(error_message)
        return {'success': False, 'error': error_message}

def fetch_strava_activities(access_token, after=None):
    """Fetch activities from Strava API"""
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Default to last 30 days if no date provided
        if not after:
            after = int((datetime.utcnow() - timedelta(days=30)).timestamp())
        
        params = {
            "after": after,
            "per_page": 100  # Maximum allowed by Strava
        }
        
        logger.info(f"Fetching activities with params: {params}")
        
        response = requests.get(f"{STRAVA_API_BASE}/athlete/activities", headers=headers, params=params)
        
        # Log response status
        logger.info(f"Activities fetch response status: {response.status_code}")
        
        if response.status_code != 200:
            error_message = f"Failed to fetch activities: {response.text}"
            logger.error(error_message)
            return {'success': False, 'error': error_message}
        
        # Parse response
        try:
            activities = response.json()
            logger.info(f"Successfully fetched {len(activities)} activities")
            return {'success': True, 'data': activities}
        except json.JSONDecodeError as e:
            error_message = f"Failed to parse activities response: {str(e)}"
            logger.error(error_message)
            return {'success': False, 'error': error_message}
            
    except Exception as e:
        error_message = f"Exception during activities fetch: {str(e)}"
        logger.error(error_message)
        return {'success': False, 'error': error_message}

def process_strava_activities(user_id, source_id, activities):
    """Process and save Strava activities to database"""
    count = 0
    
    for activity_data in activities:
        try:
            # Check if activity already exists
            existing = Activity.query.filter_by(
                user_id=user_id,
                source_id=source_id,
                external_id=str(activity_data.get('id'))
            ).first()
            
            if existing:
                # Update existing activity
                existing.activity_type = activity_data.get('type', '').lower()
                existing.start_time = datetime.strptime(activity_data.get('start_date'), "%Y-%m-%dT%H:%M:%SZ")
                existing.duration = activity_data.get('elapsed_time')
                existing.distance = activity_data.get('distance')
                existing.calories = activity_data.get('calories')
                existing.average_heart_rate = activity_data.get('average_heartrate')
                existing.max_heart_rate = activity_data.get('max_heartrate')
                existing.elevation_gain = activity_data.get('total_elevation_gain')
                existing.title = activity_data.get('name')
                existing.description = activity_data.get('description')
                existing.updated_at = datetime.utcnow()
            else:
                # Create new activity
                activity = Activity(
                    user_id=user_id,
                    source_id=source_id,
                    external_id=str(activity_data.get('id')),
                    activity_type=activity_data.get('type', '').lower(),
                    start_time=datetime.strptime(activity_data.get('start_date'), "%Y-%m-%dT%H:%M:%SZ"),
                    duration=activity_data.get('elapsed_time'),
                    distance=activity_data.get('distance'),
                    calories=activity_data.get('calories'),
                    average_heart_rate=activity_data.get('average_heartrate'),
                    max_heart_rate=activity_data.get('max_heartrate'),
                    elevation_gain=activity_data.get('total_elevation_gain'),
                    title=activity_data.get('name'),
                    description=activity_data.get('description')
                )
                
                # Add end time if available
                if activity.start_time and activity.duration:
                    activity.end_time = activity.start_time + timedelta(seconds=activity.duration)
                
                db.session.add(activity)
                count += 1
        except Exception as e:
            logger.error(f"Error processing activity {activity_data.get('id')}: {str(e)}")
            # Continue processing other activities
            continue
    
    db.session.commit()
    return count
