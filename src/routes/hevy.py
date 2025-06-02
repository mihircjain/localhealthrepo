import os
from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.models.data_source import DataSource, UserDataSource, SyncLog
from src.models.workout import Workout, Exercise, WorkoutExercise
from datetime import datetime, timedelta
import json

hevy_bp = Blueprint('hevy', __name__)

# Configure upload folder for Hevy exports
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'hevy')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@hevy_bp.route('/connect', methods=['POST'])
def connect_hevy():
    """Connect user to Hevy via credentials"""
    user_id = request.json.get('user_id')
    username = request.json.get('username')
    password = request.json.get('password')
    
    if not user_id or not username or not password:
        return jsonify({"error": "User ID, username, and password are required"}), 400
    
    # Get or create Hevy data source
    hevy_source = DataSource.query.filter_by(name="Hevy").first()
    if not hevy_source:
        hevy_source = DataSource(
            name="Hevy",
            source_type="workout",
            requires_oauth=False,
            description="Workout tracking, strength training, and exercise logs"
        )
        db.session.add(hevy_source)
        db.session.commit()
    
    # Note: In a real implementation, we would authenticate with Hevy API here
    # Since we don't have actual API access, we'll simulate a successful connection
    
    # Get or create user data source connection
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user_data_source = UserDataSource.query.filter_by(
        user_id=user.id, 
        data_source_id=hevy_source.id
    ).first()
    
    if not user_data_source:
        user_data_source = UserDataSource(
            user_id=user.id,
            data_source_id=hevy_source.id
        )
        db.session.add(user_data_source)
    
    # Store credentials securely (in a real app, these would be encrypted)
    user_data_source.access_token = username
    user_data_source.refresh_token = password  # Not recommended in production!
    user_data_source.is_active = True
    
    db.session.commit()
    
    return jsonify({"success": True, "message": "Hevy connected successfully"})

@hevy_bp.route('/upload', methods=['POST'])
def upload_hevy_export():
    """Upload and process Hevy export file"""
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not file.filename.lower().endswith(('.json', '.csv')):
        return jsonify({"error": "Only JSON or CSV files are supported"}), 400
    
    # Get user
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get or create Hevy data source
    hevy_source = DataSource.query.filter_by(name="Hevy").first()
    if not hevy_source:
        hevy_source = DataSource(
            name="Hevy",
            source_type="workout",
            requires_oauth=False,
            description="Workout tracking, strength training, and exercise logs"
        )
        db.session.add(hevy_source)
        db.session.commit()
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=hevy_source.id,
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
        # In a real implementation, we would parse the JSON/CSV file
        # For demo purposes, we'll simulate workout data
        workouts = simulate_hevy_workout_data(user_id)
        
        # Process and save workouts
        items_synced = process_hevy_workout_data(user_id, hevy_source.id, workouts)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update or create user data source connection
        user_data_source = UserDataSource.query.filter_by(
            user_id=user_id, 
            data_source_id=hevy_source.id
        ).first()
        
        if not user_data_source:
            user_data_source = UserDataSource(
                user_id=user_id,
                data_source_id=hevy_source.id,
                is_active=True
            )
            db.session.add(user_data_source)
        
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully processed {items_synced} workouts from Hevy export"
        })
        
    except Exception as e:
        # Update sync log with error
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to process Hevy export: {str(e)}"}), 500

