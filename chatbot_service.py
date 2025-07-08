import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

# LangChain imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain.memory import ConversationBufferWindowMemory
from langchain.chains import ConversationChain

class TravelChatbot:
    def __init__(self):
        try:
            # Initialize LangChain LLM
            self.llm = ChatGroq(
                groq_api_key=os.environ.get("GROQ_API_KEY"),
                model_name="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=300
            )
            
            # Initialize conversation memory
            self.memory = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 exchanges
                return_messages=True
            )
            
            # Creating conversation prompt template
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert travel companion AI for Indian tourists. You provide helpful, 
                accurate, and culturally-aware travel advice. You have access to real-time weather data 
                and can help with:
                
                - Weather updates and travel recommendations
                - Budget planning and cost-effective suggestions
                - Cultural experiences and local recommendations
                - Transportation and accommodation advice
                - Food recommendations (considering Indian dietary preferences)
                - Safety and practical travel tips
                
                Keep responses helpful but informative. If the question is about:
                - Weather: Use current conditions and practical advice
                - Budget: Give cost-effective suggestions 
                - Activities: Suggest culturally relevant experiences
                - Food: Recommend authentic local cuisine
                - Transport: Provide practical travel tips for India
                - Safety: Give responsible travel advice
                
                Respond in a friendly, knowledgeable tone. Keep responses under 200 words unless detailed explanation is needed."""),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}")
            ])
            
            # Create conversation chain
            self.conversation = ConversationChain(
                llm=self.llm,
                memory=self.memory,
                prompt=self.prompt,
                verbose=True
            )
            
            print("LangChain chatbot initialized successfully")
        except Exception as e:
            print(f"Error initializing LangChain chatbot: {e}")
            self.llm = None
            self.memory = None
            self.conversation = None

    def get_context_from_itinerary(self, itinerary_data):
        """Extract relevant context from user's itinerary"""
        try:
            if isinstance(itinerary_data, str):
                itinerary_data = json.loads(itinerary_data)
            
            destination = itinerary_data.get('destination', 'Unknown')
            duration = itinerary_data.get('duration', 0)
            budget = itinerary_data.get('budget_breakdown', {})
            
            context = f"""
            Current Trip Context:
            - Destination: {destination}
            - Duration: {duration} days
            - Budget breakdown: Accommodation ₹{budget.get('accommodation', 0)}, Food ₹{budget.get('food', 0)}, Transport ₹{budget.get('transport', 0)}
            
            You are helping with this specific trip. Provide contextual advice based on this itinerary.
            """
            
            return context
        except Exception as e:
            logging.error(f"Error extracting itinerary context: {e}")
            return ""

    def generate_response(self, user_message, itinerary_context=None, user_preferences=None):
        """Generate chatbot response using LangChain"""
        if not self.conversation:
            return self.get_fallback_response(user_message)
        
        try:
            # Build context from itinerary if available
            context_info = ""
            if itinerary_context:
                context_info = self.get_context_from_itinerary(itinerary_context)
                # Add context to the conversation temporarily
                if context_info:
                    enhanced_message = f"Context: {context_info}\n\nUser question: {user_message}"
                else:
                    enhanced_message = user_message
            else:
                enhanced_message = user_message
            
           
            response = self.conversation.predict(input=enhanced_message)
            
            return response
            
        except Exception as e:
            logging.error(f"LangChain error generating chatbot response: {e}")
            # Fallback to direct LLM call
            try:
                context_info = ""
                if itinerary_context:
                    context_info = self.get_context_from_itinerary(itinerary_context)
                
                messages = [
                    ("system", f"""You are an expert travel companion AI for Indian tourists. 
                    {context_info}
                    
                    Provide helpful, culturally-aware travel advice. Keep responses under 200 words."""),
                    ("human", user_message)
                ]
                
                response = self.llm.invoke(messages)
                return response.content
                
            except Exception as fallback_error:
                logging.error(f"Fallback chatbot error: {fallback_error}")
                return self.get_fallback_response(user_message)

    def get_fallback_response(self, user_message):
        """Provide rule-based responses when AI is unavailable"""
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['weather', 'temperature', 'rain', 'climate']):
            return "I'd recommend checking current weather conditions for your destination. Pack accordingly - light clothes for warm weather, rain gear during monsoon season, and layers for hill stations."
        
        elif any(word in message_lower for word in ['budget', 'cost', 'money', 'expensive']):
            return "For budget travel in India, consider staying in budget hotels or hostels, use public transport, eat at local restaurants, and look for free cultural activities. Street food is delicious and affordable!"
        
        elif any(word in message_lower for word in ['food', 'eat', 'restaurant', 'cuisine']):
            return "Indian cuisine varies greatly by region. Try local specialties, but ensure the place looks clean. Start with milder dishes if you're not used to spicy food. Always drink bottled or filtered water."
        
        elif any(word in message_lower for word in ['transport', 'travel', 'train', 'bus']):
            return "Indian Railways is extensive and economical. Book in advance for longer routes. For local transport, try metro, buses, or app-based cabs. Auto-rickshaws are good for short distances."
        
        else:
            return "I'm here to help with your travel questions! You can ask me about weather, budget tips, food recommendations, transportation, or local attractions."

    def get_contextual_suggestions(self, destination, interests=None):
        """Generate proactive travel suggestions using LangChain"""
        if not self.llm:
            return {
                'weather_context': f"Check the current weather in {destination} before you travel.",
                'suggestions': [
                    f"Popular attractions in {destination}",
                    "Local food specialties to try",
                    "Best transportation options",
                    "Cultural etiquette to follow"
                ]
            }
        
        try:
            interests_str = ", ".join(interests) if interests else "general tourism"
            
            prompt_template = """Provide 4 helpful travel suggestions for someone visiting {destination} who is interested in {interests}.
            Return a JSON object with:
            {{
              "weather_context": "Brief weather advice for {destination}",
              "suggestions": ["suggestion 1", "suggestion 2", "suggestion 3", "suggestion 4"]
            }}"""
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a travel expert. Return only valid JSON."),
                ("human", prompt_template)
            ])
            
            chain = prompt | self.llm
            
            response = chain.invoke({
                "destination": destination,
                "interests": interests_str
            })
            
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
            
            suggestions_data = json.loads(content)
            return suggestions_data
            
        except Exception as e:
            logging.error(f"LangChain error getting contextual suggestions: {e}")
            return {
                'weather_context': f"Check the current weather in {destination} before you travel.",
                'suggestions': [
                    f"Research popular attractions in {destination}",
                    "Try local cuisine specialties", 
                    "Learn about local customs and etiquette",
                    "Plan your transportation in advance"
                ]
            }
    
    def clear_history(self):
        """Clear conversation history"""
        if self.memory:
            self.memory.clear()
        if hasattr(self, 'conversation_history'):
            self.conversation_history = []
