"""
Core data models for the travel planning system
Updated for Pydantic v2 compatibility with comprehensive activity support
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime, date, timedelta, time
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
    SHOPPING_MALL = "shopping_mall"
    ENTERTAINMENT = "entertainment"
    CHURCH = "church"
    HISTORICAL_SITE = "historical_site"


class ActivityType(str, Enum):
    """Types of activities"""
    SIGHTSEEING = "sightseeing"
    DINING = "dining"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    CULTURAL = "cultural"
    OUTDOOR = "outdoor"
    RELAXATION = "relaxation"
    TRANSPORTATION = "transportation"
    ACCOMMODATION = "accommodation"
    NIGHTLIFE = "nightlife"
    ADVENTURE = "adventure"
    EDUCATIONAL = "educational"


class ActivityPriority(str, Enum):
    """Activity priority levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


class TravelStyle(str, Enum):
    """Travel style preferences"""
    BUDGET = "budget"
    LUXURY = "luxury"
    ADVENTURE = "adventure"
    CULTURAL = "cultural"
    RELAXATION = "relaxation"
    FAMILY = "family"
    BUSINESS = "business"


# Input Model
class TravelRequest(BaseModel):
    """User travel request"""
    destination: str = Field(..., min_length=1)
    start_date: str = Field(..., description="YYYY-MM-DD format")
    end_date: str = Field(..., description="YYYY-MM-DD format")
    budget: Optional[float] = Field(None, ge=0)
    interests: List[str] = Field(default_factory=list)
    travelers: int = Field(default=1, ge=1, le=20)
    travel_style: TravelStyle = Field(default=TravelStyle.CULTURAL)
    constraints: List[str] = Field(default_factory=list)
    preferred_activities: List[ActivityType] = Field(default_factory=list)
    
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


# Activity Model
class Activity(BaseModel):
    """Individual activity in the itinerary"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(..., min_length=1)
    description: str = Field(default="")
    activity_type: ActivityType = Field(default=ActivityType.SIGHTSEEING)
    priority: ActivityPriority = Field(default=ActivityPriority.MEDIUM)
    
    # Timing
    start_time: str = Field(..., description="HH:MM format")
    duration_minutes: int = Field(default=120, ge=15, le=480)  # 15 minutes to 8 hours
    
    # Location
    location: Optional[str] = Field(None)
    place_id: Optional[str] = Field(None)
    coordinates: Optional[Dict[str, float]] = Field(None)  # {"lat": x, "lng": y}
    
    # Details
    estimated_cost: Optional[float] = Field(None, ge=0)
    booking_required: bool = Field(default=False)
    booking_url: Optional[str] = Field(None)
    contact_info: Optional[str] = Field(None)
    
    # Ratings and reviews
    rating: Optional[float] = Field(None, ge=0, le=5)
    review_count: Optional[int] = Field(None, ge=0)
    
    # Weather dependency
    weather_dependent: bool = Field(default=False)
    indoor_activity: bool = Field(default=False)
    
    # Transportation
    transportation_to: Optional[str] = Field(None)
    transportation_time: Optional[int] = Field(None)  # minutes
    
    # Notes and tips
    notes: List[str] = Field(default_factory=list)
    tips: List[str] = Field(default_factory=list)
    
    @property
    def end_time(self) -> str:
        """Calculate end time based on start time and duration"""
        try:
            start = datetime.strptime(self.start_time, "%H:%M")
            end = start + timedelta(minutes=self.duration_minutes)
            return end.strftime("%H:%M")
        except ValueError:
            return "Unknown"
    
    @field_validator('start_time')
    @classmethod
    def validate_time_format(cls, v):
        try:
            datetime.strptime(v, "%H:%M")
            return v
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert activity to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.activity_type.value,
            "priority": self.priority.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
            "location": self.location,
            "estimated_cost": self.estimated_cost,
            "booking_required": self.booking_required,
            "rating": self.rating,
            "weather_dependent": self.weather_dependent,
            "indoor_activity": self.indoor_activity,
            "notes": self.notes,
            "tips": self.tips
        }


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
    opening_hours: Optional[Dict[str, str]] = Field(default_factory=dict)
    reviews: Optional[List[str]] = Field(default_factory=list)
    photos: Optional[List[str]] = Field(default_factory=list)
    
    def to_activity(self, start_time: str = "09:00", duration: int = 120) -> Activity:
        """Convert place recommendation to activity"""
        activity_type = ActivityType.SIGHTSEEING
        
        # Map place types to activity types
        type_mapping = {
            "restaurant": ActivityType.DINING,
            "shopping_mall": ActivityType.SHOPPING,
            "museum": ActivityType.CULTURAL,
            "park": ActivityType.OUTDOOR,
            "entertainment": ActivityType.ENTERTAINMENT,
            "church": ActivityType.CULTURAL,
            "historical_site": ActivityType.CULTURAL
        }
        
        activity_type = type_mapping.get(self.place_type, ActivityType.SIGHTSEEING)
        
        return Activity(
            name=self.name,
            description=f"Visit {self.name}",
            activity_type=activity_type,
            start_time=start_time,
            duration_minutes=duration,
            location=self.address,
            place_id=self.place_id,
            rating=self.rating,
            contact_info=self.phone_number,
            booking_url=self.website,
            indoor_activity=self.place_type in ["museum", "shopping_mall", "restaurant"]
        )


class WeatherInfo(BaseModel):
    """Weather data from Google Weather API"""
    date: str
    temperature_high: float
    temperature_low: float
    description: str
    humidity: int = Field(ge=0, le=100)
    wind_speed: float = Field(ge=0)
    precipitation_chance: int = Field(default=0, ge=0, le=100)
    
    @property
    def is_good_weather(self) -> bool:
        """Determine if weather is good for outdoor activities"""
        return (self.precipitation_chance < 30 and 
                self.temperature_high > 10 and 
                self.wind_speed < 20)


# Planning Models
class DailyPlan(BaseModel):
    """Single day itinerary with activities"""
    date: str
    weather: Optional[WeatherInfo] = None
    activities: List[Activity] = Field(default_factory=list)
    
    # Deprecated fields (kept for backward compatibility)
    morning_activities: List[str] = Field(default_factory=list)
    afternoon_activities: List[str] = Field(default_factory=list)
    evening_activities: List[str] = Field(default_factory=list)
    recommended_restaurants: List[PlaceRecommendation] = Field(default_factory=list)
    
    @property
    def total_estimated_cost(self) -> float:
        """Calculate total estimated cost for the day"""
        return sum(activity.estimated_cost or 0 for activity in self.activities)
    
    @property
    def activity_count(self) -> int:
        """Get number of activities for the day"""
        return len(self.activities)
    
    def get_activities_by_type(self, activity_type: ActivityType) -> List[Activity]:
        """Get activities of a specific type"""
        return [activity for activity in self.activities if activity.activity_type == activity_type]
    
    def get_activities_by_time_period(self, start_hour: int, end_hour: int) -> List[Activity]:
        """Get activities within a specific time period"""
        activities = []
        for activity in self.activities:
            try:
                activity_hour = int(activity.start_time.split(':')[0])
                if start_hour <= activity_hour < end_hour:
                    activities.append(activity)
            except (ValueError, IndexError):
                continue
        return activities
    
    def add_activity(self, activity: Activity) -> None:
        """Add an activity to the day, maintaining time order"""
        self.activities.append(activity)
        # Sort activities by start time
        self.activities.sort(key=lambda x: x.start_time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert daily plan to dictionary"""
        return {
            "date": self.date,
            "weather": {
                "temperature_high": self.weather.temperature_high,
                "temperature_low": self.weather.temperature_low,
                "description": self.weather.description,
                "precipitation_chance": self.weather.precipitation_chance
            } if self.weather else None,
            "activities": [activity.to_dict() for activity in self.activities],
            "total_estimated_cost": self.total_estimated_cost,
            "activity_count": self.activity_count
        }


