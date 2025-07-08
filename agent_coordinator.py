import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio
from dataclasses import dataclass

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain.tools import Tool
from langchain_core.messages import HumanMessage, SystemMessage

from weather_service import WeatherService
from budget_optimizer import BudgetOptimizer

@dataclass
class AgentContext:
    """Shared context between agents"""
    user_id: Optional[int] = None
    itinerary_id: Optional[int] = None
    current_location: Optional[str] = None
    travel_date: Optional[datetime] = None
    budget_remaining: Optional[float] = None
    user_preferences: Dict[str, Any] = None
    
class TravelAgentCoordinator:
    """
    Multi-agent coordinator for proactive travel assistance
    Orchestrates specialized agents for different travel domains
    """
    
    def __init__(self):
        self.weather_service = WeatherService()
        self.budget_optimizer = BudgetOptimizer()
        
        # Initialize base LLM
        try:
            self.llm = ChatGroq(
                groq_api_key=os.environ.get("GROQ_API_KEY"),
                model_name="llama-3.1-8b-instant",
                temperature=0.3,  
                max_tokens=1000
            )
        except Exception as e:
            logging.error(f"Failed to initialize LLM: {e}")
            self.llm = None
        
        # Agent memory for learning patterns
        self.agent_memory = {
            'successful_recommendations': [],
            'user_feedback_patterns': {},
            'weather_adaptations': [],
            'budget_optimizations': []
        }
    
    def create_weather_agent(self) -> Tool:
        """Weather monitoring and advisory agent"""
        def weather_analysis(query: str) -> str:
            try:

                location = self._extract_location(query)
                if not location:
                    return "Location not specified for weather analysis"
                

                current = self.weather_service.get_current_weather(location)
                forecast = self.weather_service.get_forecast(location, days=3)
                
                if not current:
                    return f"Weather data unavailable for {location}"
                

                analysis = self._analyze_weather_conditions(current, forecast)
                
                return json.dumps({
                    'current_conditions': current,
                    'forecast_summary': forecast[:3] if forecast else [],
                    'travel_recommendations': analysis['recommendations'],
                    'alerts': analysis['alerts'],
                    'suggested_changes': analysis['changes']
                })
                
            except Exception as e:
                return f"Weather analysis failed: {str(e)}"
        
        return Tool(
            name="weather_agent",
            description="Monitors weather conditions and provides proactive travel advice",
            func=weather_analysis
        )
    
    def create_budget_agent(self) -> Tool:
        """Budget monitoring and optimization agent"""
        def budget_analysis(query: str) -> str:
            try:

                context = self._extract_budget_context(query)
                

                recommendations = self.budget_optimizer.get_budget_recommendations(
                    context.get('destination', ''),
                    context.get('duration', 3),
                    context.get('budget', 25000),
                    context.get('interests', [])
                )
      
                cost_saving_tips = self._generate_cost_saving_tips(context)
                
                return json.dumps({
                    'budget_analysis': recommendations,
                    'cost_saving_opportunities': cost_saving_tips,
                    'spending_alerts': self._check_budget_alerts(context),
                    'optimization_suggestions': self._suggest_budget_optimizations(context)
                })
                
            except Exception as e:
                return f"Budget analysis failed: {str(e)}"
        
        return Tool(
            name="budget_agent",
            description="Monitors budget and suggests cost optimizations",
            func=budget_analysis
        )
    
    def create_activity_agent(self) -> Tool:
        """Activity discovery and management agent"""
        def activity_recommendations(query: str) -> str:
            try:
                context = self._extract_activity_context(query)

                activities = self._discover_activities(context)
                

                alternatives = self._find_activity_alternatives(context)
                
                return json.dumps({
                    'new_activities': activities,
                    'alternative_suggestions': alternatives,
                    'timing_optimizations': self._optimize_activity_timing(context),
                    'booking_opportunities': self._find_booking_deals(context)
                })
                
            except Exception as e:
                return f"Activity recommendations failed: {str(e)}"
        
        return Tool(
            name="activity_agent", 
            description="Discovers activities and optimizes travel experiences",
            func=activity_recommendations
        )
    
