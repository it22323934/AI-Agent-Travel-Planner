"""
Google Places API MCP connector
Handles hotel, restaurant, and attraction recommendations
"""

from typing import List, Dict, Any, Optional, Tuple
import logging

from mcp.base_connector import BaseMCPConnector
from core.models import PlaceRecommendation, PlaceType
from core.exceptions import GoogleAPIError
from core.constants import GOOGLE_APIS, DEFAULT_SEARCH_RADIUS, MAX_PLACES_PER_TYPE


class GooglePlacesConnector(BaseMCPConnector):
    """MCP connector for Google Places API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "google_places")
        self.base_url = GOOGLE_APIS["places_base"]
    
    async def test_connection(self) -> bool:
        """Test Places API connectivity"""
        try:
            # Test with a simple place details request for a known place
            url = f"{self.base_url}/details/json"
            params = {"place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4"}  # Google Sydney office
            
            result = await self._make_request("GET", url, params)
            return result.get("status") == "OK"
            
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False
    
    async def geocode_location(self, address: str) -> Tuple[float, float]:
        """Get coordinates for a location using Geocoding API"""
        url = GOOGLE_APIS["geocoding"]
        params = {"address": address}
        
        self.logger.info(f"Geocoding location: {address}")
        
        try:
            result = await self._make_request("GET", url, params)
            
            if result.get("status") != "OK" or not result.get("results"):
                raise GoogleAPIError(f"Geocoding failed for: {address}", "geocoding")
            
            location = result["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
            
        except Exception as e:
            self.logger.error(f"Geocoding error for {address}: {e}")
            raise GoogleAPIError(f"Failed to geocode {address}: {e}", "geocoding")
    
    async def search_nearby_places(self, location: str, place_type: PlaceType, 
                                 radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search for nearby places of a specific type"""
        try:
            # Get coordinates first
            lat, lng = await self.geocode_location(location)
            
            # Search for places
            url = f"{self.base_url}/nearbysearch/json"
            params = {
                "location": f"{lat},{lng}",
                "radius": radius,
                "type": place_type.value
            }
            
            self.logger.info(f"Searching for {place_type.value} near {location}")
            
            result = await self._make_request("GET", url, params)
            
            if result.get("status") != "OK":
                self.logger.warning(f"Places search returned status: {result.get('status')}")
                return []
            
            places = []
            results = result.get("results", [])[:MAX_PLACES_PER_TYPE]
            
            for place_data in results:
                try:
                    place = self._parse_place_data(place_data, place_type.value)
                    places.append(place)
                except Exception as e:
                    self.logger.warning(f"Error parsing place data: {e}")
                    continue
            
            self.logger.info(f"Found {len(places)} {place_type.value} places")
            return places
            
        except Exception as e:
            self.logger.error(f"Error searching places: {e}")
            return []
    
    async def get_place_details(self, place_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific place"""
        url = f"{self.base_url}/details/json"
        params = {
            "place_id": place_id,
            "fields": "name,rating,price_level,formatted_phone_number,website,opening_hours"
        }
        
        try:
            result = await self._make_request("GET", url, params)
            
            if result.get("status") != "OK":
                self.logger.warning(f"Place details returned status: {result.get('status')}")
                return None
            
            return result.get("result", {})
            
        except Exception as e:
            self.logger.error(f"Error getting place details: {e}")
            return None
    
    async def search_hotels(self, location: str, radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search for hotels in a location"""
        return await self.search_nearby_places(location, PlaceType.LODGING, radius)
    
    async def search_restaurants(self, location: str, radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search for restaurants in a location"""
        return await self.search_nearby_places(location, PlaceType.RESTAURANT, radius)
    
    async def search_attractions(self, location: str, radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search for tourist attractions in a location"""
        return await self.search_nearby_places(location, PlaceType.TOURIST_ATTRACTION, radius)
    
    async def search_museums(self, location: str, radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search for museums in a location"""
        return await self.search_nearby_places(location, PlaceType.MUSEUM, radius)
    
    async def search_parks(self, location: str, radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search for parks in a location"""
        return await self.search_nearby_places(location, PlaceType.PARK, radius)
    
    def _parse_place_data(self, place_data: Dict[str, Any], place_type: str) -> PlaceRecommendation:
        """Parse Google Places API response into PlaceRecommendation model"""
        return PlaceRecommendation(
            place_id=place_data.get("place_id", ""),
            name=place_data.get("name", "Unknown"),
            rating=place_data.get("rating", 0.0),
            price_level=place_data.get("price_level", 0),
            place_type=place_type,
            address=place_data.get("vicinity", ""),
            phone_number=place_data.get("formatted_phone_number"),
            website=place_data.get("website")
        )
    
    async def search_by_interest(self, location: str, interest: str, 
                               radius: int = DEFAULT_SEARCH_RADIUS) -> List[PlaceRecommendation]:
        """Search places based on user interests"""
        from core.constants import INTEREST_TO_PLACE_TYPES
        
        place_types = INTEREST_TO_PLACE_TYPES.get(interest.lower(), ["tourist_attraction"])
        all_places = []
        
        for place_type in place_types:
            try:
                # Convert string to PlaceType enum
                if hasattr(PlaceType, place_type.upper()):
                    enum_type = getattr(PlaceType, place_type.upper())
                    places = await self.search_nearby_places(location, enum_type, radius)
                    all_places.extend(places)
            except Exception as e:
                self.logger.warning(f"Error searching for {place_type}: {e}")
                continue
        
        # Remove duplicates based on place_id
        unique_places = []
        seen_ids = set()
        for place in all_places:
            if place.place_id not in seen_ids:
                unique_places.append(place)
                seen_ids.add(place.place_id)
        
        return unique_places[:MAX_PLACES_PER_TYPE]