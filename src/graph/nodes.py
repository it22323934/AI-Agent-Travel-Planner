"""
Node implementations for the travel planning workflow
Enhanced with comprehensive activity management
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

from graph.state import TravelPlanningState, update_state_step
from core.models import (
    TravelItinerary, DailyPlan, Activity, WeatherInfo, PlaceRecommendation,
    ActivityType, ActivityPriority, TravelStyle
)
from core.exceptions import AgentError

logger = logging.getLogger("graph.nodes")


class ActivityGenerator:
    """Helper class for generating activities"""
    
    # Activity templates by type
    ACTIVITY_TEMPLATES = {
        ActivityType.SIGHTSEEING: {
            "duration_range": (90, 180),
            "cost_range": (10, 50),
            "weather_dependent": True,
            "indoor": False,
            "booking_required": False
        },
        ActivityType.DINING: {
            "duration_range": (60, 120),
            "cost_range": (15, 100),
            "weather_dependent": False,
            "indoor": True,
            "booking_required": True
        },
        ActivityType.CULTURAL: {
            "duration_range": (120, 240),
            "cost_range": (5, 30),
            "weather_dependent": False,
            "indoor": True,
            "booking_required": False
        },
        ActivityType.OUTDOOR: {
            "duration_range": (120, 300),
            "cost_range": (0, 40),
            "weather_dependent": True,
            "indoor": False,
            "booking_required": False
        },
        ActivityType.SHOPPING: {
            "duration_range": (90, 180),
            "cost_range": (20, 200),
            "weather_dependent": False,
            "indoor": True,
            "booking_required": False
        },
        ActivityType.ENTERTAINMENT: {
            "duration_range": (120, 240),
            "cost_range": (25, 80),
            "weather_dependent": False,
            "indoor": True,
            "booking_required": True
        }
    }
    
    @classmethod
    def create_activity_from_place(cls, place: PlaceRecommendation, 
                                 start_time: str = "09:00",
                                 travel_style: TravelStyle = TravelStyle.CULTURAL) -> Activity:
        """Create an activity from a place recommendation"""
        # Map place types to activity types
        place_to_activity_map = {
            "restaurant": ActivityType.DINING,
            "tourist_attraction": ActivityType.SIGHTSEEING,
            "museum": ActivityType.CULTURAL,
            "park": ActivityType.OUTDOOR,
            "shopping_mall": ActivityType.SHOPPING,
            "entertainment": ActivityType.ENTERTAINMENT
        }
        
        activity_type = place_to_activity_map.get(place.place_type, ActivityType.SIGHTSEEING)
        template = cls.ACTIVITY_TEMPLATES.get(activity_type, cls.ACTIVITY_TEMPLATES[ActivityType.SIGHTSEEING])
        
        # Adjust duration and cost based on travel style
        duration_multiplier = {
            TravelStyle.LUXURY: 1.3,
            TravelStyle.BUDGET: 0.8,
            TravelStyle.ADVENTURE: 1.2,
            TravelStyle.FAMILY: 1.1,
            TravelStyle.BUSINESS: 0.9
        }.get(travel_style, 1.0)
        
        duration = int(random.randint(*template["duration_range"]) * duration_multiplier)
        cost = random.randint(*template["cost_range"])
        
        # Adjust cost based on price level and travel style
        if place.price_level > 0:
            cost *= (place.price_level * 0.5 + 0.5)
        
        if travel_style == TravelStyle.LUXURY:
            cost *= 1.5
        elif travel_style == TravelStyle.BUDGET:
            cost *= 0.6
        
        # Determine priority based on rating
        if place.rating >= 4.5:
            priority = ActivityPriority.HIGH
        elif place.rating >= 3.5:
            priority = ActivityPriority.MEDIUM
        else:
            priority = ActivityPriority.LOW
        
        return Activity(
            name=place.name,
            description=f"Visit {place.name}" + (f" - {place.address}" if place.address else ""),
            activity_type=activity_type,
            priority=priority,
            start_time=start_time,
            duration_minutes=duration,
            location=place.address,
            place_id=place.place_id,
            estimated_cost=cost,
            booking_required=template["booking_required"],
            booking_url=place.website,
            contact_info=place.phone_number,
            rating=place.rating,
            weather_dependent=template["weather_dependent"],
            indoor_activity=template["indoor"],
            tips=[f"Rated {place.rating}/5.0" if place.rating > 0 else "No rating available"]
        )
    
    @classmethod
    def create_meal_activity(cls, meal_type: str, time: str, 
                           restaurants: List[PlaceRecommendation],
                           travel_style: TravelStyle = TravelStyle.CULTURAL) -> Optional[Activity]:
        """Create a meal activity"""
        if not restaurants:
            return None
        
        # Select restaurant based on meal type and travel style
        restaurant = random.choice(restaurants)
        
        durations = {
            "breakfast": 45,
            "lunch": 75,
            "dinner": 90,
            "snack": 30
        }
        
        activity = cls.create_activity_from_place(restaurant, time, travel_style)
        activity.duration_minutes = durations.get(meal_type, 60)
        activity.description = f"{meal_type.capitalize()} at {restaurant.name}"
        activity.activity_type = ActivityType.DINING
        
        return activity
    
    @classmethod
    def create_transportation_activity(cls, from_location: str, to_location: str,
                                     start_time: str, duration: int = 30) -> Activity:
        """Create a transportation activity"""
        return Activity(
            name=f"Travel from {from_location} to {to_location}",
            description=f"Transportation between locations",
            activity_type=ActivityType.TRANSPORTATION,
            priority=ActivityPriority.HIGH,
            start_time=start_time,
            duration_minutes=duration,
            location=f"{from_location} to {to_location}",
            estimated_cost=10.0,  # Average transport cost
            booking_required=False,
            indoor_activity=False,
            weather_dependent=False,
            tips=["Use public transport or ride-sharing", "Allow extra time for delays"]
        )


async def planning_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Initial planning node - sets up the travel planning process
    """
    logger.info("Executing planning node")
    
    try:
        # Extract travel request
        travel_request = state["travel_request"]
        
        # Initialize planning context
        state["planning_context"] = {
            "destination": travel_request.destination,
            "duration": travel_request.duration,
            "budget": travel_request.budget,
            "interests": travel_request.interests,
            "constraints": getattr(travel_request, 'constraints', []),
            "travel_style": getattr(travel_request, 'travel_style', TravelStyle.CULTURAL),
            "preferred_activities": getattr(travel_request, 'preferred_activities', []),
            "planning_started_at": datetime.now().isoformat()
        }
        
        # Mark step as completed
        state["completed_steps"].append("planning")
        
        logger.info(f"Planning initialized for {travel_request.destination}")
        return state
        
    except Exception as e:
        logger.error(f"Planning node failed: {e}")
        state["error_messages"].append(f"Planning failed: {str(e)}")
        state["failed_steps"].append("planning")
        return state


