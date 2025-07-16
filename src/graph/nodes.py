"""
Additional workflow nodes for itinerary creation, criticism, and finalization
Continuation of the LangGraph node definitions
"""

import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from graph.state import TravelPlanningState, update_state_step
from ..agents.base_agent import LLMAgent
from ..agents.prompts import get_agent_prompt, format_prompt
from core.models import DailyPlan, WeatherInfo, TravelItinerary, PlaceRecommendation
from core.exceptions import AgentError


logger = logging.getLogger("graph_nodes")


async def itinerary_creation_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Itinerary creation node - creates detailed day-by-day itineraries
    """
    logger.info("Executing itinerary creation node")
    
    try:
        # Create itinerary expert agent
        itinerary_expert = LLMAgent(
            "itinerary_expert",
            get_agent_prompt("itinerary_expert"),
            reasoning_steps=[
                "Analyze available attractions and their optimal timing",
                "Consider weather conditions for each day",
                "Balance activity intensity and rest periods",
                "Optimize routing and transportation logistics"
            ]
        )
        
        request = state["travel_request"]
        duration = getattr(request, 'duration', 1)
        
        # Create daily itineraries
        daily_plans = []
        
        for day_num in range(duration):
            # Calculate date for this day
            start_date = datetime.fromisoformat(request.start_date)
            current_date = (start_date + timedelta(days=day_num)).strftime("%Y-%m-%d")
            
            # Get weather for this day
            day_weather = None
            if day_num < len(state["weather_forecast"]):
                day_weather = state["weather_forecast"][day_num]
            else:
                # Create default weather if not available
                day_weather = WeatherInfo(
                    date=current_date,
                    temperature_high=22.0,
                    temperature_low=15.0,
                    description="Partly cloudy",
                    humidity=60,
                    wind_speed=10.0,
                    precipitation_chance=20
                )
            
            # Create daily itinerary
            daily_plan = await _create_single_day_itinerary(
                itinerary_expert,
                current_date,
                day_weather,
                state["attractions"],
                state["restaurants"],
                request.interests,
                _determine_budget_level(request.budget, duration),
                day_num + 1  # Energy level based on day of trip
            )
            
            if daily_plan:
                daily_plans.append(daily_plan)
                logger.info(f"Created itinerary for day {day_num + 1}: {current_date}")
        
        # Update state
        state["daily_itineraries"].extend(daily_plans)
        state = update_state_step(state, "itinerary_creation", success=True)
        
        logger.info(f"Itinerary creation completed for {len(daily_plans)} days")
        return state
        
    except Exception as e:
        logger.error(f"Itinerary creation failed: {e}")
        state = update_state_step(state, "itinerary_creation", success=False, error_message=str(e))
        return state


async def _create_single_day_itinerary(
    agent: LLMAgent,
    date: str,
    weather: WeatherInfo,
    attractions: List[PlaceRecommendation],
    restaurants: List[PlaceRecommendation],
    interests: List[str],
    budget_level: str,
    energy_level: int
) -> DailyPlan:
    """Create itinerary for a single day"""
    
    # Prepare data for the day
    available_attractions = [
        {
            "name": attr.name,
            "type": attr.place_type,
            "rating": attr.rating,
            "address": attr.address
        }
        for attr in attractions[:15]  # Limit to top 15
    ]
    
    available_restaurants = [
        {
            "name": rest.name,
            "rating": rest.rating,
            "price_level": rest.price_level,
            "address": rest.address
        }
        for rest in restaurants[:10]  # Limit to top 10
    ]
    
    # Determine energy level description
    energy_descriptions = {
        1: "high",  # First day
        2: "high",
        3: "medium",
        4: "medium", 
        5: "medium-low",
        6: "low",
        7: "low"
    }
    energy_desc = energy_descriptions.get(min(energy_level, 7), "medium")
    
    # Create itinerary prompt
    itinerary_prompt = format_prompt(
        "create_daily_itinerary",
        date=date,
        destination="destination",  # Will be filled from context
        weather_description=weather.description,
        temp_high=weather.temperature_high,
        temp_low=weather.temperature_low,
        attractions=available_attractions,
        restaurants=available_restaurants,
        interests=", ".join(interests),
        budget_level=budget_level,
        energy_level=energy_desc
    )
    
    # Get itinerary from LLM
    context_data = {
        "weather": weather.__dict__,
        "attractions": available_attractions,
        "restaurants": available_restaurants,
        "constraints": {
            "budget_level": budget_level,
            "energy_level": energy_desc,
            "weather_sensitive": weather.precipitation_chance > 50
        }
    }
    
    itinerary_result = await agent.query_ollama(itinerary_prompt, context_data)
    
    # Create DailyPlan (simplified - in production would parse LLM response)
    return DailyPlan(
        date=date,
        weather=weather,
        morning_activities=["Morning activity based on LLM response"],
        afternoon_activities=["Afternoon activity based on LLM response"],
        evening_activities=["Evening activity based on LLM response"],
        recommended_restaurants=restaurants[:2]  # Top 2 restaurants
    )


async def trip_criticism_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Trip criticism node - reviews and optimizes the itinerary
    """
    logger.info("Executing trip criticism node")
    
    try:
        # Create trip critic agent
        trip_critic = LLMAgent(
            "trip_critic",
            get_agent_prompt("trip_critic"),
            reasoning_steps=[
                "Analyze itinerary flow and logical sequencing",
                "Evaluate budget compliance and optimization opportunities",
                "Check for scheduling conflicts and pacing issues",
                "Assess weather adaptation and backup plans"
            ]
        )
        
        request = state["travel_request"]
        
        # Prepare itinerary summary for criticism
        itinerary_summary = {
            "destination": request.destination,
            "duration": getattr(request, 'duration', 1),
            "budget": request.budget,
            "daily_plans": [
                {
                    "date": plan.date,
                    "weather": f"{plan.weather.description} ({plan.weather.temperature_high}°C)",
                    "activities": (
                        plan.morning_activities + 
                        plan.afternoon_activities + 
                        plan.evening_activities
                    ),
                    "restaurants": [r.name for r in plan.recommended_restaurants]
                }
                for plan in state["daily_itineraries"]
            ]
        }
        
        # Calculate estimated costs
        total_estimated_cost = _calculate_estimated_costs(state)
        budget_status = _determine_budget_status(total_estimated_cost, request.budget)
        
        # Create criticism prompt
        criticism_prompt = format_prompt(
            "optimize_itinerary",
            original_request=request.__dict__,
            itinerary=itinerary_summary,
            estimated_cost=total_estimated_cost,
            budget=request.budget or 0,
            budget_status=budget_status
        )
        
        # Get criticism and recommendations
        criticism_context = {
            "itinerary_summary": itinerary_summary,
            "cost_analysis": {
                "total_estimated": total_estimated_cost,
                "budget": request.budget,
                "status": budget_status
            },
            "data_quality": {
                "hotels_available": len(state["hotels"]),
                "restaurants_available": len(state["restaurants"]),
                "attractions_available": len(state["attractions"]),
                "weather_coverage": len(state["weather_forecast"])
            }
        }
        
        criticism_result = await trip_critic.reason_through_problem(
            "Review and optimize travel itinerary",
            criticism_context
        )
        
        # Add feedback to state
        feedback_entry = {
            "round": state["optimization_rounds"] + 1,
            "criticism": criticism_result,
            "timestamp": datetime.utcnow().isoformat(),
            "cost_analysis": criticism_context["cost_analysis"]
        }
        
        state["critic_feedback"].append(feedback_entry)
        state["optimization_rounds"] += 1
        
        state = update_state_step(state, "trip_criticism", success=True)
        logger.info(f"Trip criticism completed (round {state['optimization_rounds']})")
        
        return state
        
    except Exception as e:
        logger.error(f"Trip criticism failed: {e}")
        state = update_state_step(state, "trip_criticism", success=False, error_message=str(e))
        return state


