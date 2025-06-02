from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class BloodReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    report_name = db.Column(db.String(255), nullable=True)
    report_provider = db.Column(db.String(255), nullable=True)
    pdf_file_path = db.Column(db.String(255), nullable=True)
    is_processed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('blood_reports', lazy=True))
    metrics = db.relationship('BloodMetric', backref='blood_report', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<BloodReport {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'report_date': self.report_date,
            'report_name': self.report_name,
            'report_provider': self.report_provider,
            'pdf_file_path': self.pdf_file_path,
            'is_processed': self.is_processed,
            'metrics': [metric.to_dict() for metric in self.metrics],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class BloodMetric(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blood_report_id = db.Column(db.Integer, db.ForeignKey('blood_report.id', ondelete='CASCADE'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)
    reference_range = db.Column(db.String(100), nullable=True)
    is_normal = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<BloodMetric {self.metric_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'blood_report_id': self.blood_report_id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'unit': self.unit,
            'reference_range': self.reference_range,
            'is_normal': self.is_normal,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