async def data_collection_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Collect data from Google APIs using MCP
    """
    logger.info("Executing data collection node")
    
    try:
        travel_request = state["travel_request"]
        
        # Try to import MCP Manager
        try:
            from mcp import MCPManager
            
            async with MCPManager() as mcp:
                # Test connections
                status = await mcp.test_all_connections()
                logger.info(f"MCP connection status: {status}")
                
                # Collect all data
                data = await mcp.collect_all_data(
                    location=travel_request.destination,
                    interests=travel_request.interests,
                    start_date=travel_request.start_date,
                    end_date=travel_request.end_date
                )
                
                # Store collected data in state
                state["hotels"] = data.get("hotels", [])
                state["restaurants"] = data.get("restaurants", [])
                state["attractions"] = data.get("attractions", [])
                state["weather_forecast"] = data.get("weather", [])
                
        except ImportError:
            logger.warning("MCP Manager not available, using mock data")
            # Generate mock data for testing
            state["hotels"] = _generate_mock_hotels(travel_request.destination)
            state["restaurants"] = _generate_mock_restaurants(travel_request.destination)
            state["attractions"] = _generate_mock_attractions(travel_request.destination)
            state["weather_forecast"] = _generate_mock_weather(travel_request.duration)
        
        # Update data quality
        state["data_quality"]["completeness"] = _calculate_data_completeness(state)
        state["data_quality"]["freshness"] = datetime.now().isoformat()
        
        state["completed_steps"].append("data_collection")
        logger.info(f"Data collection completed: {len(state['hotels'])} hotels, "
                   f"{len(state['restaurants'])} restaurants, "
                   f"{len(state['attractions'])} attractions")
        
    except Exception as e:
        logger.error(f"Data collection failed: {e}")
        state["error_messages"].append(f"Data collection failed: {str(e)}")
        state["failed_steps"].append("data_collection")
    
    return state


async def destination_research_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Research destination using LLM analysis
    """
    logger.info("Executing destination research node")
    
    try:
        travel_request = state["travel_request"]
        
        # Store destination insights
        state["destination_insights"] = {
            "overview": f"Comprehensive analysis of {travel_request.destination}",
            "best_time_to_visit": "Based on weather data analysis",
            "must_see_attractions": _extract_top_attractions(state),
            "local_customs": "Important cultural information",
            "safety_tips": "General safety guidelines",
            "transportation": "Local transportation options",
            "activity_recommendations": _generate_activity_recommendations(state)
        }
        
        state["completed_steps"].append("destination_research")
        logger.info("Destination research completed")
        
    except Exception as e:
        logger.error(f"Destination research failed: {e}")
        state["error_messages"].append(f"Destination research failed: {str(e)}")
        state["failed_steps"].append("destination_research")
    
    return state