async def finalization_node(state: TravelPlanningState) -> TravelPlanningState:
    """
    Finalization node - creates final travel itinerary
    """
    logger.info("Executing finalization node")
    
    try:
        request = state["travel_request"]
        
        # Calculate final costs
        total_cost = _calculate_estimated_costs(state)
        
        # Create final itinerary
        final_itinerary = TravelItinerary(
            destination=request.destination,
            start_date=request.start_date,
            end_date=request.end_date,
            duration=getattr(request, 'duration', 1),
            weather_forecast=state["weather_forecast"],
            hotels=state["hotels"][:5],  # Top 5 hotels
            attractions=state["attractions"][:10],  # Top 10 attractions
            restaurants=state["restaurants"][:8],  # Top 8 restaurants
            daily_plans=state["daily_itineraries"],
            total_estimated_cost=total_cost,
            created_at=datetime.utcnow()
        )
        
        # Add recommendations based on criticism
        recommendations = []
        if state["critic_feedback"]:
            latest_feedback = state["critic_feedback"][-1]
            recommendations.append("Consider feedback from trip optimization analysis")
        
        if total_cost and request.budget and total_cost > request.budget:
            recommendations.append("Budget optimization may be needed")
        
        final_itinerary.recommendations = recommendations
        
        # Update state
        state["final_itinerary"] = final_itinerary
        state = update_state_step(state, "finalization", success=True)
        
        logger.info("Finalization completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Finalization failed: {e}")
        state = update_state_step(state, "finalization", success=False, error_message=str(e))
        return state


