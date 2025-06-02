from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class FoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    external_id = db.Column(db.String(100), nullable=True)  # ID from external source
    meal_type = db.Column(db.String(50), nullable=False)  # 'breakfast', 'lunch', 'dinner', 'snack'
    consumed_at = db.Column(db.DateTime, nullable=False)
    total_calories = db.Column(db.Float, nullable=True)
    total_carbs = db.Column(db.Float, nullable=True)
    total_protein = db.Column(db.Float, nullable=True)
    total_fat = db.Column(db.Float, nullable=True)
    total_fiber = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('food_entries', lazy=True))
    source = db.relationship('DataSource', backref=db.backref('food_entries', lazy=True))
    food_items = db.relationship('FoodItem', backref='food_entry', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<FoodEntry {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_id': self.source_id,
            'external_id': self.external_id,
            'meal_type': self.meal_type,
            'consumed_at': self.consumed_at,
            'total_calories': self.total_calories,
            'total_carbs': self.total_carbs,
            'total_protein': self.total_protein,
            'total_fat': self.total_fat,
            'total_fiber': self.total_fiber,
            'food_items': [item.to_dict() for item in self.food_items],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_entry_id = db.Column(db.Integer, db.ForeignKey('food_entry.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Float, nullable=True)
    unit = db.Column(db.String(50), nullable=True)  # 'g', 'ml', 'serving'
    calories = db.Column(db.Float, nullable=True)
    carbs = db.Column(db.Float, nullable=True)
    protein = db.Column(db.Float, nullable=True)
    fat = db.Column(db.Float, nullable=True)
    fiber = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<FoodItem {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'food_entry_id': self.food_entry_id,
            'name': self.name,
            'quantity': self.quantity,
            'unit': self.unit,
            'calories': self.calories,
            'carbs': self.carbs,
            'protein': self.protein,
            'fat': self.fat,
            'fiber': self.fiber,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