async def local_expertise_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Add local expertise and hidden gems
    """
    logger.info("Executing local expertise node")
    
    try:
        # Add local insights
        state["local_insights"] = {
            "hidden_gems": _find_hidden_gems(state),
            "local_favorites": "Popular local spots",
            "avoid_tourist_traps": "Places to skip",
            "insider_tips": "Local recommendations",
            "best_neighborhoods": "Areas to explore",
            "local_activities": _generate_local_activities(state)
        }
        
        state["completed_steps"].append("local_expertise")
        logger.info("Local expertise added")
        
    except Exception as e:
        logger.error(f"Local expertise failed: {e}")
        state["error_messages"].append(f"Local expertise failed: {str(e)}")
        state["failed_steps"].append("local_expertise")
    
    return state


def should_continue_to_itinerary(state: TravelPlanningState) -> str:
    """
    Decide whether to continue to itinerary creation or handle insufficient data
    """
    # Check if we have minimum required data
    has_hotels = len(state.get("hotels", [])) > 0
    has_attractions = len(state.get("attractions", [])) > 0
    has_restaurants = len(state.get("restaurants", [])) > 0
    
    if has_hotels and has_attractions and has_restaurants:
        logger.info("Sufficient data available, proceeding to itinerary creation")
        return "create_itinerary"
    else:
        logger.warning("Insufficient data for itinerary creation")
        return "handle_insufficient_data"


async def handle_insufficient_data_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Handle cases where we don't have enough data
    """
    logger.info("Handling insufficient data")
    
    missing = []
    if not state.get("hotels"):
        missing.append("hotels")
    if not state.get("attractions"):
        missing.append("attractions")
    if not state.get("restaurants"):
        missing.append("restaurants")
    
    error_msg = f"Insufficient data for planning: missing {', '.join(missing)}"
    state["error_messages"].append(error_msg)
    state["failed_steps"].append("data_validation")
    
    logger.error(error_msg)
    return state


