import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Weather API configuration
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "6f88d31629b253fb97526c12ca07a172")
WEATHER_API_BASE_URL = "https://api.openweathermap.org/data/2.5"

class WeatherService:
    def __init__(self):
        self.api_key = OPENWEATHER_API_KEY
        
    def get_coordinates(self, city_name: str) -> Optional[Dict]:
        """Get latitude and longitude for a city"""
        if not self.api_key:
            return None
            
        geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct"
        
        
        search_queries = [
            f"{city_name},IN",  
            f"{city_name},India",  
            city_name,  
        ]
        
        state_capitals = {
            'Punjab': 'Chandigarh',
            'Himachal Pradesh': 'Shimla',
            'Rajasthan': 'Jaipur',
            'Kerala': 'Thiruvananthapuram',
            'Tamil Nadu': 'Chennai',
            'Karnataka': 'Bangalore',
            'Goa': 'Panaji',
            'Gujarat': 'Gandhinagar',
            'Maharashtra': 'Mumbai'
        }
        
        clean_name = city_name.replace(', India', '').strip()
        if clean_name in state_capitals:
            search_queries.insert(0, f"{state_capitals[clean_name]},IN")
        
        for query in search_queries:
            try:
                params = {
                    'q': query,
                    'limit': 1,
                    'appid': self.api_key
                }
                
                response = requests.get(geocoding_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    return {
                        'lat': data[0]['lat'],
                        'lon': data[0]['lon'],
                        'name': data[0]['name']
                    }
            except Exception as e:
                print(f"Error with query '{query}': {e}")
                continue
        
        print(f"No coordinates found for {city_name}")
        return None
    
    def get_current_weather(self, city_name: str) -> Optional[Dict]:
        """Get current weather for a city"""
        if not self.api_key:
            return None
            
        coords = self.get_coordinates(city_name)
        if not coords:
            return None
            
        weather_url = f"{WEATHER_API_BASE_URL}/weather"
        params = {
            'lat': coords['lat'],
            'lon': coords['lon'],
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(weather_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return {
                'main': {
                    'temp': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main'].get('pressure', 0)
                },
                'weather': [{
                    'main': data['weather'][0]['main'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0].get('icon', '')
                }],
                'wind': {
                    'speed': data.get('wind', {}).get('speed', 0)
                },
                'visibility': data.get('visibility', 10000),
                'name': coords['name'],
                'sys': {
                    'country': data.get('sys', {}).get('country', 'IN')
                }
            }
        except Exception as e:
            print(f"Error getting weather for {city_name}: {e}")
        
        return None
    
    def get_forecast(self, city_name: str, days: int = 5) -> Optional[List[Dict]]:
        """Get weather forecast for upcoming days"""
        if not self.api_key:
            return None
            
        coords = self.get_coordinates(city_name)
        if not coords:
            return None
            
        forecast_url = f"{WEATHER_API_BASE_URL}/forecast"
        params = {
            'lat': coords['lat'],
            'lon': coords['lon'],
            'appid': self.api_key,
            'units': 'metric'
        }
        
        try:
            response = requests.get(forecast_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            forecast_list = []
            for item in data['list'][:days * 8]:  
                forecast_list.append({
                    'datetime': datetime.fromtimestamp(item['dt']),
                    'temperature': item['main']['temp'],
                    'description': item['weather'][0]['description'],
                    'main': item['weather'][0]['main'],
                    'humidity': item['main']['humidity'],
                    'wind_speed': item.get('wind', {}).get('speed', 0),
                    'precipitation': item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0)
                })
            
            return forecast_list
        except Exception as e:
            print(f"Error getting forecast for {city_name}: {e}")
        
        return None
    
    def check_severe_weather(self, city_name: str, travel_date: datetime) -> Optional[Dict]:
        """Check for severe weather conditions for a specific travel date"""
        forecast = self.get_forecast(city_name, 5)
        if not forecast:
            return None
        
    
        target_date = travel_date.date()
        severe_conditions = []
        
        for forecast_item in forecast:
            forecast_date = forecast_item['datetime'].date()
            
            if forecast_date == target_date:
          
                is_severe = False
                severity_reasons = []
                
                
                if forecast_item['precipitation'] > 10:
                    is_severe = True
                    severity_reasons.append(f"Heavy rainfall ({forecast_item['precipitation']:.1f}mm)")
                
                # Strong winds (>20 km/h)
                if forecast_item['wind_speed'] > 5.5:  # 5.5 m/s = ~20 km/h
                    is_severe = True
                    severity_reasons.append(f"Strong winds ({forecast_item['wind_speed']:.1f} m/s)")
                
                # Extreme temperatures
                if forecast_item['temperature'] > 40 or forecast_item['temperature'] < 5:
                    is_severe = True
                    severity_reasons.append(f"Extreme temperature ({forecast_item['temperature']:.1f}°C)")
                
                # Severe weather types
                severe_weather_types = ['Thunderstorm', 'Snow', 'Extreme']
                if forecast_item['main'] in severe_weather_types:
                    is_severe = True
                    severity_reasons.append(f"{forecast_item['main']}")
                
                if is_severe:
                    severe_conditions.append({
                        'datetime': forecast_item['datetime'],
                        'reasons': severity_reasons,
                        'temperature': forecast_item['temperature'],
                        'description': forecast_item['description'],
                        'precipitation': forecast_item['precipitation'],
                        'wind_speed': forecast_item['wind_speed']
                    })
        
        if severe_conditions:
            return {
                'city': city_name,
                'date': target_date,
                'severity': 'high' if len(severe_conditions) > 2 else 'medium',
                'conditions': severe_conditions,
                'alert_message': f"Severe weather expected in {city_name} on {target_date.strftime('%B %d, %Y')}"
            }
        
        return None


weather_service = WeatherService()
