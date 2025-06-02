import os
import requests
from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.models.data_source import DataSource, UserDataSource, SyncLog
from src.models.food import FoodEntry, FoodItem
from datetime import datetime, timedelta

healthifyme_bp = Blueprint('healthifyme', __name__)

# HealthifyMe API endpoints (these would need to be confirmed with actual API documentation)
HEALTHIFYME_API_BASE = "https://api.healthifyme.com/v1"

@healthifyme_bp.route('/connect', methods=['POST'])
def connect_healthifyme():
    """Connect user to HealthifyMe via credentials"""
    user_id = request.json.get('user_id')
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not user_id or not username or not password:
        return jsonify({"error": "User ID, username, and password are required"}), 400
    
    # Get or create HealthifyMe data source
    healthifyme_source = DataSource.query.filter_by(name="HealthifyMe").first()
    if not healthifyme_source:
        healthifyme_source = DataSource(
            name="HealthifyMe",
            source_type="food",
            api_endpoint=HEALTHIFYME_API_BASE,
            requires_oauth=False,
            description="Food tracking, nutrition, and diet planning"
        )
        db.session.add(healthifyme_source)
        db.session.commit()
    
    # Note: In a real implementation, we would authenticate with HealthifyMe API here
    # Since we don't have actual API access, we'll simulate a successful connection
    
    # Get or create user data source connection
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data_source = UserDataSource.query.filter_by(
        user_id=user.id, 
        data_source_id=healthifyme_source.id
    ).first()
    
    if not user_data_source:
        user_data_source = UserDataSource(
            user_id=user.id,
            data_source_id=healthifyme_source.id
        )
        db.session.add(user_data_source)
    
    # Store credentials securely (in a real app, these would be encrypted)
    # For demo purposes, we're storing them as access_token and refresh_token
    user_data_source.access_token = username
    user_data_source.refresh_token = password  # Not recommended in production!
    user_data_source.is_active = True
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "HealthifyMe connected successfully"})