async def itinerary_creation_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Create the actual itinerary with comprehensive activity planning
    """
    logger.info("Executing itinerary creation node")
    
    try:
        travel_request = state["travel_request"]
        travel_style = state["planning_context"].get("travel_style", TravelStyle.CULTURAL)
        
        # Create daily plans with activities
        daily_plans = []
        
        for day in range(travel_request.duration):
            # Get date for this day
            start_date = datetime.fromisoformat(travel_request.start_date)
            current_date = start_date + timedelta(days=day)
            
            # Get weather for this day
            day_weather = None
            if day < len(state.get("weather_forecast", [])):
                day_weather = state["weather_forecast"][day]
            
            # Create daily plan
            daily_plan = DailyPlan(
                date=current_date.strftime("%Y-%m-%d"),
                weather=day_weather,
                activities=[]
            )
            
            # Generate activities for the day
            activities = _generate_daily_activities(
                day=day,
                weather=day_weather,
                attractions=state.get("attractions", []),
                restaurants=state.get("restaurants", []),
                travel_style=travel_style,
                interests=travel_request.interests
            )
            
            # Add activities to daily plan
            for activity in activities:
                daily_plan.add_activity(activity)
            
            daily_plans.append(daily_plan)
        
        # Store in state
        state["daily_itineraries"] = daily_plans
        state["completed_steps"].append("itinerary_creation")
        state["optimization_rounds"] = state.get("optimization_rounds", 0) + 1
        
        logger.info(f"Created itinerary for {len(daily_plans)} days with "
                   f"{sum(len(day.activities) for day in daily_plans)} total activities")
        
    except Exception as e:
        logger.error(f"Itinerary creation failed: {e}")
        state["error_messages"].append(f"Itinerary creation failed: {str(e)}")
        state["failed_steps"].append("itinerary_creation")
    
    return state


async def trip_criticism_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Review and optimize the itinerary with activity-focused feedback
    """
    logger.info("Executing trip criticism node")
    
    try:
        # Enhanced criticism logic
        feedback = {
            "round": state.get("optimization_rounds", 1),
            "timestamp": datetime.now().isoformat(),
            "issues": [],
            "suggestions": [],
            "activity_analysis": {}
        }
        
        # Check for basic issues
        daily_plans = state.get("daily_itineraries", [])
        if len(daily_plans) < state["travel_request"].duration:
            feedback["issues"].append("Incomplete itinerary")
        
        if not state.get("hotels"):
            feedback["issues"].append("No hotel recommendations")
        
        # Activity-specific criticism
        activity_feedback = _analyze_activities(daily_plans)
        feedback["activity_analysis"] = activity_feedback
        
        # Check for activity balance
        if activity_feedback.get("activity_imbalance"):
            feedback["issues"].append("Activity type imbalance detected")
            feedback["suggestions"].append("Diversify activity types across days")
        
        # Check for scheduling conflicts
        if activity_feedback.get("scheduling_conflicts"):
            feedback["issues"].append("Scheduling conflicts detected")
            feedback["suggestions"].append("Adjust activity timing")
        
        # Weather-based suggestions
        weather_suggestions = _analyze_weather_activities(daily_plans)
        feedback["suggestions"].extend(weather_suggestions)
        
        # Add to feedback list
        if "critic_feedback" not in state:
            state["critic_feedback"] = []
        state["critic_feedback"].append(feedback)
        
        state["completed_steps"].append("trip_criticism")
        logger.info(f"Trip criticism completed (round {feedback['round']})")
        
    except Exception as e:
        logger.error(f"Trip criticism failed: {e}")
        state["error_messages"].append(f"Trip criticism failed: {str(e)}")
        state["failed_steps"].append("trip_criticism")
    
    return state


def should_optimize_again(state: TravelPlanningState) -> str:
    """
    Decide whether to optimize again or finalize
    """
    max_rounds = 2
    current_rounds = state.get("optimization_rounds", 0)
    
    if current_rounds >= max_rounds:
        logger.info("Maximum optimization rounds reached, proceeding to finalization")
        return "finalization"  # Changed from "finalize" to match your node name
    
    # Check if there are critical issues
    if state.get("critic_feedback"):
        latest_feedback = state["critic_feedback"][-1]
        critical_issues = [
            "Scheduling conflicts detected",
            "Activity type imbalance detected",
            "Incomplete itinerary"
        ]
        
        has_critical_issues = any(
            issue in latest_feedback.get("issues", []) 
            for issue in critical_issues
        )
        
        if has_critical_issues and current_rounds < max_rounds:
            logger.info("Critical issues found, optimizing again")
            return "optimize_itinerary"  # This needs to match your graph node name
    
    return "finalization"  # Changed from "finalize" to match your node name

