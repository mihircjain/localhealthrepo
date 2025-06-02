import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from src.models.user import db, User
from src.routes.strava import strava_bp
from src.routes.healthifyme import healthifyme_bp
from src.routes.apple_health import apple_health_bp
from src.routes.blood_report import blood_report_bp
from src.routes.medication import medication_bp
from src.routes.hevy import hevy_bp
from src.routes.chat import chat_bp
import os

app = Flask(__name__)
CORS(app)

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///health_dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(strava_bp, url_prefix='/api/strava')
app.register_blueprint(healthifyme_bp, url_prefix='/api/healthifyme')
app.register_blueprint(apple_health_bp, url_prefix='/api/apple-health')
app.register_blueprint(blood_report_bp, url_prefix='/api/blood-reports')
app.register_blueprint(medication_bp, url_prefix='/api/medications')
app.register_blueprint(hevy_bp, url_prefix='/api/hevy')
app.register_blueprint(chat_bp, url_prefix='/api/chat')

# Serve static files
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

# User management endpoints
@app.route('/api/users', methods=['POST'])
def create_user():
    """Create a new user"""
    name = request.json.get('name')
    email = request.json.get('email')
    
    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"error": "User with this email already exists"}), 400
    
    # Create new user
    user = User(name=name, email=email)
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "User created successfully",
        "user": user.to_dict()
    })

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users"""
    users = User.query.all()
    return jsonify({
        "success": True,
        "users": [user.to_dict() for user in users]
    })

@app.route('/api/users/<int:id>', methods=['GET'])
def get_user(id):
    """Get a specific user"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "success": True,
        "user": user.to_dict()
    })

@app.route('/api/users/<int:id>', methods=['PUT'])
def update_user(id):
    """Update a user"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    if 'name' in request.json:
        user.name = request.json.get('name')
    
    if 'email' in request.json:
        user.email = request.json.get('email')
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "User updated successfully",
        "user": user.to_dict()
    })

@app.route('/api/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    """Delete a user"""
    user = User.query.get(id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": "User deleted successfully"
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Health Dashboard API is running"
    })

# Create database tables
with app.app_context():
    db.create_all()
    
    # Check if we need to initialize the medication repository
    from src.models.medication import Medication
    if Medication.query.count() == 0:
        from src.routes.medication import initialize_medication_repository
        initialize_medication_repository()

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=5001, debug=True)

