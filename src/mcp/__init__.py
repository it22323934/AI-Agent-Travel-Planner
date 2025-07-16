"""
MCP (Model Context Protocol) connector manager
Fixed imports for direct execution
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional

# Fixed imports - remove relative imports
try:
    from mcp.google_places import GooglePlacesConnector
    from mcp.google_weather import GoogleWeatherConnector
except ImportError:
    try:
        from .google_places import GooglePlacesConnector
        from .google_weather import GoogleWeatherConnector
    except ImportError:
        print("⚠️ Could not import Google connectors - checking individual files...")
        GooglePlacesConnector = None
        GoogleWeatherConnector = None

try:
    from core.models import PlaceRecommendation, WeatherInfo, PlaceType
    from core.exceptions import MCPError
    from config.settings import get_google_api_key
except ImportError as e:
    print(f"⚠️ Import error in MCP: {e}")
    # Create fallback classes
    class PlaceRecommendation:
        pass
    class WeatherInfo:
        pass
    class PlaceType:
        LODGING = "lodging"
        RESTAURANT = "restaurant"
        TOURIST_ATTRACTION = "tourist_attraction"
    class MCPError(Exception):
        pass
    def get_google_api_key(service="default"):
        import os
        return os.getenv("GOOGLE_API_KEY", "")


class MCPManager:
    """
    Central manager for all MCP connectors
    Provides unified interface to Google APIs
    """
    
    def __init__(self):
        self.logger = logging.getLogger("mcp_manager")
        self.places_connector: Optional[GooglePlacesConnector] = None
        self.weather_connector: Optional[GoogleWeatherConnector] = None
        self._initialized = False
    
    async def __aenter__(self):
        """Initialize all connectors"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up all connectors"""
        await self.cleanup()
    
    async def initialize(self):
        """Initialize all connectors"""
        if self._initialized:
            return
        
        try:
            if GooglePlacesConnector is None or GoogleWeatherConnector is None:
                raise MCPError("Google connector classes not available")
            
            # Initialize Places API connector
            places_api_key = get_google_api_key("places")
            self.places_connector = GooglePlacesConnector(places_api_key)
            
            # Initialize Weather API connector
            weather_api_key = get_google_api_key("weather")
            self.weather_connector = GoogleWeatherConnector(weather_api_key)
            
            self.logger.info("MCP connectors initialized successfully")
            self._initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize MCP connectors: {e}")
            # Don't raise error, just log it
            self._initialized = False
    
    async def cleanup(self):
        """Clean up all connectors"""
        if self.places_connector:
            try:
                await self.places_connector.__aexit__(None, None, None)
            except:
                pass
        
        if self.weather_connector:
            try:
                await self.weather_connector.__aexit__(None, None, None)
            except:
                pass
        
        self._initialized = False
        self.logger.info("MCP connectors cleaned up")
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connectivity to all Google APIs"""
        if not self._initialized:
            await self.initialize()
        
        results = {"places": False, "weather": False}
        
        if not self._initialized:
            return results
        
        # Test Places API
        try:
            if self.places_connector:
                async with self.places_connector:
                    results["places"] = await self.places_connector.test_connection()
        except Exception as e:
            self.logger.error(f"Places API test failed: {e}")
            results["places"] = False
        
        # Test Weather API  
        try:
            if self.weather_connector:
                async with self.weather_connector:
                    results["weather"] = await self.weather_connector.test_connection()
        except Exception as e:
            self.logger.error(f"Weather API test failed: {e}")
            results["weather"] = False
        
        return results
    
    # Simplified methods for basic functionality
    async def collect_all_data(self, location: str, interests: List[str], 
                             start_date: str, end_date: str) -> Dict[str, Any]:
        """Collect all travel data - simplified version"""
        
        if not self._initialized:
            await self.initialize()
        
        # If initialization failed, return mock data
        if not self._initialized:
            return {
                "hotels": [],
                "restaurants": [],
                "attractions": [],
                "weather": [],
                "note": "Using fallback - MCP connectors not available"
            }
        
        self.logger.info(f"Collecting travel data for {location}")
        
        try:
            # Create simplified data collection
            data = {
                "hotels": [],
                "restaurants": [], 
                "attractions": [],
                "weather": [],
                "interest_places": []
            }
            
            # Try to collect data if connectors are available
            if self.places_connector:
                try:
                    async with self.places_connector:
                        data["hotels"] = await self.places_connector.search_hotels(location)
                        data["restaurants"] = await self.places_connector.search_restaurants(location)
                        data["attractions"] = await self.places_connector.search_attractions(location)
                except Exception as e:
                    self.logger.error(f"Places data collection failed: {e}")
            
            if self.weather_connector:
                try:
                    async with self.weather_connector:
                        data["weather"] = await self.weather_connector.get_weather_for_dates(location, start_date, end_date)
                except Exception as e:
                    self.logger.error(f"Weather data collection failed: {e}")
            
            self.logger.info("Travel data collection completed")
            return data
            
        except Exception as e:
            self.logger.error(f"Error collecting travel data: {e}")
            return {
                "hotels": [],
                "restaurants": [],
                "attractions": [],
                "weather": [],
                "error": str(e)
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics from all connectors"""
        return {
            "initialized": self._initialized,
            "places_connector": self.places_connector is not None,
            "weather_connector": self.weather_connector is not None,
            "status": "operational" if self._initialized else "limited"
        }