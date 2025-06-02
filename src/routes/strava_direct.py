import os
import requests
from flask import Blueprint, jsonify, current_app
from datetime import datetime, timedelta
import logging

strava_direct_bp = Blueprint('strava_direct', __name__)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Strava API credentials
CLIENT_ID = "162438"
CLIENT_SECRET = "c749fe341837025381598173baae43e5baae9201"
REFRESH_TOKEN = "6ecba6a50038cd87e9bb054c8e9860a420bd97f5"

@strava_direct_bp.route('/fetch', methods=['GET'])
def fetch_strava_data():
    """Fetch Strava data directly using refresh token"""
    try:
        # Step 1: Refresh Access Token
        logger.info("Refreshing Strava access token")
        token_url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "scope": "activity:read_all,read"  # Explicitly request required scopes
        }

        token_response = requests.post(token_url, data=payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data["access_token"]
        logger.info("Successfully refreshed Strava access token")

        # Step 2: Fetch Activities
        logger.info("Fetching Strava activities")
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"per_page": 20, "page": 1}

        activities_response = requests.get(activities_url, headers=headers, params=params)
        activities_response.raise_for_status()
        activities = activities_response.json()
        logger.info(f"Successfully fetched {len(activities)} activities")

        # Step 3: Format activities for display
        formatted_activities = []
        for act in activities:
            formatted_activities.append({
                "date": act.get("start_date_local", "")[:10],
                "type": act.get("type", "Unknown"),
                "distance": round(act.get("distance", 0) / 1000, 2),
                "duration": round(act.get("moving_time", 0) / 60, 1),
                "heart_rate": act.get("average_heartrate", "N/A"),
                "name": act.get("name", "Unnamed Activity"),
                "elevation_gain": act.get("total_elevation_gain", 0)
            })

        return jsonify({
            "success": True,
            "activities": formatted_activities
        })

    except Exception as e:
        logger.error(f"Error fetching Strava data: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to fetch Strava data: {str(e)}"
        }), 500

