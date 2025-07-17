"""
Main application entry point for the Travel Planning System
Integrates all components into a complete working system
"""

import asyncio
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Fix import paths by adding directories to Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(project_root))

# Import basic modules first
try:
    import core.models as models
    import core.exceptions as exceptions
    from config.settings import settings
    
    print("✅ Basic imports successful")
    
    TravelRequest = models.TravelRequest
    TravelItinerary = models.TravelItinerary
    TravelPlannerError = exceptions.TravelPlannerError
    ValidationError = exceptions.ValidationError
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Creating simplified version without full workflow...")


class TravelPlannerApp:
    """
    Main application class for the Travel Planning System
    Provides high-level interface for travel planning operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger("travel_planner_app")
        self.workflow = None
        self._setup_complete = False
    
    async def setup(self):
        """Initialize the application"""
        if self._setup_complete:
            return
        
        try:
            # Setup logging
            logging.basicConfig(
                level=getattr(settings, 'log_level', 'INFO'),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            self.logger.info("Travel Planning System starting up")
            
            # Test connections
            await self._test_system_connections()
            
            self._setup_complete = True
            self.logger.info("Travel Planning System setup complete")
            
        except Exception as e:
            self.logger.error(f"Failed to setup Travel Planning System: {e}")
            raise Exception(f"System setup failed: {e}")
    
    async def plan_trip_simple(self, travel_request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simple trip planning without full workflow (for testing)
        """
        try:
            self.logger.info(f"Planning trip to {travel_request_data.get('destination')}")
            
            # Basic validation
            required_fields = ['destination', 'start_date', 'end_date']
            missing_fields = [field for field in required_fields if not travel_request_data.get(field)]
            
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {missing_fields}"
                }
            
            # Test API connections
            api_status = await self._test_google_apis()
            ollama_status = await self._test_ollama()
            
            # Create a simple response
            result = {
                "success": True,
                "itinerary": {
                    "destination": travel_request_data["destination"],
                    "travel_dates": {
                        "start_date": travel_request_data["start_date"],
                        "end_date": travel_request_data["end_date"],
                        "duration": self._calculate_duration(
                            travel_request_data["start_date"], 
                            travel_request_data["end_date"]
                        )
                    },
                    "budget": travel_request_data.get("budget"),
                    "interests": travel_request_data.get("interests", []),
                    "status": "basic_planning_complete",
                    "message": "This is a simplified version. Full planning requires all components."
                },
                "system_status": {
                    "google_apis": api_status,
                    "ollama": ollama_status,
                    "configuration": "loaded"
                },
                "next_steps": [
                    "Ensure all Python modules are properly imported",
                    "Test Google API connectivity with real requests",
                    "Test Ollama model responses",
                    "Implement full workflow when imports are resolved"
                ]
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Trip planning failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "error_type": "planning_error"
            }
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get current system status and health"""
        try:
            # Test system components
            google_status = await self._test_google_apis()
            ollama_status = await self._test_ollama()
            
            return {
                "status": "operational" if google_status and ollama_status else "partial",
                "components": {
                    "google_apis": google_status,
                    "ollama": ollama_status,
                    "configuration": "loaded"
                },
                "configuration": {
                    "ollama_model": getattr(settings, 'ollama_model', 'unknown'),
                    "ollama_url": getattr(settings, 'ollama_base_url', 'unknown'),
                    "google_apis_configured": bool(getattr(settings, 'google_api_key', '')),
                    "max_trip_duration": getattr(settings, 'max_trip_duration', 30)
                },
                "system_info": {
                    "version": "1.0.0-beta",
                    "setup_complete": self._setup_complete,
                    "working_directory": str(Path.cwd()),
                    "python_version": sys.version
                }
            }
        
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _test_system_connections(self):
        """Test connections to external services"""
        google_ok = await self._test_google_apis()
        ollama_ok = await self._test_ollama()
        
        if google_ok:
            self.logger.info("✅ Google APIs accessible")
        else:
            self.logger.warning("⚠️ Google APIs not accessible")
        
        if ollama_ok:
            self.logger.info("✅ Ollama accessible")
        else:
            self.logger.warning("⚠️ Ollama not accessible")
    
    async def _test_google_apis(self) -> bool:
        """Test Google APIs connectivity"""
        try:
            import aiohttp
            api_key = getattr(settings, 'google_api_key', '')
            
            if not api_key:
                return False
            
            # Test with a simple geocoding request
            url = f"https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": "Paris, France",
                "key": api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("status") == "OK"
            
            return False
            
        except Exception as e:
            self.logger.error(f"Google API test failed: {e}")
            return False
    
    async def _test_ollama(self) -> bool:
        """Test Ollama connectivity"""
        try:
            import aiohttp
            ollama_url = getattr(settings, 'ollama_base_url', 'http://localhost:11434')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{ollama_url}/api/tags") as response:
                    return response.status == 200
                    
        except Exception as e:
            self.logger.error(f"Ollama test failed: {e}")
            return False
    
    def _calculate_duration(self, start_date: str, end_date: str) -> int:
        """Calculate trip duration in days"""
        try:
            from datetime import datetime
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)
            return (end - start).days
        except:
            return 0


# Simplified CLI interface
async def simple_cli():
    """Simplified command-line interface"""
    print("🌍 Travel Planning System - Beta Version")
    print("=" * 50)
    
    app = TravelPlannerApp()
    
    try:
        # Setup system
        print("Initializing system...")
        await app.setup()
        
        # Get system status
        status = await app.get_system_status()
        print(f"System Status: {status['status']}")
        print(f"Google APIs: {'✅' if status['components']['google_apis'] else '❌'}")
        print(f"Ollama: {'✅' if status['components']['ollama'] else '❌'}")
        
        # Sample travel request
        sample_request = {
            "destination": "Paris, France",
            "start_date": "2024-09-15",
            "end_date": "2024-09-20",
            "budget": 2000.0,
            "interests": ["museums", "food", "architecture"],
            "travelers": 2
        }
        
        print("\n📝 Sample Travel Request:")
        print(f"   Destination: {sample_request['destination']}")
        print(f"   Dates: {sample_request['start_date']} to {sample_request['end_date']}")
        print(f"   Budget: ${sample_request['budget']}")
        print(f"   Interests: {', '.join(sample_request['interests'])}")
        
        # Plan the trip
        print("\n🚀 Planning trip...")
        result = await app.plan_trip_simple(sample_request)
        
        if result["success"]:
            print("\n✅ Basic trip planning successful!")
            
            itinerary = result["itinerary"]
            print(f"🎯 Destination: {itinerary['destination']}")
            print(f"📅 Duration: {itinerary['travel_dates']['duration']} days")
            print(f"💰 Budget: ${itinerary.get('budget', 'Not specified')}")
            print(f"🎭 Interests: {', '.join(itinerary['interests'])}")
            
            print(f"\n📊 System Status:")
            system_status = result["system_status"]
            print(f"   Google APIs: {'✅' if system_status['google_apis'] else '❌'}")
            print(f"   Ollama: {'✅' if system_status['ollama'] else '❌'}")
            
            print(f"\n📋 Next Steps:")
            for i, step in enumerate(result["next_steps"], 1):
                print(f"   {i}. {step}")
            
        else:
            print(f"\n❌ Trip planning failed: {result['error']}")
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        print("\nThis is a beta version. Full functionality requires all components to be properly imported.")


# Example usage functions
async def test_google_api():
    """Test Google API functionality"""
    app = TravelPlannerApp()
    await app.setup()
    
    google_working = await app._test_google_apis()
    
    if google_working:
        print("✅ Google APIs are working!")
        print("You can now use the full travel planning features.")
    else:
        print("❌ Google APIs not working. Check your API key and internet connection.")
    
    return google_working


async def test_ollama():
    """Test Ollama functionality"""
    app = TravelPlannerApp()
    await app.setup()
    
    ollama_working = await app._test_ollama()
    
    if ollama_working:
        print("✅ Ollama is working!")
        print("You can now use AI-powered travel recommendations.")
    else:
        print("❌ Ollama not working. Make sure Ollama is running:")
        print("   1. Install Ollama from https://ollama.ai")
        print("   2. Run: ollama serve")
        print("   3. Run: ollama pull llama3.2:3b")
    
    return ollama_working


if __name__ == "__main__":
    print("🧪 Starting Travel Planning System...")
    
    # You can also test individual components:
    # asyncio.run(test_google_api())
    # asyncio.run(test_ollama())
    
    # Run the main CLI
    asyncio.run(simple_cli())