@hevy_bp.route('/sync', methods=['POST'])
def sync_hevy_data():
    """Manually sync Hevy data for a user"""
    user_id = request.json.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get user data source connection
    hevy_source = DataSource.query.filter_by(name="Hevy").first()
    if not hevy_source:
        return jsonify({"error": "Hevy data source not configured"}), 404
    
    user_data_source = UserDataSource.query.filter_by(
        user_id=user_id, 
        data_source_id=hevy_source.id,
        is_active=True
    ).first()
    
    if not user_data_source:
        return jsonify({"error": "User not connected to Hevy"}), 404
    
    # Create sync log
    sync_log = SyncLog(
        user_id=user_id,
        data_source_id=hevy_source.id,
        sync_start_time=datetime.utcnow(),
        status="pending"
    )
    db.session.add(sync_log)
    db.session.commit()
    
    try:
        # In a real implementation, we would fetch data from Hevy API
        # For demo purposes, we'll simulate workout data
        workouts = simulate_hevy_workout_data(user_id)
        
        # Process and save workouts
        items_synced = process_hevy_workout_data(user_id, hevy_source.id, workouts)
        
        # Update sync log
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "success"
        sync_log.items_synced = items_synced
        
        # Update last sync time
        user_data_source.last_sync_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True, 
            "message": f"Successfully synced {items_synced} workouts from Hevy"
        })
        
    except Exception as e:
        # Update sync log with error
        sync_log.sync_end_time = datetime.utcnow()
        sync_log.status = "failed"
        sync_log.error_message = str(e)
        db.session.commit()
        
        return jsonify({"error": f"Failed to sync Hevy data: {str(e)}"}), 500

def simulate_hevy_workout_data(user_id):
    """Simulate workout data from Hevy for demo purposes"""
    today = datetime.utcnow().date()
    
    # Common exercises
    exercises = [
        {"id": 1, "name": "Bench Press", "muscle_group": "Chest", "exercise_type": "strength"},
        {"id": 2, "name": "Squat", "muscle_group": "Legs", "exercise_type": "strength"},
        {"id": 3, "name": "Deadlift", "muscle_group": "Back", "exercise_type": "strength"},
        {"id": 4, "name": "Pull-up", "muscle_group": "Back", "exercise_type": "strength"},
        {"id": 5, "name": "Shoulder Press", "muscle_group": "Shoulders", "exercise_type": "strength"},
        {"id": 6, "name": "Bicep Curl", "muscle_group": "Arms", "exercise_type": "strength"},
        {"id": 7, "name": "Tricep Extension", "muscle_group": "Arms", "exercise_type": "strength"},
        {"id": 8, "name": "Leg Press", "muscle_group": "Legs", "exercise_type": "strength"},
        {"id": 9, "name": "Lat Pulldown", "muscle_group": "Back", "exercise_type": "strength"},
        {"id": 10, "name": "Treadmill", "muscle_group": "Cardio", "exercise_type": "cardio"}
    ]
    
    # Simulate workouts for the past 2 weeks
    workouts = []
    
    # Workout templates
    workout_templates = [
        {
            "name": "Chest Day",
            "exercises": [1, 7, 9],  # Bench Press, Tricep Extension, Lat Pulldown
            "duration": 3600,  # 1 hour
            "calories": 350
        },
        {
            "name": "Leg Day",
            "exercises": [2, 8],  # Squat, Leg Press
            "duration": 2700,  # 45 minutes
            "calories": 400
        },
        {
            "name": "Back Day",
            "exercises": [3, 4, 9],  # Deadlift, Pull-up, Lat Pulldown
            "duration": 3300,  # 55 minutes
            "calories": 380
        },
        {
            "name": "Cardio Session",
            "exercises": [10],  # Treadmill
            "duration": 1800,  # 30 minutes
            "calories": 250
        }
    ]
    
    # Generate workouts for specific days
    workout_days = [1, 3, 5, 8, 10, 12, 14]  # Days ago
    
    for day_offset in workout_days:
        workout_date = today - timedelta(days=day_offset)
        
        # Select a workout template
        template_index = day_offset % len(workout_templates)
        template = workout_templates[template_index]
        
        workout = {
            "id": f"workout_{workout_date.strftime('%Y%m%d')}",
            "workout_name": template["name"],
            "workout_date": datetime.combine(workout_date, datetime.min.time().replace(hour=18)),
            "duration": template["duration"],
            "calories_burned": template["calories"],
            "notes": f"Felt {'great' if day_offset % 2 == 0 else 'tired'} during this workout.",
            "exercises": []
        }
        
        # Add exercises to the workout
        for exercise_id in template["exercises"]:
            exercise = next((e for e in exercises if e["id"] == exercise_id), None)
            if exercise:
                # For strength exercises
                if exercise["exercise_type"] == "strength":
                    sets = 3 + (day_offset % 2)  # 3 or 4 sets
                    reps = 8 + (day_offset % 3)  # 8-10 reps
                    weight = 50 + (exercise_id * 5) + (day_offset % 5)  # Varying weight
                    
                    workout["exercises"].append({
                        "exercise_id": exercise_id,
                        "sets": sets,
                        "reps": reps,
                        "weight": weight,
                        "duration": None,
                        "distance": None,
                        "notes": "Increased weight from last session" if day_offset % 3 == 0 else None
                    })
                # For cardio exercises
                else:
                    duration = 1800  # 30 minutes
                    distance = 5.0 + (day_offset * 0.1)  # 5+ km
                    
                    workout["exercises"].append({
                        "exercise_id": exercise_id,
                        "sets": 1,
                        "reps": None,
                        "weight": None,
                        "duration": duration,
                        "distance": distance,
                        "notes": "Felt good pace" if day_offset % 2 == 0 else "Pushed harder than usual"
                    })
        
        workouts.append(workout)
    
    return workouts, exercises

