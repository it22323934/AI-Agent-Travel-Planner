"""
Constants for the travel planning system
"""

# Ollama Configuration
OLLAMA_DEFAULT_CONFIG = {
    "base_url": "http://localhost:11434",
    "model": "llama3.2:3b",
    "temperature": 0.7,
    "max_tokens": 2048
}

# Google API Endpoints
GOOGLE_APIS = {
    "places_base": "https://maps.googleapis.com/maps/api/place",
    "geocoding": "https://maps.googleapis.com/maps/api/geocode/json",
    "weather": "https://weather.googleapis.com/v1"
}

# Agent Names
AGENT_NAMES = {
    "planner": "PlannerAgent",
    "destination_finder": "DestinationFinder", 
    "local_expert": "LocalExpert",
    "itinerary_expert": "ItineraryExpert",
    "trip_critic": "TripCritic"
}

# Place Type Mappings
INTEREST_TO_PLACE_TYPES = {
    "museums": ["museum", "art_gallery"],
    "food": ["restaurant", "cafe"],
    "nature": ["park", "zoo"],
    "history": ["museum", "landmark"],
    "shopping": ["shopping_mall", "store"],
    "entertainment": ["amusement_park", "movie_theater"]
}

# Default Search Parameters
DEFAULT_SEARCH_RADIUS = 5000  # meters
MAX_PLACES_PER_TYPE = 10
DEFAULT_TRIP_DURATION_LIMIT = 14  # days

# Budget Categories (USD per day)
BUDGET_RANGES = {
    "budget": (50, 100),
    "mid_range": (100, 200), 
    "luxury": (200, 500)
}

# Activity Durations (minutes)
ACTIVITY_DURATIONS = {
    "museum": 120,
    "restaurant": 90,
    "park": 90,
    "shopping": 120,
    "sightseeing": 60
}