async def optimize_itinerary_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Optimize the itinerary based on criticism feedback
    """
    logger.info("Executing itinerary optimization node")
    
    try:
        if not state.get("critic_feedback"):
            logger.warning("No feedback available for optimization")
            return state
        
        latest_feedback = state["critic_feedback"][-1]
        daily_plans = state.get("daily_itineraries", [])
        
        # Apply optimizations based on feedback
        optimized_plans = []
        
        for day_plan in daily_plans:
            optimized_plan = _optimize_daily_plan(day_plan, latest_feedback)
            optimized_plans.append(optimized_plan)
        
        # Update state with optimized plans
        state["daily_itineraries"] = optimized_plans
        state["optimization_rounds"] = state.get("optimization_rounds", 0) + 1
        
        logger.info(f"Itinerary optimization completed (round {state['optimization_rounds']})")
        
    except Exception as e:
        logger.error(f"Itinerary optimization failed: {e}")
        state["error_messages"].append(f"Optimization failed: {str(e)}")
        state["failed_steps"].append("optimization")
    
    return state


async def finalization_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Create final travel itinerary with comprehensive activity data
    """
    logger.info("Executing finalization node")
    
    try:
        travel_request = state["travel_request"]
        
        # Calculate total estimated cost
        total_cost = 0
        for day_plan in state.get("daily_itineraries", []):
            total_cost += day_plan.total_estimated_cost
        
        # Generate packing suggestions based on activities
        packing_suggestions = _generate_packing_suggestions(
            state.get("daily_itineraries", []),
            state.get("weather_forecast", [])
        )
        
        # Generate important notes
        important_notes = _generate_important_notes(
            travel_request.destination,
            state.get("daily_itineraries", [])
        )
        
        # Create final itinerary
        final_itinerary = TravelItinerary(
            destination=travel_request.destination,
            start_date=travel_request.start_date,
            end_date=travel_request.end_date,
            duration=travel_request.duration,
            weather_forecast=state.get("weather_forecast", []),
            daily_plans=state.get("daily_itineraries", []),
            total_budget=travel_request.budget,
            total_estimated_cost=total_cost,
            hotels=state.get("hotels", [])[:3],  # Top 3 hotels
            attractions=state.get("attractions", []),
            restaurants=state.get("restaurants", []),
            transportation_info={
                "type": "Mixed transport",
                "details": "Combination of public transport, walking, and ride-sharing",
                "estimated_daily_cost": 15.0
            },
            packing_suggestions=packing_suggestions,
            important_notes=important_notes,
            recommendations=_generate_final_recommendations(state)
        )
        
        # Store in state
        state["final_itinerary"] = final_itinerary
        state["completed_steps"].append("finalization")
        
        logger.info(f"Finalization completed successfully. Total activities: {final_itinerary.total_activities}")
        
    except Exception as e:
        logger.error(f"Finalization failed: {e}")
        state["error_messages"].append(f"Finalization failed: {str(e)}")
        state["failed_steps"].append("finalization")
    
    return state


# Helper functions for activity management
def _generate_daily_activities(day: int, weather: Optional[WeatherInfo], 
                             attractions: List[PlaceRecommendation],
                             restaurants: List[PlaceRecommendation],
                             travel_style: TravelStyle,
                             interests: List[str]) -> List[Activity]:
    """Generate activities for a single day"""
    activities = []
    
    # Morning activity (9:00 AM)
    if attractions:
        morning_attraction = attractions[day % len(attractions)]
        morning_activity = ActivityGenerator.create_activity_from_place(
            morning_attraction, "09:00", travel_style
        )
        
        # Adjust for weather
        if weather and not weather.is_good_weather and morning_activity.weather_dependent:
            # Find indoor alternative
            indoor_attractions = [a for a in attractions if a.place_type in ["museum", "shopping_mall"]]
            if indoor_attractions:
                morning_attraction = indoor_attractions[day % len(indoor_attractions)]
                morning_activity = ActivityGenerator.create_activity_from_place(
                    morning_attraction, "09:00", travel_style
                )
        
        activities.append(morning_activity)
    
    # Lunch (12:00 PM)
    lunch_activity = ActivityGenerator.create_meal_activity(
        "lunch", "12:00", restaurants, travel_style
    )
    if lunch_activity:
        activities.append(lunch_activity)
    
    # Afternoon activity (2:00 PM)
    if len(attractions) > 1:
        afternoon_attraction = attractions[(day + 1) % len(attractions)]
        afternoon_activity = ActivityGenerator.create_activity_from_place(
            afternoon_attraction, "14:00", travel_style
        )
        activities.append(afternoon_activity)
    
    # Evening activity (6:00 PM)
    if len(restaurants) > 1:
        dinner_activity = ActivityGenerator.create_meal_activity(
            "dinner", "18:00", restaurants, travel_style
        )
        if dinner_activity:
            activities.append(dinner_activity)
    
    # Add transportation between activities
    if len(activities) > 1:
        transport_activities = []
        for i in range(len(activities) - 1):
            current_activity = activities[i]
            next_activity = activities[i + 1]
            
            # Calculate transport time
            transport_start = current_activity.end_time
            transport_activity = ActivityGenerator.create_transportation_activity(
                current_activity.location or "Previous location",
                next_activity.location or "Next location",
                transport_start,
                duration=20  # 20-minute travel time
            )
            transport_activities.append((i + 1, transport_activity))
        
        # Insert transport activities
        for offset, (index, transport_activity) in enumerate(transport_activities):
            activities.insert(index + offset, transport_activity)
    
    return activities


