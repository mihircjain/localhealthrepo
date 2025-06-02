from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class SleepRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    external_id = db.Column(db.String(100), nullable=True)  # ID from external source
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    deep_sleep_duration = db.Column(db.Integer, nullable=True)  # in seconds
    light_sleep_duration = db.Column(db.Integer, nullable=True)  # in seconds
    rem_sleep_duration = db.Column(db.Integer, nullable=True)  # in seconds
    awake_duration = db.Column(db.Integer, nullable=True)  # in seconds
    sleep_score = db.Column(db.Integer, nullable=True)  # 0-100 if available
    heart_rate_avg = db.Column(db.Float, nullable=True)
    heart_rate_min = db.Column(db.Float, nullable=True)
    heart_rate_max = db.Column(db.Float, nullable=True)
    respiratory_rate_avg = db.Column(db.Float, nullable=True)
    sleep_data = db.Column(db.JSON, nullable=True)  # Additional sleep metrics
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('sleep_records', lazy=True))
    source = db.relationship('DataSource', backref=db.backref('sleep_records', lazy=True))

    def __repr__(self):
        return f'<SleepRecord {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_id': self.source_id,
            'external_id': self.external_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'deep_sleep_duration': self.deep_sleep_duration,
            'light_sleep_duration': self.light_sleep_duration,
            'rem_sleep_duration': self.rem_sleep_duration,
            'awake_duration': self.awake_duration,
            'sleep_score': self.sleep_score,
            'heart_rate_avg': self.heart_rate_avg,
            'heart_rate_min': self.heart_rate_min,
            'heart_rate_max': self.heart_rate_max,
            'respiratory_rate_avg': self.respiratory_rate_avg,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