# Output Model
class TravelItinerary(BaseModel):
    """Complete travel itinerary with enhanced activity support"""
    destination: str
    start_date: str
    end_date: str
    duration: int
    weather_forecast: List[WeatherInfo] = Field(default_factory=list)
    hotels: List[PlaceRecommendation] = Field(default_factory=list)
    attractions: List[PlaceRecommendation] = Field(default_factory=list)
    restaurants: List[PlaceRecommendation] = Field(default_factory=list)
    daily_plans: List[DailyPlan] = Field(default_factory=list)
    
    # Enhanced fields
    total_budget: Optional[float] = None
    total_estimated_cost: Optional[float] = None
    transportation_info: Dict[str, Any] = Field(default_factory=dict)
    packing_suggestions: List[str] = Field(default_factory=list)
    important_notes: List[str] = Field(default_factory=list)
    
    # Activity statistics
    activity_summary: Dict[str, int] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def total_activities(self) -> int:
        """Get total number of activities across all days"""
        return sum(len(day.activities) for day in self.daily_plans)
    
    @property
    def activities_by_type(self) -> Dict[str, int]:
        """Get activity count by type"""
        type_counts = {}
        for day in self.daily_plans:
            for activity in day.activities:
                activity_type = activity.activity_type.value
                type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
        return type_counts
    
    def get_all_activities(self) -> List[Activity]:
        """Get all activities from all days"""
        all_activities = []
        for day in self.daily_plans:
            all_activities.extend(day.activities)
        return all_activities
    
    def calculate_total_cost(self) -> float:
        """Calculate total estimated cost for the entire trip"""
        total = 0
        for day in self.daily_plans:
            total += day.total_estimated_cost
        return total
    
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
            'daily_plans': [day.to_dict() for day in self.daily_plans],
            'total_budget': self.total_budget,
            'total_estimated_cost': self.calculate_total_cost(),
            'total_activities': self.total_activities,
            'activities_by_type': self.activities_by_type,
            'transportation_info': self.transportation_info,
            'packing_suggestions': self.packing_suggestions,
            'important_notes': self.important_notes,
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