def _analyze_activities(daily_plans: List[DailyPlan]) -> Dict[str, Any]:
    """Analyze activities across all days for balance and conflicts"""
    analysis = {
        "total_activities": 0,
        "activity_types": {},
        "scheduling_conflicts": False,
        "activity_imbalance": False,
        "average_daily_cost": 0,
        "weather_conflicts": []
    }
    
    total_cost = 0
    
    for day_plan in daily_plans:
        analysis["total_activities"] += len(day_plan.activities)
        total_cost += day_plan.total_estimated_cost
        
        # Track activity types
        for activity in day_plan.activities:
            activity_type = activity.activity_type.value
            analysis["activity_types"][activity_type] = (
                analysis["activity_types"].get(activity_type, 0) + 1
            )
        
        # Check for scheduling conflicts
        activities_sorted = sorted(day_plan.activities, key=lambda x: x.start_time)
        for i in range(len(activities_sorted) - 1):
            current = activities_sorted[i]
            next_activity = activities_sorted[i + 1]
            
            # Check if current activity ends after next one starts
            if current.end_time > next_activity.start_time:
                analysis["scheduling_conflicts"] = True
                break
        
        # Check weather conflicts
        if day_plan.weather and not day_plan.weather.is_good_weather:
            outdoor_activities = [a for a in day_plan.activities if a.weather_dependent]
            if outdoor_activities:
                analysis["weather_conflicts"].append({
                    "date": day_plan.date,
                    "activities": [a.name for a in outdoor_activities]
                })
    
    # Calculate averages
    if daily_plans:
        analysis["average_daily_cost"] = total_cost / len(daily_plans)
    
    # Check for activity imbalance
    if analysis["activity_types"]:
        max_count = max(analysis["activity_types"].values())
        min_count = min(analysis["activity_types"].values())
        if max_count > min_count * 2:  # If one type is more than double another
            analysis["activity_imbalance"] = True
    
    return analysis


def _analyze_weather_activities(daily_plans: List[DailyPlan]) -> List[str]:
    """Analyze weather vs activities and provide suggestions"""
    suggestions = []
    
    for day_plan in daily_plans:
        if not day_plan.weather:
            continue
        
        weather = day_plan.weather
        outdoor_activities = [a for a in day_plan.activities if a.weather_dependent]
        
        if not weather.is_good_weather and outdoor_activities:
            suggestions.append(
                f"Consider indoor alternatives for {day_plan.date} due to weather"
            )
        
        if weather.precipitation_chance > 60:
            suggestions.append(
                f"High rain chance on {day_plan.date} - prioritize indoor activities"
            )
    
    return suggestions


