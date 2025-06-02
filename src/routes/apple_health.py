import os
import json
from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.models.data_source import DataSource, UserDataSource, SyncLog
from src.models.sleep import SleepRecord
from datetime import datetime, timedelta

apple_health_bp = Blueprint('apple_health', __name__)

# Configure upload folder for Apple Health exports
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'apple_health')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@apple_health_bp.route('/upload', methods=['POST'])
def upload_apple_health_export():
    """Upload and process Apple Health export file"""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith(('.xml', '.zip')):
        return jsonify({"error": "Only XML or ZIP files are supported"}), 400
    
    # Get user
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get or create Apple Health data source
    apple_health_source = DataSource.query.filter_by(name="Apple Health").first()
    if not apple_health_source:
        apple_health_source = DataSource(
            name="Apple Health",
            source_type="sleep",
            requires_oauth=False,
            description="Sleep tracking, heart rate, and general health metrics"
        )
        db.session.add(apple_health_source)
        db.session.commit()
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=apple_health_source.id,
        sync_start_time=datetime.utcnow(),
        status="pending"
    )
    db.session.add(sync_log)
    db.session.commit()
    
    try:
        # Save the file
        filename = f"{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Process the file
        # In a real implementation, we would parse the XML file
        # For demo purposes, we'll simulate sleep data
        sleep_records = simulate_apple_health_sleep_data(user_id)
        
        # Process and save sleep records
        items_synced = process_apple_health_sleep_data(user_id, apple_health_source.id, sleep_records)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update or create user data source connection
        user_data_source = UserDataSource.query.filter_by(
            user_id=user_id, 
            data_source_id=apple_health_source.id
        ).first()
        
        if not user_data_source:
            user_data_source = UserDataSource(
                user_id=user_id,
                data_source_id=apple_health_source.id,
                is_active=True
            )
            db.session.add(user_data_source)
        
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully processed {items_synced} sleep records from Apple Health export"
        })
        
    except Exception as e:
        # Update sync log with error
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to process Apple Health export: {str(e)}"}), 500

@apple_health_bp.route('/connect_device', methods=['POST'])
def connect_device():
    """Connect to a sleep tracking device (Oura, Fitbit, etc.)"""
    user_id = request.json.get('user_id')
    device_type = request.json.get('device_type')
    credentials = request.json.get('credentials', {})
    
    if not user_id or not device_type:
        return jsonify({"error": "User ID and device type are required"}), 400
    
    # Get user
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get or create device data source
    device_source = DataSource.query.filter_by(name=device_type).first()
    if not device_source:
        device_source = DataSource(
            name=device_type,
            source_type="sleep",
            requires_oauth=True,
            description=f"Sleep tracking via {device_type}"
        )
        db.session.add(device_source)
        db.session.commit()
    
    # Create or update user data source connection
    user_data_source = UserDataSource.query.filter_by(
        user_id=user_id, 
        data_source_id=device_source.id
    ).first()
    
    if not user_data_source:
        user_data_source = UserDataSource(
            user_id=user_id,
            data_source_id=device_source.id
        )
        db.session.add(user_data_source)
    
    # Store credentials (in a real app, these would be encrypted)
    user_data_source.access_token = credentials.get('access_token')
    user_data_source.refresh_token = credentials.get('refresh_token')
    user_data_source.is_active = True
    
    db.session.commit()
    
    # In a real implementation, we would sync data from the device
    # For demo purposes, we'll simulate sleep data
    try:
        sleep_records = simulate_apple_health_sleep_data(user_id)
        items_synced = process_apple_health_sleep_data(user_id, device_source.id, sleep_records)
        
        user_data_source.last_sync_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully connected to {device_type} and synced {items_synced} sleep records"
        })
    except Exception as e:
        return jsonify({"error": f"Failed to sync data from {device_type}: {str(e)}"}), 500

@apple_health_bp.route('/sync', methods=['POST'])
def sync_sleep_data():
    """Manually sync sleep data for a user"""
    user_id = request.json.get('user_id')
    source_name = request.json.get('source_name', 'Apple Health')
    
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get data source
    data_source = DataSource.query.filter_by(name=source_name).first()
    if not data_source:
        return jsonify({"error": f"{source_name} data source not configured"}), 404
    
    # Get user data source connection
    user_data_source = UserDataSource.query.filter_by(
        user_id=user_id, 
        data_source_id=data_source.id,
        is_active=True
    ).first()
    
    if not user_data_source:
        return jsonify({"error": f"User not connected to {source_name}"}), 404
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=data_source.id,
        sync_start_time=datetime.utcnow(),
        status="pending"
    )
    db.session.add(sync_log)
    db.session.commit()
    
    try:
        # In a real implementation, we would fetch data from the device/API
        # For demo purposes, we'll simulate sleep data
        sleep_records = simulate_apple_health_sleep_data(user_id)
        
        # Process and save sleep records
        items_synced = process_apple_health_sleep_data(user_id, data_source.id, sleep_records)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update last sync time
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully synced {items_synced} sleep records from {source_name}"
        })
        
    except Exception as e:
        # Update sync log with error
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to sync sleep data: {str(e)}"}), 500

