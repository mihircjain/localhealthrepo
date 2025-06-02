from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class UserQuery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    query_text = db.Column(db.Text, nullable=False)
    query_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    response_text = db.Column(db.Text, nullable=True)
    data_sources_used = db.Column(db.JSON, nullable=True)  # List of data sources used to answer the query
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('queries', lazy=True))

    def __repr__(self):
        return f'<UserQuery {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'query_text': self.query_text,
            'query_time': self.query_time,
            'response_text': self.response_text,
            'data_sources_used': self.data_sources_used,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Insight(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    insight_type = db.Column(db.String(100), nullable=False)  # 'trend', 'correlation', 'recommendation'
    insight_text = db.Column(db.Text, nullable=False)
    data_sources = db.Column(db.JSON, nullable=True)  # Data sources this insight is based on
    relevance_score = db.Column(db.Float, nullable=True)  # How relevant/important this insight is (0-1)
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('insights', lazy=True))

    def __repr__(self):
        return f'<Insight {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'insight_type': self.insight_type,
            'insight_text': self.insight_text,
            'data_sources': self.data_sources,
            'relevance_score': self.relevance_score,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'is_read': self.is_read,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
