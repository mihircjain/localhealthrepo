from flask_sqlalchemy import SQLAlchemy
from src.models.user import db
from datetime import datetime

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    source_id = db.Column(db.Integer, db.ForeignKey('data_source.id'), nullable=False)
    external_id = db.Column(db.String(100), nullable=True)  # ID from external source
    workout_name = db.Column(db.String(255), nullable=False)
    workout_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    calories_burned = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('workouts', lazy=True))
    source = db.relationship('DataSource', backref=db.backref('workouts', lazy=True))
    exercises = db.relationship('WorkoutExercise', backref='workout', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Workout {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'source_id': self.source_id,
            'external_id': self.external_id,
            'workout_name': self.workout_name,
            'workout_date': self.workout_date,
            'duration': self.duration,
            'calories_burned': self.calories_burned,
            'notes': self.notes,
            'exercises': [exercise.to_dict() for exercise in self.exercises],
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class Exercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    muscle_group = db.Column(db.String(100), nullable=True)
    exercise_type = db.Column(db.String(50), nullable=True)  # 'strength', 'cardio', 'flexibility'
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Exercise {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'muscle_group': self.muscle_group,
            'exercise_type': self.exercise_type,
            'description': self.description,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }


class WorkoutExercise(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    workout_id = db.Column(db.Integer, db.ForeignKey('workout.id', ondelete='CASCADE'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercise.id'), nullable=False)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds, for timed exercises
    distance = db.Column(db.Float, nullable=True)  # for distance-based exercises
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    exercise = db.relationship('Exercise', backref=db.backref('workout_exercises', lazy=True))

    def __repr__(self):
        return f'<WorkoutExercise {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'workout_id': self.workout_id,
            'exercise_id': self.exercise_id,
            'exercise_name': self.exercise.name if self.exercise else None,
            'sets': self.sets,
            'reps': self.reps,
            'weight': self.weight,
            'duration': self.duration,
            'distance': self.distance,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