def _optimize_daily_plan(day_plan: DailyPlan, feedback: Dict[str, Any]) -> DailyPlan:
    """Optimize a single day plan based on feedback"""
    optimized_activities = []
    
    for activity in day_plan.activities:
        # Skip activities that conflict with weather
        if (day_plan.weather and not day_plan.weather.is_good_weather and 
            activity.weather_dependent and not activity.indoor_activity):
            # Replace with indoor alternative
            if activity.activity_type == ActivityType.SIGHTSEEING:
                # Convert to museum/cultural activity
                activity.activity_type = ActivityType.CULTURAL
                activity.indoor_activity = True
                activity.weather_dependent = False
                activity.description += " (moved indoors due to weather)"
        
        optimized_activities.append(activity)
    
    # Re-sort activities by time
    optimized_activities.sort(key=lambda x: x.start_time)
    
    # Update the day plan
    day_plan.activities = optimized_activities
    
    return day_plan


def _generate_packing_suggestions(daily_plans: List[DailyPlan], 
                                weather_forecast: List[WeatherInfo]) -> List[str]:
    """Generate packing suggestions based on activities and weather"""
    suggestions = []
    
    # Activity-based suggestions
    activity_types = set()
    for day_plan in daily_plans:
        for activity in day_plan.activities:
            activity_types.add(activity.activity_type)
    
    if ActivityType.OUTDOOR in activity_types:
        suggestions.extend([
            "Comfortable hiking shoes",
            "Sun protection (hat, sunscreen)",
            "Water bottle"
        ])
    
    if ActivityType.CULTURAL in activity_types:
        suggestions.extend([
            "Comfortable walking shoes",
            "Modest clothing for religious sites"
        ])
    
    if ActivityType.DINING in activity_types:
        suggestions.append("Smart casual attire for restaurants")
    
    # Weather-based suggestions
    if weather_forecast:
        temps = [w.temperature_high for w in weather_forecast]
        if min(temps) < 15:
            suggestions.append("Warm jacket or sweater")
        if max(temps) > 25:
            suggestions.append("Light, breathable clothing")
        
        if any(w.precipitation_chance > 50 for w in weather_forecast):
            suggestions.extend(["Umbrella or rain jacket", "Waterproof shoes"])
    
    return list(set(suggestions))  # Remove duplicates


def _generate_important_notes(destination: str, daily_plans: List[DailyPlan]) -> List[str]:
    """Generate important notes based on destination and activities"""
    notes = [
        f"Check visa requirements for {destination}",
        "Notify bank of travel plans",
        "Consider travel insurance"
    ]
    
    # Activity-specific notes
    has_booking_required = any(
        activity.booking_required
        for day_plan in daily_plans
        for activity in day_plan.activities
    )
    
    if has_booking_required:
        notes.append("Some activities require advance booking")
    
    has_cultural_activities = any(
        activity.activity_type == ActivityType.CULTURAL
        for day_plan in daily_plans
        for activity in day_plan.activities
    )
    
    if has_cultural_activities:
        notes.append("Research local customs and dress codes")
    
    return notes


def _generate_final_recommendations(state: Dict[str, Any]) -> List[str]:
    """Generate final travel recommendations"""
    recommendations = []
    
    # Based on activities
    total_activities = sum(
        len(day.activities) for day in state.get("daily_itineraries", [])
    )
    
    if total_activities > 20:
        recommendations.append("Consider a more relaxed pace - you have many activities planned")
    
    # Based on budget
    travel_request = state["travel_request"]
    if travel_request.budget:
        estimated_cost = sum(
            day.total_estimated_cost for day in state.get("daily_itineraries", [])
        )
        if estimated_cost > travel_request.budget:
            recommendations.append("Consider reducing activities or finding budget alternatives")
    
    # General recommendations
    recommendations.extend([
        "Download offline maps for navigation",
        "Learn basic local phrases",
        "Keep emergency contacts handy",
        "Take photos of important documents"
    ])
    
    return recommendations


# Mock data generators for testing
def _generate_mock_hotels(destination: str) -> List[PlaceRecommendation]:
    """Generate mock hotel data"""
    return [
        PlaceRecommendation(
            place_id=f"hotel_{i}",
            name=f"Hotel {i} in {destination}",
            rating=4.0 + (i * 0.1),
            price_level=i % 4 + 1,
            place_type="lodging",
            address=f"Street {i}, {destination}"
        ) for i in range(1, 6)
    ]


