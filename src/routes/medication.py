import os
from flask import Blueprint, request, jsonify, current_app
from src.models.user import db, User
from src.models.data_source import DataSource, UserDataSource, SyncLog
from src.models.medication import Medication, UserMedication, MedicationLog
from datetime import datetime, timedelta
import json

medication_bp = Blueprint('medication', __name__)

@medication_bp.route('/medications', methods=['GET'])
def get_medications():
    """Get all medications in the repository"""
    search = request.args.get('search', '')
    
    query = Medication.query
    
    if search:
        query = query.filter(Medication.name.ilike(f'%{search}%') | 
                            Medication.generic_name.ilike(f'%{search}%'))
    
    medications = query.order_by(Medication.name).all()
    
    return jsonify({
        "success": True,
        "medications": [medication.to_dict() for medication in medications]
    })

@medication_bp.route('/medications', methods=['POST'])
def add_medication():
    """Add a new medication to the repository"""
    name = request.json.get('name')
    generic_name = request.json.get('generic_name')
    medication_type = request.json.get('medication_type')
    standard_dosage = request.json.get('standard_dosage')
    description = request.json.get('description')
    side_effects = request.json.get('side_effects')
    
    if not name:
        return jsonify({"error": "Medication name is required"}), 400
    
    # Check if medication already exists
    existing = Medication.query.filter(Medication.name.ilike(name)).first()
    if existing:
        return jsonify({"error": "Medication with this name already exists"}), 400
    
    # Create new medication
    medication = Medication(
        name=name,
        generic_name=generic_name,
        medication_type=medication_type,
        standard_dosage=standard_dosage,
        description=description,
        side_effects=side_effects
    )
    
    db.session.add(medication)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Medication added successfully",
        "medication": medication.to_dict()
    })

@medication_bp.route('/user-medications', methods=['GET'])
def get_user_medications():
    """Get all medications for a user"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    user_medications = UserMedication.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        "success": True,
        "medications": [medication.to_dict() for medication in user_medications]
    })

@medication_bp.route('/user-medications', methods=['POST'])
def add_user_medication():
    """Add a medication for a user"""
    user_id = request.json.get('user_id')
    medication_id = request.json.get('medication_id')
    custom_name = request.json.get('custom_name')
    dosage = request.json.get('dosage')
    frequency = request.json.get('frequency')
    start_date = request.json.get('start_date')
    end_date = request.json.get('end_date')
    notes = request.json.get('notes')
    
    if not user_id or not medication_id:
        return jsonify({"error": "User ID and medication ID are required"}), 400
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if medication exists
    medication = Medication.query.get(medication_id)
    if not medication:
        return jsonify({"error": "Medication not found"}), 404
    
    # Parse dates
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD"}), 400
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid end date format. Use YYYY-MM-DD"}), 400
    
    # Create user medication
    user_medication = UserMedication(
        user_id=user_id,
        medication_id=medication_id,
        custom_name=custom_name,
        dosage=dosage,
        frequency=frequency,
        start_date=start_date,
        end_date=end_date,
        notes=notes
    )
    
    db.session.add(user_medication)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Medication added for user",
        "user_medication": user_medication.to_dict()
    })

@medication_bp.route('/user-medications/<int:id>', methods=['PUT'])
def update_user_medication(id):
    """Update a user's medication"""
    user_medication = UserMedication.query.get(id)
    if not user_medication:
        return jsonify({"error": "User medication not found"}), 404
    
    # Update fields
    if 'custom_name' in request.json:
        user_medication.custom_name = request.json.get('custom_name')
    
    if 'dosage' in request.json:
        user_medication.dosage = request.json.get('dosage')
    
    if 'frequency' in request.json:
        user_medication.frequency = request.json.get('frequency')
    
    if 'start_date' in request.json:
        start_date = request.json.get('start_date')
        if start_date:
            try:
                user_medication.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD"}), 400
    
    if 'end_date' in request.json:
        end_date = request.json.get('end_date')
        if end_date:
            try:
                user_medication.end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"error": "Invalid end date format. Use YYYY-MM-DD"}), 400
    
    if 'notes' in request.json:
        user_medication.notes = request.json.get('notes')
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "User medication updated",
        "user_medication": user_medication.to_dict()
    })

@medication_bp.route('/user-medications/<int:id>', methods=['DELETE'])
def delete_user_medication(id):
    """Delete a user's medication"""
    user_medication = UserMedication.query.get(id)
    if not user_medication:
        return jsonify({"error": "User medication not found"}), 404
    
    db.session.delete(user_medication)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "User medication deleted"
    })

@medication_bp.route('/logs', methods=['GET'])
def get_medication_logs():
    """Get medication logs for a user"""
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    
    # Get date range
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Parse dates
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid start date format. Use YYYY-MM-DD"}), 400
    else:
        start_date = (datetime.utcnow() - timedelta(days=30)).date()
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"error": "Invalid end date format. Use YYYY-MM-DD"}), 400
    else:
        end_date = datetime.utcnow().date()
    
    # Get user medications
    user_medications = UserMedication.query.filter_by(user_id=user_id).all()
    user_medication_ids = [um.id for um in user_medications]
    
    # Get logs for these medications
    logs = MedicationLog.query.filter(
        MedicationLog.user_medication_id.in_(user_medication_ids),
        MedicationLog.taken_at >= datetime.combine(start_date, datetime.min.time()),
        MedicationLog.taken_at <= datetime.combine(end_date, datetime.max.time())
    ).order_by(MedicationLog.taken_at.desc()).all()
    
    # Prepare response with medication details
    result = []
    for log in logs:
        user_medication = next((um for um in user_medications if um.id == log.user_medication_id), None)
        if user_medication:
            medication = Medication.query.get(user_medication.medication_id)
            log_dict = log.to_dict()
            log_dict['medication_name'] = medication.name if medication else 'Unknown'
            log_dict['custom_name'] = user_medication.custom_name
            log_dict['standard_dosage'] = user_medication.dosage
            result.append(log_dict)
    
    return jsonify({
        "success": True,
        "logs": result
    })

