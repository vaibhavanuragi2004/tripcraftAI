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
        # Get form data
        destination = request.form.get('destination', '').strip()
        start_date_str = request.form.get('start_date', '')
        end_date_str = request.form.get('end_date', '')
        budget = float(request.form.get('budget', 0))
        interests = request.form.getlist('interests')
        
        # Calculate duration from dates
        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            duration = (end_date - start_date).days
        else:
            duration = 0
        
        # Validate input
        if not destination or duration <= 0 or budget <= 0:
            flash('Please fill in all required fields with valid values.', 'error')
            return redirect(url_for('index'))
        
        # Generate itinerary using AI
        app.logger.info(f"Generating itinerary for {destination}, {duration} days, budget ₹{budget}")
        itinerary_data = generate_travel_itinerary(destination, duration, budget, interests)
        
        if not itinerary_data:
            flash('Failed to generate itinerary. Please try again.', 'error')
            return redirect(url_for('index'))
        
        # Save to database
        itinerary = TravelItinerary(
            destination=destination,
            duration=duration,
            budget=budget
        )
        itinerary.set_interests_list(interests)
        itinerary.set_itinerary_data(itinerary_data)
        
        db.session.add(itinerary)
        db.session.flush()  # Get the ID
        
        # Create checkpoints
        for day_data in itinerary_data.get('days', []):
            day_num = day_data.get('day', 1)
            for activity in day_data.get('activities', []):
                # Prepare notes with opening hours and tips
                notes_parts = []
                if activity.get('opening_hours'):
                    notes_parts.append(f"opening_hours:{activity.get('opening_hours')}")
                if activity.get('tips'):
                    notes_parts.append(f"tips:{activity.get('tips')}")
                if activity.get('travel_time_to_next'):
                    notes_parts.append(f"travel_time:{activity.get('travel_time_to_next')}")
                if activity.get('transportation_mode'):
                    notes_parts.append(f"transport:{activity.get('transportation_mode')}")
                
                checkpoint = Checkpoint(
                    itinerary_id=itinerary.id,
                    day=day_num,
                    time=activity.get('time', '09:00'),
                    location=activity.get('location', ''),
                    activity=activity.get('description', ''),
                    estimated_cost=activity.get('cost', 0.0),
                    notes=', '.join(notes_parts) if notes_parts else None
                )
                db.session.add(checkpoint)
        
        db.session.commit()
        
        flash('Itinerary generated successfully!', 'success')
        return redirect(url_for('view_itinerary', itinerary_id=itinerary.id))
        
    except ValueError as e:
        flash('Please enter valid numbers for duration and budget.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        app.logger.error(f"Error generating itinerary: {str(e)}")
        flash('An error occurred while generating your itinerary. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/itinerary/<int:itinerary_id>')
def view_itinerary(itinerary_id):
    itinerary = TravelItinerary.query.get_or_404(itinerary_id)
    checkpoints = Checkpoint.query.filter_by(itinerary_id=itinerary_id).order_by(Checkpoint.day, Checkpoint.time).all()
    
    # Group checkpoints by day
    days_data = {}
    for checkpoint in checkpoints:
        if checkpoint.day not in days_data:
            days_data[checkpoint.day] = []
        days_data[checkpoint.day].append(checkpoint)
    
    # Calculate progress
    total_checkpoints = len(checkpoints)
    completed_checkpoints = len([c for c in checkpoints if c.is_completed])
    progress_percentage = (completed_checkpoints / total_checkpoints * 100) if total_checkpoints > 0 else 0
    
    return render_template('itinerary.html', 
                         itinerary=itinerary, 
                         days_data=days_data,
                         progress_percentage=progress_percentage,
                         total_checkpoints=total_checkpoints,
                         completed_checkpoints=completed_checkpoints)



@app.route('/tracking/<int:itinerary_id>')
def tracking(itinerary_id):
    itinerary = TravelItinerary.query.get_or_404(itinerary_id)
    checkpoints = Checkpoint.query.filter_by(itinerary_id=itinerary_id).order_by(Checkpoint.day, Checkpoint.time).all()
    
    return render_template('tracking.html', 
                         itinerary=itinerary, 
                         checkpoints=checkpoints)

@app.route('/complete_checkpoint/<int:checkpoint_id>', methods=['POST'])
def complete_checkpoint(checkpoint_id):
    checkpoint = Checkpoint.query.get_or_404(checkpoint_id)
    
    if not checkpoint.is_completed:
        checkpoint.mark_completed()
        checkpoint.notes = request.form.get('notes', '')
        db.session.commit()
        flash('Checkpoint completed!', 'success')
    
    return redirect(url_for('view_itinerary', itinerary_id=checkpoint.itinerary_id))

@app.route('/my_itineraries')
def my_itineraries():
    itineraries = TravelItinerary.query.order_by(TravelItinerary.created_at.desc()).all()
    return render_template('my_itineraries.html', itineraries=itineraries)

@app.route('/reorder_checkpoints', methods=['POST'])
def reorder_checkpoints():
    try:
        data = request.get_json()
        checkpoint_ids = data.get('checkpoint_ids', [])
        
        if not checkpoint_ids:
            return jsonify({'success': False, 'error': 'No checkpoint IDs provided'})
        

        for index, checkpoint_id in enumerate(checkpoint_ids):
            checkpoint = Checkpoint.query.get(checkpoint_id)
            if checkpoint:

                start_hour = 9 + (index * 2)
                new_time = f"{start_hour:02d}:00"
                checkpoint.time = new_time
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Checkpoints reordered successfully'})
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error reordering checkpoints: {e}")
        return jsonify({'success': False, 'error': 'Failed to reorder checkpoints'})

@app.route('/api/weather-alerts', methods=['GET'])
def get_weather_alerts():
    """API endpoint to get weather alerts for upcoming trips"""
    try:
        alerts = []
        tomorrow = datetime.now().date() + timedelta(days=1)
        

        
        return jsonify(alerts)
        
    except Exception as e:
        app.logger.error(f"Error getting weather alerts: {e}")
        return jsonify([])

@app.route('/api/weather/<destination>', methods=['GET'])
def get_destination_weather(destination):
    """Get current weather for a destination"""
    try:
        weather_data = weather_service.get_current_weather(destination)
        if weather_data:
            return jsonify(weather_data)
        else:
            return jsonify({'error': 'Weather data not available'}), 404
    except Exception as e:
        app.logger.error(f"Error getting weather for {destination}: {e}")
        return jsonify({'error': 'Weather service unavailable'}), 500

@app.route('/api/itinerary/<int:itinerary_id>/checkpoints', methods=['GET'])
def get_itinerary_checkpoints(itinerary_id):
    """Get checkpoints for React tracker component"""
    try:
        itinerary = TravelItinerary.query.get_or_404(itinerary_id)
        checkpoints = Checkpoint.query.filter_by(itinerary_id=itinerary_id).order_by(Checkpoint.day, Checkpoint.time).all()
        
        # Find next incomplete checkpoint
        next_checkpoint = None
        for checkpoint in checkpoints:
            if not checkpoint.is_completed:
                next_checkpoint = {
                    'id': checkpoint.id,
                    'location': checkpoint.location,
                    'time': checkpoint.time,
                    'day': checkpoint.day
                }
                break
        
        checkpoints_data = []
        for checkpoint in checkpoints:
            checkpoints_data.append({
                'id': checkpoint.id,
                'location': checkpoint.location,
                'activity': checkpoint.activity,
                'time': checkpoint.time,
                'day': checkpoint.day,
                'estimated_cost': checkpoint.estimated_cost,
                'is_completed': checkpoint.is_completed,
                'completed_at': checkpoint.completed_at.isoformat() if checkpoint.completed_at else None,
                'notes': checkpoint.notes
            })
        
        return jsonify({
            'checkpoints': checkpoints_data,
            'next_checkpoint': next_checkpoint
        })
        
    except Exception as e:
        app.logger.error(f"Error getting checkpoints for itinerary {itinerary_id}: {e}")
        return jsonify({'error': 'Failed to load checkpoints'}), 500

@app.route('/chatbot')
@app.route('/chatbot/<int:itinerary_id>')
def chatbot(itinerary_id=None):
    """Travel companion chatbot page"""
    itinerary = None
    suggestions = []
    
    if itinerary_id:
        itinerary = TravelItinerary.query.get_or_404(itinerary_id)
        
        
        chatbot_service = TravelChatbot()
        context = chatbot_service.get_contextual_suggestions(
            itinerary.destination, 
            itinerary.get_interests_list()
        )
        suggestions = context.get('suggestions', [])
    
    return render_template('chatbot.html', itinerary=itinerary, suggestions=suggestions)

@app.route('/api/chatbot', methods=['POST'])
def chatbot_api():
    """API endpoint for chatbot interactions"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        itinerary_id = data.get('itinerary_id')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'})
        

        chatbot_service = TravelChatbot()
        
        
        itinerary_context = None
        user_preferences = None
        
        if itinerary_id:
            itinerary = TravelItinerary.query.get(itinerary_id)
            if itinerary:
                itinerary_context = itinerary.get_itinerary_data()
                user_preferences = itinerary.get_interests_list()
        
        # Generate response
        response = chatbot_service.generate_response(
            message, 
            itinerary_context=itinerary_context,
            user_preferences=user_preferences
        )
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Error in chatbot API: {e}")
        return jsonify({
            'success': False, 
            'error': 'Sorry, I encountered an error processing your message.'
        })

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.route('/itinerary/<int:itinerary_id>/download')
def download_itinerary_pdf(itinerary_id):
    
    itinerary = TravelItinerary.query.get_or_404(itinerary_id)
    checkpoints = Checkpoint.query.filter_by(itinerary_id=itinerary_id).order_by(Checkpoint.day, Checkpoint.time).all()
    
    days_data = {}
    for checkpoint in checkpoints:
        if checkpoint.day not in days_data:
            days_data[checkpoint.day] = []
        days_data[checkpoint.day].append(checkpoint)

    
    pdf_data = create_itinerary_pdf(itinerary, days_data) 

    
    return Response(
        pdf_data,
        mimetype='application/pdf',
        headers={
            'Content-Disposition': f'attachment;filename={itinerary.destination.lower().replace(" ", "_")}_itinerary.pdf'
        }
    )


class PDF(FPDF):
    def header(self):
    
        self.set_font('Helvetica', 'B', 15)
        
        self.cell(80)
        self.cell(30, 10, 'TripCraftAI Itinerary', 0, 0, 'C')
        self.ln(20)

    def footer(self):

        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')


class PDF(FPDF):
    def header(self):
    
        self.set_font('Helvetica', 'B', 15)
        
        self.cell(80)
        self.cell(30, 10, 'TripCraftAI Itinerary', 0, 0, 'C')
        
        self.ln(20)

    def footer(self):

        self.set_y(-15)

        self.set_font('Helvetica', 'I', 8)
        
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_itinerary_pdf(itinerary, days_data):
    """Generates a PDF document for the itinerary using FPDF2."""
    
    pdf = PDF()
    pdf.add_page()
    
    # --- Itinerary Header ---
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 10, f'{itinerary.destination}', 0, 1, 'L')
    
    pdf.set_font('Helvetica', '', 12)
    pdf.cell(0, 10, f"{itinerary.duration} Days | Budget: Rs {itinerary.budget:,.0f} | Created: {itinerary.created_at.strftime('%b %d, %Y')}", 0, 1, 'L')
    pdf.ln(10)

    
    for day_num in range(1, itinerary.duration + 1):
        day_data = days_data.get(day_num, [])
        
        pdf.set_font('Helvetica', 'B', 16)
        pdf.cell(0, 10, f'Day {day_num}', 0, 1, 'L')
        pdf.line(pdf.get_x(), pdf.get_y(), pdf.get_x() + 190, pdf.get_y()) # Underline
        pdf.ln(5)
        
        if day_data:
            for checkpoint in day_data:
                pdf.set_font('Helvetica', 'B', 12)
                pdf.cell(0, 8, f"{checkpoint.time} - {checkpoint.location}", 0, 1)
                
                pdf.set_font('Helvetica', '', 12)
                
                pdf.multi_cell(0, 8, f"Activity: {checkpoint.activity}")
                
                if checkpoint.estimated_cost > 0:
                    pdf.cell(0, 8, f"Est. Cost: Rs {checkpoint.estimated_cost:,.0f}", 0, 1)
                pdf.ln(5) 
        else:
            pdf.set_font('Helvetica', 'I', 12)
            pdf.cell(0, 10, 'No activities planned for this day.', 0, 1)
            pdf.ln(5)

    return bytes(pdf.output(dest='S'))

recommendation_service = RecommendationService()

@app.route('/recommendations')
def recommendations():

    recommended_destinations = recommendation_service.get_recommendations()
    
    return render_template('recommendations.html', recommendations=recommended_destinations)
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
