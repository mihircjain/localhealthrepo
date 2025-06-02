from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class DataSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    source_type = db.Column(db.String(50), nullable=False)  # 'activity', 'food', 'sleep', 'blood_report', 'medication', 'workout'
    api_endpoint = db.Column(db.String(255), nullable=True)
    requires_oauth = db.Column(db.Boolean, default=False)
    oauth_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<DataSource {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'source_type': self.source_type,
            'api_endpoint': self.api_endpoint,
            'requires_oauth': self.requires_oauth,
            'oauth_url': self.oauth_url,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class UserDataSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_source.id', ondelete='CASCADE'), nullable=False)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    last_sync_at = db.Column(db.DateTime, nullable=True)
    sync_frequency = db.Column(db.String(20), default='daily')  # 'hourly', 'daily', 'weekly'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('data_sources', lazy=True))
    data_source = db.relationship('DataSource', backref=db.backref('users', lazy=True))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'data_source_id', name='uix_user_data_source'),
    )

    def __repr__(self):
        return f'<UserDataSource {self.user_id}:{self.data_source_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_source_id': self.data_source_id,
            'data_source_name': self.data_source.name if self.data_source else None,
            'is_active': self.is_active,
            'last_sync_at': self.last_sync_at,
            'sync_frequency': self.sync_frequency,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class SyncLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_source.id', ondelete='CASCADE'), nullable=False)
    sync_start_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    sync_end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False)  # 'pending', 'success', 'failed'
    items_synced = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('sync_logs', lazy=True))
    data_source = db.relationship('DataSource', backref=db.backref('sync_logs', lazy=True))

    def __repr__(self):
        return f'<SyncLog {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data_source_id': self.data_source_id,
            'data_source_name': self.data_source.name if self.data_source else None,
            'sync_start_time': self.sync_start_time,
            'sync_end_time': self.sync_end_time,
            'status': self.status,
            'items_synced': self.items_synced,
            'error_message': self.error_message,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
