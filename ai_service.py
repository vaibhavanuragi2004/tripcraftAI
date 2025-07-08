import json
import os
import logging
from typing import Dict, List, Any, Optional

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain.chains import LLMChain


try:
    llm = ChatGroq(
        groq_api_key=os.environ.get("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        temperature=0.7,
        max_tokens=4000
    )
    print(f"LangChain GROQ client initialized successfully with key length: {len(os.environ.get('GROQ_API_KEY', ''))}")
except Exception as e:
    print(f"Error initializing LangChain GROQ client: {e}")
    llm = None


class ActivityModel(BaseModel):
    time: str = Field(description="Time of the activity in HH:MM format")
    activity: str = Field(description="Name of the activity")
    location: str = Field(description="Specific location name")
    duration: str = Field(description="Duration of the activity")
    cost: float = Field(description="Estimated cost in Indian Rupees")
    description: str = Field(description="Detailed description of the activity")
    tips: str = Field(description="Practical tips for Indian tourists")

class ItineraryDay(BaseModel):
    day: int = Field(description="Day number of the itinerary")
    activities: List[ActivityModel] = Field(description="List of activities for the day")

class TravelItinerary(BaseModel):
    destination: str = Field(description="Travel destination")
    duration: int = Field(description="Trip duration in days")
    days: List[ItineraryDay] = Field(description="Daily itinerary breakdown")
    travel_tips: List[str] = Field(description="Helpful travel tips")
    budget_breakdown: Dict[str, float] = Field(description="Budget allocation by category")

def generate_basic_itinerary(destination, duration, budget, interests):
    """
    Generate a basic itinerary template when AI is not available
    """
    interests_str = ", ".join(interests) if interests else "general sightseeing"
    
    
    daily_budget = budget / duration if duration > 0 else budget
    
    basic_itinerary = {
        "destination": destination,
        "duration": duration,
        "days": [],
        "travel_tips": [
            f"Pack comfortable walking shoes for exploring {destination}",
            "Carry a water bottle and stay hydrated",
            "Try local cuisine but ensure food safety",
            "Keep emergency contacts and important documents handy",
            "Respect local customs and traditions"
        ],
        "budget_breakdown": {
            "accommodation": round(budget * 0.35),
            "food": round(budget * 0.25),
            "transport": round(budget * 0.20),
            "activities": round(budget * 0.15),
            "shopping": round(budget * 0.05)
        }
    }
    
    # Generate basic daily structure
    for day in range(1, duration + 1):
        day_activities = [
            {
                "time": "09:00",
                "activity": "Morning Exploration",
                "location": f"Central {destination}",
                "duration": "3 hours",
                "cost": daily_budget * 0.3,
                "description": f"Explore the main attractions of {destination} focusing on {interests_str}",
                "tips": "Start early to avoid crowds and heat"
            },
            {
                "time": "13:00",
                "activity": "Local Lunch",
                "location": "Local Restaurant",
                "duration": "1 hour",
                "cost": daily_budget * 0.2,
                "description": "Try authentic local cuisine",
                "tips": "Ask locals for restaurant recommendations"
            },
            {
                "time": "15:00",
                "activity": "Afternoon Activity",
                "location": f"{destination} Highlights",
                "duration": "2 hours",
                "cost": daily_budget * 0.25,
                "description": f"Continue exploring {destination} based on your interests in {interests_str}",
                "tips": "Take breaks and stay hydrated"
            }
        ]
        
        basic_itinerary["days"].append({
            "day": day,
            "activities": day_activities
        })
    
    return basic_itinerary

def generate_travel_itinerary(destination, duration, budget, interests):
    """
    Generate a detailed travel itinerary using LangChain for Indian tourists
    """
    if not llm:
        logging.warning("LangChain LLM not available, using basic itinerary")
        return generate_basic_itinerary(destination, duration, budget, interests)
    
    try:
        # Prepare interests string
        interests_str = ", ".join(interests) if interests else "general sightseeing"
        
        # Create system prompt template
        system_template = """You are an expert travel planner specializing in trips for Indian tourists. 
        You create detailed, culturally-aware itineraries with accurate costs in Indian Rupees.
        Always respond with valid JSON that matches the exact schema provided."""
        

        human_template = """Create a detailed {duration}-day travel itinerary for {destination} for Indian tourists with a budget of ₹{budget}.

Tourist interests: {interests}

Requirements:
1. Include specific places, timings, and estimated costs in Indian Rupees
2. Consider Indian cultural preferences and dietary requirements
3. Include practical tips for Indian travelers
4. Suggest budget-friendly options and local transportation
5. Include authentic local experiences and cultural sites
6. Consider seasonal weather and best visiting times

Return ONLY a valid JSON object with this exact structure:
{{
  "destination": "{destination}",
  "duration": {duration},
  "days": [
    {{
      "day": 1,
      "activities": [
        {{
          "time": "09:00",
          "activity": "Activity name",
          "location": "Specific location",
          "duration": "2 hours",
          "cost": 500,
          "description": "Detailed description",
          "tips": "Practical tips for Indian tourists"
        }}
      ]
    }}
  ],
  "travel_tips": [
    "Location-specific tips including best travel routes and timing advice"
  ],
  "budget_breakdown": {{
    "accommodation": 7000,
    "food": 4000,
    "transport": 3000,
    "activities": 4000,
    "shopping": 2000
  }}
}}

Plan each day to cover one geographical area/zone efficiently. Ensure realistic travel times and costs within the specified budget."""
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template(human_template)
        ])
        
        # Create chain with LangChain
        chain = prompt | llm
        
        # Execute chain
        response = chain.invoke({
            "destination": destination,
            "duration": duration,
            "budget": budget,
            "interests": interests_str
        })
        
        content = response.content.strip()

        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            content = content[start:end].strip()
        elif '```' in content:
            start = content.find('```') + 3
            end = content.find('```', start)
            content = content[start:end].strip()
        
        try:
            itinerary_data = json.loads(content)
            logging.info(f"Successfully generated LangChain itinerary for {destination}")
            return itinerary_data
        except json.JSONDecodeError as json_error:
            logging.error(f"LangChain JSON decode error: {json_error}")
            return generate_basic_itinerary(destination, duration, budget, interests)
            
    except Exception as e:
        logging.error(f"LangChain error generating itinerary: {e}")
        return generate_basic_itinerary(destination, duration, budget, interests)