def _determine_budget_level(budget: float, duration: int) -> str:
    """Determine budget level category"""
    if not budget or duration <= 0:
        return "unknown"
    
    daily_budget = budget / duration
    
    if daily_budget < 100:
        return "budget"
    elif daily_budget < 200:
        return "mid_range"
    elif daily_budget < 400:
        return "luxury"
    else:
        return "ultra_luxury"


def _calculate_estimated_costs(state: TravelPlanningState) -> float:
    """Calculate estimated total costs for the trip"""
    total = 0.0
    
    # Hotel costs (average top 3 hotels per night)
    if state["hotels"]:
        avg_hotel_cost = sum(
            (h.price_level or 0) * 50  # Rough estimate: price_level * $50
            for h in state["hotels"][:3]
        ) / min(3, len(state["hotels"]))
        
        duration = len(state["daily_itineraries"]) or 1
        total += avg_hotel_cost * duration
    
    # Activity and meal costs per day
    daily_activity_cost = 80  # Rough estimate
    daily_meal_cost = 60     # Rough estimate
    
    total += (daily_activity_cost + daily_meal_cost) * len(state["daily_itineraries"])
    
    return total


def _determine_budget_status(estimated_cost: float, budget: float) -> str:
    """Determine budget status"""
    if not budget:
        return "no_budget_specified"
    
    if estimated_cost <= budget:
        return "within_budget"
    elif estimated_cost <= budget * 1.1:
        return "slightly_over_budget"
    else:
        return "over_budget"


async def should_optimize_again(state: TravelPlanningState) -> str:
    """
    Decision node - determines if another optimization round is needed
    """
    max_optimization_rounds = 2
    
    if state["optimization_rounds"] >= max_optimization_rounds:
        logger.info("Maximum optimization rounds reached, proceeding to finalization")
        return "finalize"
    
    # Check if there are critical issues that need addressing
    if state["critic_feedback"]:
        latest_feedback = state["critic_feedback"][-1]
        # In production, would parse feedback to determine if re-optimization is needed
        # For now, always proceed to finalization after first round
        logger.info("Proceeding to finalization after criticism")
        return "finalize"
    
    return "finalize"