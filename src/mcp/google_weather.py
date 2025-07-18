"""
Google Weather API MCP connector
Handles weather forecast data for travel planning
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import json

from mcp.base_connector import BaseMCPConnector
from mcp.google_places import GooglePlacesConnector
from core.models import WeatherInfo
from core.exceptions import GoogleAPIError
from core.constants import GOOGLE_APIS


class GoogleWeatherConnector(BaseMCPConnector):
    """MCP connector for Google Weather API"""
    
    def __init__(self, api_key: str):
        super().__init__("", "google_weather")
        self.base_url = "https://weather.googleapis.com"
        # Create a places connector to use for geocoding
        self.places_connector = GooglePlacesConnector(api_key)
    
    async def test_connection(self) -> bool:
        """Test Weather API connectivity"""
        try:
            # Test with current weather for a known location
            weather = await self.get_current_weather("40.7128,-74.0060")  # NYC coordinates
            return weather is not None
            
        except Exception as e:
            self.logger.error(f"Weather API connection test failed: {e}")
            return False
    
    async def get_current_weather(self, location: str) -> Optional[WeatherInfo]:
        """Get current weather for a location
        
        Args:
            location: Can be either coordinates "lat,lng" or a place name that will be converted
        """
        url = f"{self.base_url}/v1/currentConditions:lookup"
        
        # Convert location to coordinates if needed
        if ',' in location and any(char.isdigit() for char in location):
            # Already in coordinate format
            lat, lng = location.split(',')
            lat = float(lat.strip())
            lng = float(lng.strip())
        else:
            # Convert place name to coordinates using Google Places geocoding
            try:
                lat, lng = await self.places_connector.geocode_location(location)
            except Exception as e:
                self.logger.error(f"Geocoding error for {location}: {e}")
                # Fallback coordinates if geocoding fails (New York City)
                lat, lng = 40.7128, -74.0060
        
        # Build params with nested location object
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "languageCode": "en"
        }
        
        try:
            self.logger.info(f"Getting current weather for: {location} ({lat},{lng})")
            self.logger.debug(f"Request params: {params}")
            
            result = await self._make_request("GET", url, params)
            
            if not result:
                self.logger.warning(f"No current weather data for {location}")
                return None
            
            # Log the full response structure to help debug
            self.logger.debug(f"Current weather API response: {result}")
            
            return self._parse_current_weather(result)
            
        except Exception as e:
            self.logger.error(f"Error getting current weather: {e}")
            # Return mock data for development
            return self._generate_mock_weather(location, datetime.now().strftime("%Y-%m-%d"))
    
    async def get_weather_forecast(self, location: str, days: int = 7) -> List[WeatherInfo]:
        """Get weather forecast for multiple days
        
        Args:
            location: Can be either coordinates "lat,lng" or a place name that will be converted
            days: Number of days to forecast (max 10)
        """
        url = f"{self.base_url}/v1/forecast/days:lookup"
        
        # Convert location to coordinates if needed
        if ',' in location and any(char.isdigit() for char in location):
            # Already in coordinate format
            lat, lng = location.split(',')
            lat = float(lat.strip())
            lng = float(lng.strip())
        else:
            # Convert place name to coordinates using Google Places geocoding
            try:
                lat, lng = await self.places_connector.geocode_location(location)
            except Exception as e:
                self.logger.error(f"Geocoding error for {location}: {e}")
                # Fallback coordinates if geocoding fails (New York City)
                lat, lng = 40.7128, -74.0060
        
        # Build params with nested location object
        params = {
            "location.latitude": lat,
            "location.longitude": lng,
            "days": min(days, 10),
            "pageSize": min(days, 10),
            "languageCode": "en",
            "unitsSystem": "METRIC"  # Add unitsSystem parameter for forecast
        }
        
        try:
            self.logger.info(f"Getting {days}-day forecast for: {location} ({lat},{lng})")
            self.logger.debug(f"Request params: {params}")
            
            result = await self._make_request("GET", url, params)
            
            # Log the full response structure to help debug
            self.logger.debug(f"Forecast API response: {result}")
            
            if "forecastDays" not in result:
                self.logger.warning(f"No forecast data for {location}")
                return self._generate_mock_forecast(location, days)
            
            weather_list = []
            for day_data in result["forecastDays"][:days]:
                weather_info = self._parse_forecast_day(day_data)
                if weather_info:
                    weather_list.append(weather_info)
            
            self.logger.info(f"Retrieved {len(weather_list)} days of forecast")
            return weather_list
            
        except Exception as e:
            self.logger.error(f"Error getting weather forecast: {e}")
            # Return mock data for development
            return self._generate_mock_forecast(location, days)
    
    async def get_weather_for_dates(self, location: str, start_date: str, end_date: str) -> List[WeatherInfo]:
        """Get weather forecast for specific date range"""
        try:
            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)
            days = (end_dt - start_dt).days + 1
            
            if days > 10:
                self.logger.warning(f"Requested {days} days, limiting to 10")
                days = 10
            
            return await self.get_weather_forecast(location, days)
            
        except ValueError as e:
            self.logger.error(f"Invalid date format: {e}")
            return []
    
    def _parse_current_weather(self, data: Dict[str, Any]) -> Optional[WeatherInfo]:
        """Parse current weather API response into WeatherInfo model"""
        try:
            # Extract temperature values
            temp = data.get("temperature", {})
            temp_value = temp.get("value", 20.0) if isinstance(temp, dict) else 20.0
            
            # Extract feels like temperature
            feels_like = data.get("feelsLikeTemperature", {})
            feels_like_value = feels_like.get("value", temp_value) if isinstance(feels_like, dict) else temp_value
            
            # Extract wind data
            wind = data.get("windConditions", {})
            wind_speed = wind.get("speed", {}).get("value", 10.0) if isinstance(wind, dict) else 10.0
            
            # Extract precipitation data - it's an object with 'percent' and 'type'
            precipitation = data.get("precipitation", {})
            if isinstance(precipitation, dict):
                precip_chance = precipitation.get("percent", 0)
            else:
                precip_chance = 0
            
            # Get weather description - it's an object with 'type' and other fields
            weather_condition_obj = data.get("weatherCondition", {})
            if isinstance(weather_condition_obj, dict):
                # Try to get the type directly first
                weather_condition = weather_condition_obj.get("type", None)
                
                # If type is not found, look for alternative fields
                if not weather_condition:
                    # Check for 'summary' field which might contain the weather description
                    weather_condition = weather_condition_obj.get("summary", None)
                
                # Check for 'condition' or 'description' as alternative fields
                if not weather_condition:
                    weather_condition = (weather_condition_obj.get("condition") or 
                                        weather_condition_obj.get("description") or
                                        "Unknown")
                
                # Convert enum-style type to readable description if it's a string
                if weather_condition and isinstance(weather_condition, str):
                    weather_condition = weather_condition.replace("_", " ").title()
                else:
                    weather_condition = "Unknown"
            else:
                weather_condition = "Unknown"
                
            # Debug log the weather condition parsing
            self.logger.debug(f"Weather condition extracted: {weather_condition}")
            self.logger.debug(f"From weather condition object: {weather_condition_obj}")
            
            # Extract humidity
            humidity = data.get("relativeHumidity", 50)
            
            return WeatherInfo(
                date=datetime.now().strftime("%Y-%m-%d"),
                temperature_high=temp_value,
                temperature_low=temp_value - 5,  # Estimate for current conditions
                description=weather_condition,
                humidity=humidity,
                wind_speed=wind_speed * 3.6,  # Convert m/s to km/h
                precipitation_chance=precip_chance
            )
        except Exception as e:
            self.logger.error(f"Error parsing current weather data: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.logger.debug(f"Raw data: {data}")
            return None
    
    def _parse_forecast_day(self, day_data: Dict[str, Any]) -> Optional[WeatherInfo]:
        """Parse a single day from forecast data"""
        try:
            # Extract date from display date
            display_date = day_data.get("displayDate", {})
            date_str = f"{display_date.get('year')}-{display_date.get('month'):02d}-{display_date.get('day'):02d}"
            
            # Extract temperature data
            max_temp = day_data.get("maxTemperature", {})
            min_temp = day_data.get("minTemperature", {})
            max_temp_value = max_temp.get("value", 25.0) if isinstance(max_temp, dict) else 25.0
            min_temp_value = min_temp.get("value", 15.0) if isinstance(min_temp, dict) else 15.0
            
            # Get daytime weather info (using daytime as primary)
            daytime = day_data.get("daytime", {})
            
            # Extract weather condition - it's an object with 'type'
            weather_condition_obj = daytime.get("weatherCondition", {})
            if isinstance(weather_condition_obj, dict):
                # Try to get the type directly first
                weather_condition = weather_condition_obj.get("type", None)
                
                # If type is not found, look for alternative fields
                if not weather_condition:
                    # Check for 'summary' field which might contain the weather description
                    weather_condition = weather_condition_obj.get("summary", None)
                
                # Check for 'condition' or 'description' as alternative fields
                if not weather_condition:
                    weather_condition = (weather_condition_obj.get("condition") or 
                                        weather_condition_obj.get("description") or
                                        "Unknown")
                
                # Convert enum-style type to readable description if it's a string
                if weather_condition and isinstance(weather_condition, str):
                    weather_condition = weather_condition.replace("_", " ").title()
                else:
                    weather_condition = "Unknown"
            else:
                weather_condition = "Unknown"
                
            # Debug log the weather condition parsing
            self.logger.debug(f"Forecast day weather condition extracted: {weather_condition}")
            self.logger.debug(f"From weather condition object: {weather_condition_obj}")
            
            # Extract daytime precipitation - it's an object with 'percent' and 'type'
            daytime_precip = daytime.get("precipitation", {})
            if isinstance(daytime_precip, dict):
                precip_chance = daytime_precip.get("percent", 0)
            else:
                precip_chance = 0
            
            daytime_wind = daytime.get("windConditions", {})
            wind_speed = 0
            if isinstance(daytime_wind, dict):
                wind_data = daytime_wind.get("maxSpeed", {})
                wind_speed = wind_data.get("value", 0) if isinstance(wind_data, dict) else 0
            
            # Extract humidity from daytime
            humidity = daytime.get("relativeHumidity", 60)
            
            return WeatherInfo(
                date=date_str,
                temperature_high=max_temp_value,
                temperature_low=min_temp_value,
                description=weather_condition,
                humidity=humidity,
                wind_speed=wind_speed * 3.6,  # Convert m/s to km/h
                precipitation_chance=precip_chance
            )
        except Exception as e:
            self.logger.error(f"Error parsing forecast day: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            self.logger.debug(f"Raw day data: {day_data}")
            return None
    
    # Location to coordinates conversion is now handled by GooglePlacesConnector
    
    def _generate_mock_weather(self, location: str, date: str) -> WeatherInfo:
        """Generate mock weather data for development/testing"""
        self.logger.info(f"Generating mock weather data for {location} on {date}")
        
        # Simple mock data based on location
        base_temp = 20.0
        if "arctic" in location.lower() or "alaska" in location.lower():
            base_temp = -5.0
        elif "desert" in location.lower() or "sahara" in location.lower():
            base_temp = 35.0
        elif "tropical" in location.lower() or "hawaii" in location.lower():
            base_temp = 28.0
        
        return WeatherInfo(
            date=date,
            temperature_high=base_temp + 5,
            temperature_low=base_temp - 5,
            description="Partly cloudy",
            humidity=60,
            wind_speed=15.0,
            precipitation_chance=30
        )
    
    def _generate_mock_forecast(self, location: str, days: int) -> List[WeatherInfo]:
        """Generate mock forecast data for development/testing"""
        self.logger.info(f"Generating mock {days}-day forecast for {location}")
        
        weather_list = []
        base_date = datetime.now()
        
        for i in range(days):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            weather = self._generate_mock_weather(location, date)
            
            # Add some variation to mock data
            weather.temperature_high += (i % 3) - 1
            weather.temperature_low += (i % 3) - 1
            weather.precipitation_chance = (i * 10) % 80
            
            descriptions = ["Sunny", "Partly cloudy", "Cloudy", "Light rain"]
            weather.description = descriptions[i % len(descriptions)]
            
            weather_list.append(weather)
        
        return weather_list