from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import TravelItinerary, Checkpoint
from ai_service import generate_travel_itinerary
from weather_service import WeatherService
from chatbot_service import TravelChatbot
from agent_coordinator import TravelAgentCoordinator, AgentContext

# Initialize services
weather_service = WeatherService()
chatbot = TravelChatbot()
agent_coordinator = TravelAgentCoordinator()
import json
from datetime import datetime, timedelta

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_itinerary', methods=['POST'])
def generate_itinerary():
    try:
        
        destination = request.form.get('destination', '').strip()
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        budget = float(request.form.get('budget', 0))
        interests = request.form.getlist('interests')
        
  
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            duration = (end_date - start_date).days
        else:
            duration = 0
        
      
        if not destination or duration <= 0 or budget <= 0:
            flash('Please fill in all required fields with valid values.', 'error')
            return redirect(url_for('index'))
        
        
        app.logger.info(f"Generating itinerary for {destination}, {duration} days, budget ₹{budget}")
        itinerary_data = generate_travel_itinerary(destination, duration, budget, interests)
        
        if not itinerary_data:
            flash('Failed to generate itinerary. Please try again.', 'error')
            return redirect(url_for('index'))
        
      
        itinerary = TravelItinerary(
            destination=destination,
            duration=duration,
            budget=budget
        )
        itinerary.set_interests_list(interests)
        itinerary.set_itinerary_data(itinerary_data)
        
        db.session.add(itinerary)
        db.session.flush()  # Get the ID
        