def process_hevy_workout_data(user_id, source_id, workout_data):
    """Process and save Hevy workout data to database"""
    workouts, exercise_data = workout_data
    count = 0
    
    # First, ensure all exercises exist in the database
    for exercise_info in exercise_data:
        existing_exercise = Exercise.query.filter_by(name=exercise_info["name"]).first()
        
        if not existing_exercise:
            new_exercise = Exercise(
                name=exercise_info["name"],
                muscle_group=exercise_info["muscle_group"],
                exercise_type=exercise_info["exercise_type"]
            )
            db.session.add(new_exercise)
    
    db.session.commit()
    
    # Now process workouts
    for workout_info in workouts:
        # Check if workout already exists
        existing_workout = Workout.query.filter_by(
            user_id=user_id,
            source_id=source_id,
            external_id=workout_info["id"]
        ).first()
        
        if existing_workout:
            # Update existing workout
            existing_workout.workout_name = workout_info["workout_name"]
            existing_workout.workout_date = workout_info["workout_date"]
            existing_workout.duration = workout_info["duration"]
            existing_workout.calories_burned = workout_info["calories_burned"]
            existing_workout.notes = workout_info["notes"]
            existing_workout.updated_at = datetime.utcnow()
            
            # Remove existing workout exercises
            for exercise in existing_workout.exercises:
                db.session.delete(exercise)
            
            # Add new workout exercises
            for exercise_info in workout_info["exercises"]:
                exercise = Exercise.query.filter_by(name=next(e["name"] for e in exercise_data if e["id"] == exercise_info["exercise_id"])).first()
                
                if exercise:
                    workout_exercise = WorkoutExercise(
                        workout_id=existing_workout.id,
                        exercise_id=exercise.id,
                        sets=exercise_info["sets"],
                        reps=exercise_info["reps"],
                        weight=exercise_info["weight"],
                        duration=exercise_info["duration"],
                        distance=exercise_info["distance"],
                        notes=exercise_info["notes"]
                    )
                    db.session.add(workout_exercise)
        else:
            # Create new workout
            new_workout = Workout(
                user_id=user_id,
                source_id=source_id,
                external_id=workout_info["id"],
                workout_name=workout_info["workout_name"],
                workout_date=workout_info["workout_date"],
                duration=workout_info["duration"],
                calories_burned=workout_info["calories_burned"],
                notes=workout_info["notes"]
            )
            db.session.add(new_workout)
            db.session.flush()  # Get the ID for the new workout
            
            # Add workout exercises
            for exercise_info in workout_info["exercises"]:
                exercise = Exercise.query.filter_by(name=next(e["name"] for e in exercise_data if e["id"] == exercise_info["exercise_id"])).first()
                
                if exercise:
                    workout_exercise = WorkoutExercise(
                        workout_id=new_workout.id,
                        exercise_id=exercise.id,
                        sets=exercise_info["sets"],
                        reps=exercise_info["reps"],
                        weight=exercise_info["weight"],
                        duration=exercise_info["duration"],
                        distance=exercise_info["distance"],
                        notes=exercise_info["notes"]
                    )
                    db.session.add(workout_exercise)
            
            count += 1
    
    db.session.commit()
    return count