def get_location_suggestions(query):
    """
    Get location suggestions based on user input using LangChain
    """
    if not llm:
        return []
    
    try:
        
        suggestion_template = """Based on the query "{query}", suggest 5 popular travel destinations in India.
        Return ONLY a JSON array of destination names like: ["Mumbai", "Delhi", "Goa", "Kerala", "Rajasthan"]
        Focus on destinations that match the query or are popular for Indian tourists."""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a travel expert. Return only valid JSON arrays of Indian destinations."),
            ("human", suggestion_template)
        ])
        
        # Create chain
        chain = prompt | llm
        
        # Execute chain
        response = chain.invoke({"query": query})
        content = response.content.strip()
        
        # Extract JSON if wrapped
        if '```json' in content:
            start = content.find('```json') + 7
            end = content.find('```', start)
            content = content[start:end].strip()
        elif '```' in content:
            start = content.find('```') + 3
            end = content.find('```', start)
            content = content[start:end].strip()
        
        suggestions = json.loads(content)
        return suggestions if isinstance(suggestions, list) else []
        
    except Exception as e:
        logging.error(f"LangChain error getting location suggestions: {e}")
        return []



def get_station_code(city_name: str) -> Optional[str]:
    """
    Uses the LLM to find the primary Indian Railways station code for a given city.
    """
    if not llm:
        return None

    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an Indian Railways expert. Your task is to provide the primary, most common railway station code for a given Indian city. Respond with ONLY the station code in uppercase. For example, for 'New Delhi' respond with 'NDLS'. For 'Kolkata' respond with 'HWH'. If you cannot find a code, respond with 'None'."),
            ("human", "City: {city}")
        ])

        chain = prompt | llm
        response = chain.invoke({"city": city_name})
        
        code = response.content.strip().upper()

        if code.lower() == 'none' or len(code) > 6: # Basic validation
            logging.warning(f"Could not find a valid station code for '{city_name}'.")
            return None
        
        logging.info(f"Found station code '{code}' for city '{city_name}'.")
        return code

    except Exception as e:
        logging.error(f"Error getting station code for '{city_name}': {e}")
        return None        
