from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    generic_name = db.Column(db.String(255), nullable=True)
    medication_type = db.Column(db.String(100), nullable=True)  # 'pill', 'liquid', 'injection', etc.
    standard_dosage = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    side_effects = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Medication {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'generic_name': self.generic_name,
            'medication_type': self.medication_type,
            'standard_dosage': self.standard_dosage,
            'description': self.description,
            'side_effects': self.side_effects,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class UserMedication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'), nullable=False)
    custom_name = db.Column(db.String(255), nullable=True)
    dosage = db.Column(db.String(100), nullable=True)
    frequency = db.Column(db.String(100), nullable=True)  # 'once daily', 'twice daily', etc.
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('medications', lazy=True))
    medication = db.relationship('Medication', backref=db.backref('user_medications', lazy=True))
    logs = db.relationship('MedicationLog', backref='user_medication', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<UserMedication {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'medication_id': self.medication_id,
            'medication_name': self.medication.name if self.medication else None,
            'custom_name': self.custom_name,
            'dosage': self.dosage,
            'frequency': self.frequency,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class MedicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_medication_id = db.Column(db.Integer, db.ForeignKey('user_medication.id', ondelete='CASCADE'), nullable=False)
    taken_at = db.Column(db.DateTime, nullable=False)
    dosage_taken = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<MedicationLog {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_medication_id': self.user_medication_id,
            'taken_at': self.taken_at,
            'dosage_taken': self.dosage_taken,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