@strava_direct_bp.route('/chart-data', methods=['GET'])
def get_chart_data():
    """Get formatted Strava data for charts"""
    try:
        # Step 1: Refresh Access Token
        logger.info("Refreshing Strava access token for chart data")
        token_url = "https://www.strava.com/oauth/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "scope": "activity:read_all,read"  # Explicitly request required scopes
        }

        token_response = requests.post(token_url, data=payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data["access_token"]
        logger.info("Successfully refreshed Strava access token")

        # Step 2: Fetch Activities for the last 30 days (more data for better charts)
        logger.info("Fetching Strava activities for charts")
        activities_url = "https://www.strava.com/api/v3/athlete/activities"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # Get timestamp for 30 days ago
        thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
        params = {
            "after": thirty_days_ago,
            "per_page": 30  # Get more activities for better chart data
        }

        activities_response = requests.get(activities_url, headers=headers, params=params)
        activities_response.raise_for_status()
        activities = activities_response.json()
        logger.info(f"Successfully fetched {len(activities)} activities for charts")

        # Step 3: Process data for different chart types
        
        # Sort activities by date
        activities.sort(key=lambda x: x.get("start_date_local", ""))
        
        # Extract data for charts
        dates = []
        heart_rates = []
        speeds = []
        calories = []
        distances = []
        durations = []
        elevation_gains = []
        activity_types = []
        
        for act in activities:
            # Get date in readable format
            date = act.get("start_date_local", "")[:10]
            dates.append(date)
            
            # Heart rate data
            heart_rate = act.get("average_heartrate")
            heart_rates.append(heart_rate if heart_rate is not None else None)
            
            # Speed calculation (m/s converted to km/h)
            distance = act.get("distance", 0)  # in meters
            duration = act.get("moving_time", 0)  # in seconds
            
            if duration > 0:
                speed_kmh = (distance / 1000) / (duration / 3600)
                speeds.append(round(speed_kmh, 2))
            else:
                speeds.append(None)
            
            # Calories
            calorie = act.get("calories")
            calories.append(calorie if calorie is not None else None)
            
            # Distance in km
            distances.append(round(distance / 1000, 2))
            
            # Duration in minutes
            durations.append(round(duration / 60, 1))
            
            # Elevation gain
            elevation_gain = act.get("total_elevation_gain", 0)
            elevation_gains.append(elevation_gain)
            
            # Activity type
            activity_types.append(act.get("type", "Unknown"))
        
        # Create datasets for each chart type
        heart_rate_data = {
            "labels": dates,
            "datasets": [{
                "label": "Heart Rate (bpm)",
                "data": heart_rates,
                "borderColor": "rgba(255, 99, 132, 1)",
                "backgroundColor": "rgba(255, 99, 132, 0.2)",
                "fill": False
            }]
        }
        
        speed_data = {
            "labels": dates,
            "datasets": [{
                "label": "Speed (km/h)",
                "data": speeds,
                "borderColor": "rgba(54, 162, 235, 1)",
                "backgroundColor": "rgba(54, 162, 235, 0.2)",
                "fill": False
            }]
        }
        
        calories_data = {
            "labels": dates,
            "datasets": [{
                "label": "Calories Burned",
                "data": calories,
                "borderColor": "rgba(255, 159, 64, 1)",
                "backgroundColor": "rgba(255, 159, 64, 0.2)",
                "fill": False
            }]
        }
        
        distance_data = {
            "labels": dates,
            "datasets": [{
                "label": "Distance (km)",
                "data": distances,
                "borderColor": "rgba(75, 192, 192, 1)",
                "backgroundColor": "rgba(75, 192, 192, 0.2)",
                "fill": False
            }]
        }
        
        duration_data = {
            "labels": dates,
            "datasets": [{
                "label": "Duration (min)",
                "data": durations,
                "borderColor": "rgba(153, 102, 255, 1)",
                "backgroundColor": "rgba(153, 102, 255, 0.2)",
                "fill": False
            }]
        }
        
        elevation_data = {
            "labels": dates,
            "datasets": [{
                "label": "Elevation Gain (m)",
                "data": elevation_gains,
                "borderColor": "rgba(255, 206, 86, 1)",
                "backgroundColor": "rgba(255, 206, 86, 0.2)",
                "fill": False
            }]
        }
        
        # Activity type distribution
        activity_type_counts = {}
        for activity_type in activity_types:
            if activity_type in activity_type_counts:
                activity_type_counts[activity_type] += 1
            else:
                activity_type_counts[activity_type] = 1
        
        activity_distribution = {
            "labels": list(activity_type_counts.keys()),
            "datasets": [{
                "label": "Activity Types",
                "data": list(activity_type_counts.values()),
                "backgroundColor": [
                    "rgba(255, 99, 132, 0.6)",
                    "rgba(54, 162, 235, 0.6)",
                    "rgba(255, 206, 86, 0.6)",
                    "rgba(75, 192, 192, 0.6)",
                    "rgba(153, 102, 255, 0.6)",
                    "rgba(255, 159, 64, 0.6)",
                    "rgba(199, 199, 199, 0.6)"
                ]
            }]
        }
        
        # Return all chart data
        return jsonify({
            "success": True,
            "heart_rate": heart_rate_data,
            "speed": speed_data,
            "calories": calories_data,
            "distance": distance_data,
            "duration": duration_data,
            "elevation": elevation_data,
            "activity_distribution": activity_distribution,
            "raw_data": {
                "dates": dates,
                "heart_rates": heart_rates,
                "speeds": speeds,
                "calories": calories,
                "distances": distances,
                "durations": durations,
                "elevation_gains": elevation_gains,
                "activity_types": activity_types
            }
        })

    except Exception as e:
        logger.error(f"Error fetching chart data: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to fetch chart data: {str(e)}"
        }), 500