def _generate_mock_restaurants(destination: str) -> List[PlaceRecommendation]:
    """Generate mock restaurant data"""
    return [
        PlaceRecommendation(
            place_id=f"restaurant_{i}",
            name=f"Restaurant {i} in {destination}",
            rating=3.5 + (i * 0.2),
            price_level=i % 4 + 1,
            place_type="restaurant",
            address=f"Food Street {i}, {destination}"
        ) for i in range(1, 8)
    ]


def _generate_mock_attractions(destination: str) -> List[PlaceRecommendation]:
    """Generate mock attraction data"""
    attraction_types = ["tourist_attraction", "museum", "park", "historical_site"]
    return [
        PlaceRecommendation(
            place_id=f"attraction_{i}",
            name=f"Attraction {i} in {destination}",
            rating=4.0 + (i * 0.1),
            price_level=i % 3 + 1,
            place_type=attraction_types[i % len(attraction_types)],
            address=f"Tourist Street {i}, {destination}"
        ) for i in range(1, 10)
    ]


def _generate_mock_weather(duration: int) -> List[WeatherInfo]:
    """Generate mock weather data"""
    return [
        WeatherInfo(
            date=(datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d"),
            temperature_high=20 + (i % 10),
            temperature_low=15 + (i % 5),
            description=["Sunny", "Partly cloudy", "Rainy", "Cloudy"][i % 4],
            humidity=60 + (i % 20),
            wind_speed=10 + (i % 15),
            precipitation_chance=i * 10 % 80
        ) for i in range(duration)
    ]


# Helper functions (continued from previous implementation)
def _calculate_data_completeness(state: Dict[str, Any]) -> float:
    """Calculate how complete the collected data is"""
    components = [
        len(state.get("hotels", [])) > 0,
        len(state.get("restaurants", [])) > 0,
        len(state.get("attractions", [])) > 0,
        len(state.get("weather_forecast", [])) > 0
    ]
    return sum(components) / len(components)


def _extract_top_attractions(state: Dict[str, Any]) -> List[str]:
    """Extract top attractions from state"""
    attractions = state.get("attractions", [])
    if not attractions:
        return ["No attractions available"]
    
    # Sort by rating and return top 5
    sorted_attractions = sorted(attractions, key=lambda x: x.rating, reverse=True)
    return [attr.name for attr in sorted_attractions[:5]]


def _find_hidden_gems(state: Dict[str, Any]) -> List[str]:
    """Find hidden gems from the data"""
    attractions = state.get("attractions", [])
    
    # Find attractions with good ratings but lower popularity (fewer reviews)
    hidden_gems = []
    for attr in attractions:
        if attr.rating >= 4.0 and hasattr(attr, 'review_count'):
            if attr.review_count < 100:  # Assuming fewer reviews = less popular
                hidden_gems.append(attr.name)
    
    return hidden_gems[:3] if hidden_gems else ["Local market", "Hidden garden", "Authentic local restaurant"]


def _generate_activity_recommendations(state: Dict[str, Any]) -> List[str]:
    """Generate activity recommendations based on data"""
    recommendations = []
    
    attractions = state.get("attractions", [])
    if attractions:
        # Group by activity type
        cultural_sites = [a for a in attractions if a.place_type in ["museum", "historical_site"]]
        outdoor_spots = [a for a in attractions if a.place_type in ["park", "tourist_attraction"]]
        
        if cultural_sites:
            recommendations.append("Explore local museums and historical sites")
        if outdoor_spots:
            recommendations.append("Enjoy outdoor activities and natural attractions")
    
    return recommendations


def _generate_local_activities(state: Dict[str, Any]) -> List[str]:
    """Generate local activity suggestions"""
    return [
        "Visit local markets in the morning",
        "Take a walking tour of historic neighborhoods",
        "Try street food at popular local spots",
        "Attend cultural performances or events",
        "Explore artisan workshops and galleries"
    ]


# Export all node functions
__all__ = [
    'planning_node',
    'data_collection_node',
    'destination_research_node',
    'local_expertise_node',
    'should_continue_to_itinerary',
    'handle_insufficient_data_node',
    'itinerary_creation_node',
    'trip_criticism_node',
    'should_optimize_again',
    'optimize_itinerary_node',
    'finalization_node',
    'ActivityGenerator'
]