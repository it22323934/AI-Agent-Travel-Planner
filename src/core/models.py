"""
Core data models for the travel planning system
Updated for Pydantic v2 compatibility
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date, timedelta
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    """Agent task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PlaceType(str, Enum):
    """Google Places API types"""
    LODGING = "lodging"
    TOURIST_ATTRACTION = "tourist_attraction"
    RESTAURANT = "restaurant"
    MUSEUM = "museum"
    PARK = "park"


# Input Model
class TravelRequest(BaseModel):
    """User travel request"""
    destination: str = Field(..., min_length=1)
    start_date: str = Field(..., description="YYYY-MM-DD format")
    end_date: str = Field(..., description="YYYY-MM-DD format")
    budget: Optional[float] = Field(None, ge=0)
    interests: List[str] = Field(default_factory=list)
    travelers: int = Field(default=1, ge=1, le=20)
    
    # Add duration property
    @property
    def duration(self) -> int:
        """Calculate trip duration in days"""
        try:
            start = datetime.fromisoformat(self.start_date)
            end = datetime.fromisoformat(self.end_date)
            return (end - start).days
        except:
            return 0
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.fromisoformat(v)
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
    
    @model_validator(mode='after')
    def validate_date_logic(self):
        """Validate that start_date is before end_date"""
        try:
            start_date = datetime.fromisoformat(self.start_date)
            end_date = datetime.fromisoformat(self.end_date)
            
            if start_date >= end_date:
                raise ValueError("Start date must be before end date")
            
            duration = (end_date - start_date).days
            if duration > 30:
                raise ValueError("Trip duration cannot exceed 30 days")
                
        except ValueError as e:
            raise ValueError(f"Date validation error: {e}")
        
        return self


# Google API Models
class PlaceRecommendation(BaseModel):
    """Place from Google Places API"""
    place_id: str
    name: str
    rating: float = Field(default=0.0, ge=0, le=5)
    price_level: int = Field(default=0, ge=0, le=4)
    place_type: str
    address: str = ""
    phone_number: Optional[str] = None
    website: Optional[str] = None


class WeatherInfo(BaseModel):
    """Weather data from Google Weather API"""
    date: str
    temperature_high: float
    temperature_low: float
    description: str
    humidity: int = Field(ge=0, le=100)
    wind_speed: float = Field(ge=0)
    precipitation_chance: int = Field(default=0, ge=0, le=100)


# Planning Models
class DailyPlan(BaseModel):
    """Single day itinerary"""
    date: str
    weather: WeatherInfo
    morning_activities: List[str] = Field(default_factory=list)
    afternoon_activities: List[str] = Field(default_factory=list)
    evening_activities: List[str] = Field(default_factory=list)
    recommended_restaurants: List[PlaceRecommendation] = Field(default_factory=list)


# Output Model
class TravelItinerary(BaseModel):
    """Complete travel itinerary"""
    destination: str
    start_date: str
    end_date: str
    duration: int
    weather_forecast: List[WeatherInfo]
    hotels: List[PlaceRecommendation] = Field(default_factory=list)
    attractions: List[PlaceRecommendation] = Field(default_factory=list)
    restaurants: List[PlaceRecommendation] = Field(default_factory=list)
    daily_plans: List[DailyPlan] = Field(default_factory=list)
    total_estimated_cost: Optional[float] = None
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'destination': self.destination,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'duration': self.duration,
            'weather_forecast': [
                {
                    'date': w.date,
                    'temperature_high': w.temperature_high,
                    'temperature_low': w.temperature_low,
                    'description': w.description,
                    'humidity': w.humidity,
                    'wind_speed': w.wind_speed,
                    'precipitation_chance': w.precipitation_chance
                } for w in self.weather_forecast
            ],
            'hotels': [
                {
                    'place_id': h.place_id,
                    'name': h.name,
                    'rating': h.rating,
                    'price_level': h.price_level,
                    'place_type': h.place_type,
                    'address': h.address
                } for h in self.hotels
            ],
            'attractions': [
                {
                    'place_id': a.place_id,
                    'name': a.name,
                    'rating': a.rating,
                    'price_level': a.price_level,
                    'place_type': a.place_type,
                    'address': a.address
                } for a in self.attractions
            ],
            'restaurants': [
                {
                    'place_id': r.place_id,
                    'name': r.name,
                    'rating': r.rating,
                    'price_level': r.price_level,
                    'place_type': r.place_type,
                    'address': r.address
                } for r in self.restaurants
            ],
            'daily_plans': [
                {
                    'date': plan.date,
                    'weather': {
                        'temperature_high': plan.weather.temperature_high,
                        'temperature_low': plan.weather.temperature_low,
                        'description': plan.weather.description
                    },
                    'morning_activities': plan.morning_activities,
                    'afternoon_activities': plan.afternoon_activities,
                    'evening_activities': plan.evening_activities,
                    'recommended_restaurants': [
                        {'name': r.name, 'rating': r.rating} 
                        for r in plan.recommended_restaurants
                    ]
                } for plan in self.daily_plans
            ],
            'total_estimated_cost': self.total_estimated_cost,
            'recommendations': self.recommendations,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Agent Communication
class AgentMessage(BaseModel):
    """Message between agents"""
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Configuration
class OllamaConfig(BaseModel):
    """Ollama configuration for local LLM"""
    base_url: str = "http://localhost:11434"
    model: str = "llama3.2:3b"
    temperature: float = 0.7
    max_tokens: int = 2048


class GoogleAPIConfig(BaseModel):
    """Google APIs configuration"""
    api_key: str
    timeout: int = 30
    max_retries: int = 3