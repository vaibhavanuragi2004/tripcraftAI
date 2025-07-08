from app import db
from datetime import datetime
import json

class TravelItinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    destination = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # days
    budget = db.Column(db.Float, nullable=False)
    interests = db.Column(db.Text)  
    itinerary_data = db.Column(db.Text)  # JSON string of generated itinerary
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    checkpoints = db.relationship('Checkpoint', backref='itinerary', lazy=True, cascade='all, delete-orphan')
    
    def get_interests_list(self):
        if self.interests:
            return json.loads(self.interests)
        return []
    
    def set_interests_list(self, interests_list):
        self.interests = json.dumps(interests_list)
    
    def get_itinerary_data(self):
        if self.itinerary_data:
            return json.loads(self.itinerary_data)
        return {}
    
    def set_itinerary_data(self, data):
        self.itinerary_data = json.dumps(data)



class Checkpoint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('travel_itinerary.id'), nullable=False)
    day = db.Column(db.Integer, nullable=False)
    time = db.Column(db.String(10), nullable=False)  # HH:MM format
    location = db.Column(db.String(200), nullable=False)
    activity = db.Column(db.Text, nullable=False)
    estimated_cost = db.Column(db.Float, default=0.0)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    
    def mark_completed(self):
        self.is_completed = True
        self.completed_at = datetime.utcnow()