@medication_bp.route('/logs', methods=['POST'])
def add_medication_log():
    """Log a medication intake"""
    user_medication_id = request.json.get('user_medication_id')
    taken_at = request.json.get('taken_at')
    dosage_taken = request.json.get('dosage_taken')
    notes = request.json.get('notes')
    
    if not user_medication_id:
        return jsonify({"error": "User medication ID is required"}), 400
    
    # Check if user medication exists
    user_medication = UserMedication.query.get(user_medication_id)
    if not user_medication:
        return jsonify({"error": "User medication not found"}), 404
    
    # Parse taken_at
    if taken_at:
        try:
            taken_at = datetime.strptime(taken_at, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                taken_at = datetime.strptime(taken_at, '%Y-%m-%d')
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DD HH:MM:SS or YYYY-MM-DD"}), 400
    else:
        taken_at = datetime.utcnow()
    
    # Create medication log
    medication_log = MedicationLog(
        user_medication_id=user_medication_id,
        taken_at=taken_at,
        dosage_taken=dosage_taken or user_medication.dosage,
        notes=notes
    )
    
    db.session.add(medication_log)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Medication log added",
        "log": medication_log.to_dict()
    })

@medication_bp.route('/logs/<int:id>', methods=['DELETE'])
def delete_medication_log(id):
    """Delete a medication log"""
    medication_log = MedicationLog.query.get(id)
    if not medication_log:
        return jsonify({"error": "Medication log not found"}), 404
    
    db.session.delete(medication_log)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Medication log deleted"
    })

@medication_bp.route('/initialize', methods=['POST'])
def initialize_medication_repository():
    """Initialize the medication repository with common medications"""
    # Check if repository is already populated
    if Medication.query.count() > 0:
        return jsonify({
            "success": True,
            "message": "Medication repository already initialized",
            "count": Medication.query.count()
        })
    
    # Common medications
    medications = [
        {
            "name": "Aspirin",
            "generic_name": "Acetylsalicylic acid",
            "medication_type": "pill",
            "standard_dosage": "81-325 mg",
            "description": "Used to treat pain, fever, and inflammation.",
            "side_effects": "Stomach upset, heartburn, easy bruising or bleeding."
        },
        {
            "name": "Ibuprofen",
            "generic_name": "Ibuprofen",
            "medication_type": "pill",
            "standard_dosage": "200-800 mg",
            "description": "Used to reduce fever and treat pain or inflammation.",
            "side_effects": "Stomach upset, heartburn, dizziness, mild headache."
        },
        {
            "name": "Acetaminophen",
            "generic_name": "Paracetamol",
            "medication_type": "pill",
            "standard_dosage": "325-1000 mg",
            "description": "Used to treat mild to moderate pain and reduce fever.",
            "side_effects": "Nausea, stomach pain, loss of appetite."
        },
        {
            "name": "Lisinopril",
            "generic_name": "Lisinopril",
            "medication_type": "pill",
            "standard_dosage": "5-40 mg",
            "description": "Used to treat high blood pressure and heart failure.",
            "side_effects": "Dizziness, headache, dry cough."
        },
        {
            "name": "Atorvastatin",
            "generic_name": "Atorvastatin",
            "medication_type": "pill",
            "standard_dosage": "10-80 mg",
            "description": "Used to lower cholesterol and reduce risk of heart disease.",
            "side_effects": "Muscle pain, diarrhea, gas, heartburn."
        },
        {
            "name": "Metformin",
            "generic_name": "Metformin",
            "medication_type": "pill",
            "standard_dosage": "500-2000 mg",
            "description": "Used to treat type 2 diabetes.",
            "side_effects": "Nausea, vomiting, stomach upset, diarrhea."
        },
        {
            "name": "Levothyroxine",
            "generic_name": "Levothyroxine",
            "medication_type": "pill",
            "standard_dosage": "25-200 mcg",
            "description": "Used to treat hypothyroidism.",
            "side_effects": "Weight loss, tremors, headache, changes in appetite."
        },
        {
            "name": "Amlodipine",
            "generic_name": "Amlodipine",
            "medication_type": "pill",
            "standard_dosage": "2.5-10 mg",
            "description": "Used to treat high blood pressure and chest pain.",
            "side_effects": "Swelling in ankles or feet, dizziness, flushing."
        },
        {
            "name": "Omeprazole",
            "generic_name": "Omeprazole",
            "medication_type": "pill",
            "standard_dosage": "20-40 mg",
            "description": "Used to treat heartburn, acid reflux, and ulcers.",
            "side_effects": "Headache, stomach pain, diarrhea, nausea."
        },
        {
            "name": "Albuterol",
            "generic_name": "Salbutamol",
            "medication_type": "inhaler",
            "standard_dosage": "2 puffs every 4-6 hours",
            "description": "Used to treat asthma and COPD.",
            "side_effects": "Nervousness, shaking, headache, throat irritation."
        }
    ]
    
    # Add medications to database
    for med_data in medications:
        medication = Medication(**med_data)
        db.session.add(medication)
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "Medication repository initialized",
        "count": len(medications)
    })