def simulate_apple_health_sleep_data(user_id):
    """Simulate sleep data from Apple Health for demo purposes"""
    today = datetime.utcnow().date()
    
    # Simulate a week of sleep records
    sleep_records = []
    
    for day_offset in range(7):
        sleep_date = today - timedelta(days=day_offset)
        
        # Generate a sleep record for each night
        sleep_start = datetime.combine(sleep_date - timedelta(days=1), datetime.min.time().replace(hour=23, minute=30))
        sleep_end = datetime.combine(sleep_date, datetime.min.time().replace(hour=7, minute=15))
        
        # Add some variation
        sleep_start = sleep_start + timedelta(minutes=day_offset * 5)
        sleep_end = sleep_end + timedelta(minutes=day_offset * 3)
        
        total_duration = int((sleep_end - sleep_start).total_seconds())
        
        # Calculate sleep phases (simplified)
        deep_sleep = int(total_duration * 0.25)  # 25% deep sleep
        rem_sleep = int(total_duration * 0.20)   # 20% REM sleep
        light_sleep = int(total_duration * 0.45)  # 45% light sleep
        awake = total_duration - deep_sleep - rem_sleep - light_sleep  # 10% awake
        
        # Generate heart rate data
        heart_rate_avg = 58 + day_offset
        heart_rate_min = heart_rate_avg - 5
        heart_rate_max = heart_rate_avg + 15
        
        # Generate sleep score (0-100)
        sleep_score = 85 - (day_offset * 3)
        
        sleep_record = {
            "id": f"sleep_{sleep_date.strftime('%Y%m%d')}",
            "start_time": sleep_start,
            "end_time": sleep_end,
            "duration": total_duration,
            "deep_sleep_duration": deep_sleep,
            "light_sleep_duration": light_sleep,
            "rem_sleep_duration": rem_sleep,
            "awake_duration": awake,
            "sleep_score": sleep_score,
            "heart_rate_avg": heart_rate_avg,
            "heart_rate_min": heart_rate_min,
            "heart_rate_max": heart_rate_max,
            "respiratory_rate_avg": 15.5 + (day_offset * 0.2)
        }
        
        sleep_records.append(sleep_record)
    
    return sleep_records

def process_apple_health_sleep_data(user_id, source_id, sleep_records):
    """Process and save Apple Health sleep data to database"""
    count = 0
    
    for record_data in sleep_records:
        # Check if sleep record already exists
        existing = SleepRecord.query.filter_by(
            user_id=user_id,
            source_id=source_id,
            external_id=record_data.get('id')
        ).first()
        
        if existing:
            # Update existing sleep record
            existing.start_time = record_data.get('start_time')
            existing.end_time = record_data.get('end_time')
            existing.duration = record_data.get('duration')
            existing.deep_sleep_duration = record_data.get('deep_sleep_duration')
            existing.light_sleep_duration = record_data.get('light_sleep_duration')
            existing.rem_sleep_duration = record_data.get('rem_sleep_duration')
            existing.awake_duration = record_data.get('awake_duration')
            existing.sleep_score = record_data.get('sleep_score')
            existing.heart_rate_avg = record_data.get('heart_rate_avg')
            existing.heart_rate_min = record_data.get('heart_rate_min')
            existing.heart_rate_max = record_data.get('heart_rate_max')
            existing.respiratory_rate_avg = record_data.get('respiratory_rate_avg')
            existing.updated_at = datetime.utcnow()
        else:
            # Create new sleep record
            sleep_record = SleepRecord(
                user_id=user_id,
                source_id=source_id,
                external_id=record_data.get('id'),
                start_time=record_data.get('start_time'),
                end_time=record_data.get('end_time'),
                duration=record_data.get('duration'),
                deep_sleep_duration=record_data.get('deep_sleep_duration'),
                light_sleep_duration=record_data.get('light_sleep_duration'),
                rem_sleep_duration=record_data.get('rem_sleep_duration'),
                awake_duration=record_data.get('awake_duration'),
                sleep_score=record_data.get('sleep_score'),
                heart_rate_avg=record_data.get('heart_rate_avg'),
                heart_rate_min=record_data.get('heart_rate_min'),
                heart_rate_max=record_data.get('heart_rate_max'),
                respiratory_rate_avg=record_data.get('respiratory_rate_avg')
            )
            db.session.add(sleep_record)
            count += 1
    
    db.session.commit()
    return count
