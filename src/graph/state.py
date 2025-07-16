"""
LangGraph state management for travel planning workflow
Defines the shared state structure for all agents
"""

from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import operator

from core.models import (
    TravelRequest, TravelItinerary, PlaceRecommendation, 
    WeatherInfo, DailyPlan, TaskStatus
)


class TravelPlanningState(TypedDict):
    """
    Shared state for the travel planning workflow
    This state is passed between all agents in the graph
    """
    
    # Original request
    travel_request: TravelRequest
    
    # Processing status
    current_step: str
    completed_steps: Annotated[List[str], operator.add]
    failed_steps: Annotated[List[str], operator.add]
    
    # Collected data from APIs
    hotels: Annotated[List[PlaceRecommendation], operator.add]
    restaurants: Annotated[List[PlaceRecommendation], operator.add]
    attractions: Annotated[List[PlaceRecommendation], operator.add]
    weather_forecast: List[WeatherInfo]
    
    # Agent outputs
    destination_analysis: Optional[Dict[str, Any]]
    local_insights: Optional[Dict[str, Any]]
    daily_itineraries: Annotated[List[DailyPlan], operator.add]
    
    # Final output
    final_itinerary: Optional[TravelItinerary]
    
    # Feedback and optimization
    critic_feedback: Annotated[List[Dict[str, Any]], operator.add]
    optimization_rounds: int
    
    # Metadata
    processing_start_time: datetime
    last_updated: datetime
    error_messages: Annotated[List[str], operator.add]


def create_initial_state(travel_request: TravelRequest) -> TravelPlanningState:
    """Create initial state from travel request"""
    return TravelPlanningState(
        travel_request=travel_request,
        current_step="planning",
        completed_steps=[],
        failed_steps=[],
        hotels=[],
        restaurants=[],
        attractions=[],
        weather_forecast=[],
        destination_analysis=None,
        local_insights=None,
        daily_itineraries=[],
        final_itinerary=None,
        critic_feedback=[],
        optimization_rounds=0,
        processing_start_time=datetime.utcnow(),
        last_updated=datetime.utcnow(),
        error_messages=[]
    )


def update_state_step(state: TravelPlanningState, step_name: str, 
                     success: bool = True, error_message: str = None) -> TravelPlanningState:
    """Update state with step completion"""
    state["current_step"] = step_name
    state["last_updated"] = datetime.utcnow()
    
    if success:
        if step_name not in state["completed_steps"]:
            state["completed_steps"].append(step_name)
    else:
        if step_name not in state["failed_steps"]:
            state["failed_steps"].append(step_name)
        if error_message:
            state["error_messages"].append(f"{step_name}: {error_message}")
    
    return state


def get_state_summary(state: TravelPlanningState) -> Dict[str, Any]:
    """Get summary of current state"""
    return {
        "destination": state["travel_request"].destination,
        "duration": getattr(state["travel_request"], 'duration', 0),
        "current_step": state["current_step"],
        "completed_steps": state["completed_steps"],
        "failed_steps": state["failed_steps"],
        "data_collected": {
            "hotels": len(state["hotels"]),
            "restaurants": len(state["restaurants"]),
            "attractions": len(state["attractions"]),
            "weather_days": len(state["weather_forecast"])
        },
        "has_final_itinerary": state["final_itinerary"] is not None,
        "optimization_rounds": state["optimization_rounds"],
        "processing_time": (
            state["last_updated"] - state["processing_start_time"]
        ).total_seconds(),
        "error_count": len(state["error_messages"])
    }


def is_state_ready_for_step(state: TravelPlanningState, step_name: str) -> bool:
    """Check if state has required data for a step"""
    requirements = {
        "data_collection": [],  # No prerequisites
        "destination_research": [],
        "local_expertise": ["data_collection"],
        "itinerary_creation": ["data_collection", "destination_research"],
        "trip_criticism": ["itinerary_creation"],
        "finalization": ["trip_criticism"]
    }
    
    required_steps = requirements.get(step_name, [])
    completed = state["completed_steps"]
    
    return all(req_step in completed for req_step in required_steps)


def has_sufficient_data(state: TravelPlanningState) -> bool:
    """Check if state has sufficient data for itinerary creation"""
    return (
        len(state["weather_forecast"]) > 0 and
        (len(state["hotels"]) > 0 or len(state["attractions"]) > 0)
    )


# State validation functions
def validate_state_data(state: TravelPlanningState) -> List[str]:
    """Validate state data and return list of issues"""
    issues = []
    
    # Check required fields
    if not state.get("travel_request"):
        issues.append("Missing travel request")
    
    # Check data consistency
    request = state.get("travel_request")
    if request:
        duration = getattr(request, 'duration', 0)
        if len(state["weather_forecast"]) > 0 and len(state["weather_forecast"]) < duration:
            issues.append(f"Insufficient weather data: {len(state['weather_forecast'])} days for {duration} day trip")
    
    # Check for errors
    if len(state["error_messages"]) > 5:
        issues.append("Too many errors encountered")
    
    return issues


class StateManager:
    """Helper class for managing state transitions"""
    
    def __init__(self):
        self.state_history: List[Dict[str, Any]] = []
    
    def snapshot_state(self, state: TravelPlanningState, step_name: str):
        """Take snapshot of state for debugging"""
        snapshot = {
            "timestamp": datetime.utcnow().isoformat(),
            "step": step_name,
            "summary": get_state_summary(state),
            "validation_issues": validate_state_data(state)
        }
        self.state_history.append(snapshot)
    
    def get_state_history(self) -> List[Dict[str, Any]]:
        """Get complete state history"""
        return self.state_history
    
    def clear_history(self):
        """Clear state history"""
        self.state_history.clear()