@healthifyme_bp.route('/sync', methods=['POST'])
def sync_healthifyme_data():
    """Manually sync HealthifyMe data for a user"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get user data source connection
    healthifyme_source = DataSource.query.filter_by(name="HealthifyMe").first()
    if not healthifyme_source:
        return jsonify({"error": "HealthifyMe data source not configured"}), 404
    
    user_data_source = UserDataSource.query.filter_by(
        user_id=user_id, 
        data_source_id=healthifyme_source.id,
        is_active=True
    ).first()
    
    if not user_data_source:
        return jsonify({"error": "User not connected to HealthifyMe"}), 404
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=healthifyme_source.id,
        sync_start_time=datetime.utcnow(),
        status="pending"
    )
    db.session.add(sync_log)
    db.session.commit()
    
    try:
        # In a real implementation, we would fetch data from HealthifyMe API here
        # Since we don't have actual API access, we'll simulate data
        
        # Get food entries from HealthifyMe (simulated)
        food_entries = simulate_healthifyme_food_data()
        
        # Process and save food entries
        items_synced = process_healthifyme_food_data(user_id, healthifyme_source.id, food_entries)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update last sync time
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully synced {items_synced} food entries from HealthifyMe"
        })
        
    except Exception as e:
        # Update sync log with error
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to sync HealthifyMe data: {str(e)}"}), 500

@healthifyme_bp.route('/upload', methods=['POST'])
def upload_healthifyme_export():
    """Upload HealthifyMe data export file"""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Get user data source connection
    healthifyme_source = DataSource.query.filter_by(name="HealthifyMe").first()
    if not healthifyme_source:
        return jsonify({"error": "HealthifyMe data source not configured"}), 404
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=healthifyme_source.id,
        sync_start_time=datetime.utcnow(),
        status="pending"
    )
    db.session.add(sync_log)
    db.session.commit()
    
    try:
        # Process the uploaded file
        # In a real implementation, we would parse the CSV/JSON export file
        # For demo purposes, we'll simulate data
        
        # Get food entries from HealthifyMe (simulated)
        food_entries = simulate_healthifyme_food_data()
        
        # Process and save food entries
        items_synced = process_healthifyme_food_data(user_id, healthifyme_source.id, food_entries)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update or create user data source connection
        user_data_source = UserDataSource.query.filter_by(
            user_id=user_id, 
            data_source_id=healthifyme_source.id
        ).first()
        
        if not user_data_source:
            user_data_source = UserDataSource(
                user_id=user_id,
                data_source_id=healthifyme_source.id,
                is_active=True
            )
            db.session.add(user_data_source)
        
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully processed {items_synced} food entries from HealthifyMe export"
        })
        
    except Exception as e:
        # Update sync log with error
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to process HealthifyMe export: {str(e)}"}), 500

def simulate_healthifyme_food_data():
    """Simulate food data from HealthifyMe for demo purposes"""
    today = datetime.utcnow().date()
    
    # Simulate a week of food entries
    food_entries = []
    
    for day_offset in range(7):
        entry_date = today - timedelta(days=day_offset)
        
        # Breakfast
        breakfast = {
            "id": f"breakfast_{entry_date.strftime('%Y%m%d')}",
            "meal_type": "breakfast",
            "consumed_at": datetime.combine(entry_date, datetime.min.time().replace(hour=8)),
            "total_calories": 450,
            "total_carbs": 65,
            "total_protein": 15,
            "total_fat": 12,
            "total_fiber": 8,
            "items": [
                {
                    "name": "Oatmeal",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 350,
                    "carbs": 60,
                    "protein": 12,
                    "fat": 8,
                    "fiber": 7
                },
                {
                    "name": "Banana",
                    "quantity": 1,
                    "unit": "serving",
                    "calories": 100,
                    "carbs": 25,
                    "protein": 1,
                    "fat": 0.3,
                    "fiber": 3
                }
            ]
        }
        
        # Lunch
        lunch = {
            "id": f"lunch_{entry_date.strftime('%Y%m%d')}",
            "meal_type": "lunch",
            "consumed_at": datetime.combine(entry_date, datetime.min.time().replace(hour=13)),
            "total_calories": 650,
            "total_carbs": 75,
            "total_protein": 35,
            "total_fat": 20,
            "total_fiber": 12,
            "items": [
                {
                    "name": "Brown Rice",
                    "quantity": 150,
                    "unit": "g",
                    "calories": 250,
                    "carbs": 55,
                    "protein": 5,
                    "fat": 2,
                    "fiber": 4
                },
                {
                    "name": "Grilled Chicken",
                    "quantity": 120,
                    "unit": "g",
                    "calories": 200,
                    "carbs": 0,
                    "protein": 30,
                    "fat": 8,
                    "fiber": 0
                },
                {
                    "name": "Mixed Vegetables",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 100,
                    "carbs": 20,
                    "protein": 5,
                    "fat": 1,
                    "fiber": 8
                }
            ]
        }
        
        # Dinner
        dinner = {
            "id": f"dinner_{entry_date.strftime('%Y%m%d')}",
            "meal_type": "dinner",
            "consumed_at": datetime.combine(entry_date, datetime.min.time().replace(hour=19)),
            "total_calories": 550,
            "total_carbs": 45,
            "total_protein": 35,
            "total_fat": 25,
            "total_fiber": 10,
            "items": [
                {
                    "name": "Quinoa",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 200,
                    "carbs": 35,
                    "protein": 8,
                    "fat": 4,
                    "fiber": 5
                },
                {
                    "name": "Salmon",
                    "quantity": 150,
                    "unit": "g",
                    "calories": 250,
                    "carbs": 0,
                    "protein": 25,
                    "fat": 15,
                    "fiber": 0
                },
                {
                    "name": "Broccoli",
                    "quantity": 100,
                    "unit": "g",
                    "calories": 100,
                    "carbs": 10,
                    "protein": 2,
                    "fat": 1,
                    "fiber": 5
                }
            ]
        }
        
        # Snack
        snack = {
            "id": f"snack_{entry_date.strftime('%Y%m%d')}",
            "meal_type": "snack",
            "consumed_at": datetime.combine(entry_date, datetime.min.time().replace(hour=16)),
            "total_calories": 200,
            "total_carbs": 25,
            "total_protein": 10,
            "total_fat": 8,
            "total_fiber": 3,
            "items": [
                {
                    "name": "Greek Yogurt",
                    "quantity": 150,
                    "unit": "g",
                    "calories": 150,
                    "carbs": 10,
                    "protein": 15,
                    "fat": 5,
                    "fiber": 0
                },
                {
                    "name": "Almonds",
                    "quantity": 20,
                    "unit": "g",
                    "calories": 120,
                    "carbs": 4,
                    "protein": 5,
                    "fat": 10,
                    "fiber": 3
                }
            ]
        }
        
        food_entries.extend([breakfast, lunch, dinner, snack])
    
    return food_entries

def process_healthifyme_food_data(user_id, source_id, food_entries):
    """Process and save HealthifyMe food data to database"""
    count = 0
    
    for entry_data in food_entries:
        # Check if food entry already exists
        existing = FoodEntry.query.filter_by(
            user_id=user_id,
            source_id=source_id,
            external_id=entry_data.get('id')
        ).first()
        
        if existing:
            # Update existing food entry
            existing.meal_type = entry_data.get('meal_type')
            existing.consumed_at = entry_data.get('consumed_at')
            existing.total_calories = entry_data.get('total_calories')
            existing.total_carbs = entry_data.get('total_carbs')
            existing.total_protein = entry_data.get('total_protein')
            existing.total_fat = entry_data.get('total_fat')
            existing.total_fiber = entry_data.get('total_fiber')
            existing.updated_at = datetime.utcnow()
            
            # Remove existing food items
            for item in existing.food_items:
                db.session.delete(item)
            
            # Add new food items
            for item_data in entry_data.get('items', []):
                food_item = FoodItem(
                    food_entry_id=existing.id,
                    name=item_data.get('name'),
                    quantity=item_data.get('quantity'),
                    unit=item_data.get('unit'),
                    calories=item_data.get('calories'),
                    carbs=item_data.get('carbs'),
                    protein=item_data.get('protein'),
                    fat=item_data.get('fat'),
                    fiber=item_data.get('fiber')
                )
                db.session.add(food_item)
        else:
            # Create new food entry
            food_entry = FoodEntry(
                user_id=user_id,
                source_id=source_id,
                external_id=entry_data.get('id'),
                meal_type=entry_data.get('meal_type'),
                consumed_at=entry_data.get('consumed_at'),
                total_calories=entry_data.get('total_calories'),
                total_carbs=entry_data.get('total_carbs'),
                total_protein=entry_data.get('total_protein'),
                total_fat=entry_data.get('total_fat'),
                total_fiber=entry_data.get('total_fiber')
            )
            db.session.add(food_entry)
            db.session.flush()  # Get the ID for the new food entry
            
            # Add food items
            for item_data in entry_data.get('items', []):
                food_item = FoodItem(
                    food_entry_id=food_entry.id,
                    name=item_data.get('name'),
                    quantity=item_data.get('quantity'),
                    unit=item_data.get('unit'),
                    calories=item_data.get('calories'),
                    carbs=item_data.get('carbs'),
                    protein=item_data.get('protein'),
                    fat=item_data.get('fat'),
                    fiber=item_data.get('fiber')
                )
                db.session.add(food_item)
            
            count += 1
    
    db.session.commit()
    return count
