import os
import requests
from flask import Blueprint, jsonify, current_app
from datetime import datetime
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
            "refresh_token": REFRESH_TOKEN
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
