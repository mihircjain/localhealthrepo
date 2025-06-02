from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    external_id = db.Column(db.String(100), nullable=True)  # ID from external source (e.g., Strava activity ID)
    activity_type = db.Column(db.String(50), nullable=False)  # 'run', 'ride', 'swim', etc.
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    distance = db.Column(db.Float, nullable=True)  # in meters
    calories = db.Column(db.Float, nullable=True)
    average_heart_rate = db.Column(db.Float, nullable=True)
    max_heart_rate = db.Column(db.Float, nullable=True)
    elevation_gain = db.Column(db.Float, nullable=True)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    route_data = db.Column(db.JSON, nullable=True)  # GPS data if available
    weather_data = db.Column(db.JSON, nullable=True)  # Weather conditions during activity
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('activities', lazy=True))
    source = db.relationship('DataSource', backref=db.backref('activities', lazy=True))

    def __repr__(self):
        return f'<Activity {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_id': self.source_id,
            'external_id': self.external_id,
            'activity_type': self.activity_type,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'distance': self.distance,
            'calories': self.calories,
            'average_heart_rate': self.average_heart_rate,
            'max_heart_rate': self.max_heart_rate,
            'elevation_gain': self.elevation_gain,
            'title': self.title,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
