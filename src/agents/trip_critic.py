"""
Itinerary Expert Agent - Creates detailed day-by-day travel itineraries
Implements comprehensive itinerary planning and optimization
"""

import json
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from agents.base_agent import LLMAgent
from agents.prompts import get_agent_prompt, format_prompt
from core.models import PlaceRecommendation, WeatherInfo, DailyPlan
from core.exceptions import AgentError
from core.constants import ACTIVITY_DURATIONS


class ItineraryExpert(LLMAgent):
    """
    Itinerary expert agent that creates detailed day-by-day travel plans
    
    Responsibilities:
    - Create detailed daily itineraries with optimal timing
    - Balance activities with rest periods and travel time
    - Optimize routes and minimize transportation time
    - Consider weather conditions and seasonal factors
    - Ensure realistic and achievable daily schedules
    """
    
    def __init__(self):
        super().__init__(
            agent_name="itinerary_expert",
            system_prompt=get_agent_prompt("itinerary_expert"),
            reasoning_steps=[
                "Analyze available attractions and optimal daily distribution",
                "Consider weather patterns and activity suitability",
                "Optimize routing and minimize travel time between locations",
                "Balance activity intensity with rest and meal periods",
                "Create realistic and enjoyable daily schedules"
            ]
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for itinerary creation
        """
        self.log_action("Starting itinerary creation")
        
        # Validate input
        await self.validate_input(input_data, ["travel_request", "collected_data", "local_expertise"])
        
        travel_request = input_data["travel_request"]
        collected_data = input_data["collected_data"]
        local_expertise = input_data.get("local_expertise", {})
        
        # Create comprehensive itinerary
        itinerary_result = await self.create_comprehensive_itinerary(
            travel_request, collected_data, local_expertise
        )
        
        return {
            "daily_itineraries": itinerary_result,
            "agent_name": self.agent_name,
            "processing_time": (datetime.utcnow() - self.start_time).total_seconds(),
            "status": "completed"
        }
    
    async def create_comprehensive_itinerary(self, travel_request, collected_data: Dict[str, Any],
                                           local_expertise: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive day-by-day itinerary
        """
        self.log_action(f"Creating itinerary for {travel_request.destination}")
        
        duration = getattr(travel_request, 'duration', 1)
        
        # Prepare itinerary data
        itinerary_data = await self.prepare_itinerary_data(
            travel_request, collected_data, local_expertise
        )
        
        # Create daily plans
        daily_plans = []
        for day_num in range(duration):
            daily_plan = await self.create_daily_itinerary(
                day_num + 1,
                travel_request,
                itinerary_data,
                collected_data.get("weather", [])
            )
            daily_plans.append(daily_plan)
            self.log_action(f"Created itinerary for day {day_num + 1}")
        
        # Optimize overall itinerary flow
        optimized_plans = await self.optimize_itinerary_flow(daily_plans, itinerary_data)
        
        # Calculate costs and logistics
        itinerary_summary = await self.create_itinerary_summary(
            optimized_plans, travel_request, itinerary_data
        )
        
        return {
            "daily_plans": optimized_plans,
            "itinerary_summary": itinerary_summary,
            "optimization_notes": await self.generate_optimization_notes(optimized_plans),
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def prepare_itinerary_data(self, travel_request, collected_data: Dict[str, Any],
                                   local_expertise: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare and organize data for itinerary creation
        """
        self.log_action("Preparing itinerary data")
        
        # Categorize and rank attractions
        attractions = collected_data.get("attractions", [])
        restaurants = collected_data.get("restaurants", [])
        
        categorized_attractions = self._categorize_attractions_by_time(attractions)
        ranked_restaurants = self._rank_restaurants_by_meal_type(restaurants)
        
        # Extract timing insights from local expertise
        timing_optimization = local_expertise.get("timing_optimization", {})
        local_recommendations = local_expertise.get("local_recommendations", {})
        
        return {
            "attractions": {
                "morning_suitable": categorized_attractions["morning"],
                "afternoon_suitable": categorized_attractions["afternoon"],
                "evening_suitable": categorized_attractions["evening"],
                "all_day": categorized_attractions["flexible"]
            },
            "restaurants": {
                "breakfast": ranked_restaurants["breakfast"],
                "lunch": ranked_restaurants["lunch"],
                "dinner": ranked_restaurants["dinner"]
            },
            "timing_insights": timing_optimization,
            "local_recommendations": local_recommendations,
            "budget_level": self._determine_budget_level(travel_request.budget, getattr(travel_request, 'duration', 1)),
            "interests": travel_request.interests
        }
    
    async def create_daily_itinerary(self, day_number: int, travel_request,
                                   itinerary_data: Dict[str, Any],
                                   weather_forecast: List[WeatherInfo]) -> DailyPlan:
        """
        Create detailed itinerary for a single day
        """
        self.log_action(f"Creating day {day_number} itinerary")
        
        # Calculate date for this day
        start_date = datetime.fromisoformat(travel_request.start_date)
        current_date = (start_date + timedelta(days=day_number - 1)).strftime("%Y-%m-%d")
        
        # Get weather for this day
        day_weather = self._get_weather_for_day(weather_forecast, day_number - 1)
        
        # Determine day's theme and energy level
        day_theme = self._determine_day_theme(day_number, getattr(travel_request, 'duration', 1))
        energy_level = self._calculate_energy_level(day_number)
        
        # Create daily schedule using LLM
        daily_schedule = await self._generate_daily_schedule(
            current_date, day_weather, day_theme, energy_level, itinerary_data, travel_request
        )
        
        # Create DailyPlan object
        daily_plan = DailyPlan(
            date=current_date,
            weather=day_weather,
            morning_activities=daily_schedule["morning"],
            afternoon_activities=daily_schedule["afternoon"],
            evening_activities=daily_schedule["evening"],
            recommended_restaurants=daily_schedule["restaurants"]
        )
        
        return daily_plan
    
    async def _generate_daily_schedule(self, date: str, weather: WeatherInfo,
                                     day_theme: str, energy_level: str,
                                     itinerary_data: Dict[str, Any],
                                     travel_request) -> Dict[str, Any]:
        """
        Generate detailed daily schedule using LLM
        """
        # Prepare schedule generation prompt
        schedule_prompt = f"""
        Create a detailed daily itinerary for this travel day:
        
        Date: {date}
        Destination: {travel_request.destination}
        Day Theme: {day_theme}
        Energy Level: {energy_level}
        
        Weather Conditions:
        - Temperature: {weather.temperature_low}°C - {weather.temperature_high}°C
        - Condition: {weather.description}
        - Rain Chance: {weather.precipitation_chance}%
        
        Available Attractions by Time:
        Morning Options: {[a.name for a in itinerary_data['attractions']['morning_suitable'][:5]]}
        Afternoon Options: {[a.name for a in itinerary_data['attractions']['afternoon_suitable'][:5]]}
        Evening Options: {[a.name for a in itinerary_data['attractions']['evening_suitable'][:3]]}
        
        Restaurant Options:
        Breakfast: {[r.name for r in itinerary_data['restaurants']['breakfast'][:3]]}
        Lunch: {[r.name for r in itinerary_data['restaurants']['lunch'][:3]]}
        Dinner: {[r.name for r in itinerary_data['restaurants']['dinner'][:3]]}
        
        Create a balanced daily schedule with:
        1. Morning activities (9 AM - 12 PM)
        2. Lunch and afternoon activities (12 PM - 6 PM)
        3. Evening activities and dinner (6 PM - 10 PM)
        
        Consider weather conditions, energy level, and logical flow between activities.
        Include estimated times and brief reasoning for choices.
        """
        
        context_data = {
            "date": date,
            "weather": weather.__dict__,
            "day_theme": day_theme,
            "energy_level": energy_level,
            "available_options": itinerary_data["attractions"],
            "restaurants": itinerary_data["restaurants"],
            "budget_level": itinerary_data["budget_level"]
        }
        
        schedule_result = await self.query_ollama(schedule_prompt, context_data)
        
        # Parse and structure the schedule (simplified for demo)
        return {
            "morning": self._select_morning_activities(itinerary_data, weather, energy_level),
            "afternoon": self._select_afternoon_activities(itinerary_data, weather, energy_level),
            "evening": self._select_evening_activities(itinerary_data, weather),
            "restaurants": self._select_daily_restaurants(itinerary_data["restaurants"]),
            "llm_reasoning": schedule_result
        }
    
    def _select_morning_activities(self, itinerary_data: Dict[str, Any],
                                 weather: WeatherInfo, energy_level: str) -> List[str]:
        """Select appropriate morning activities"""
        morning_attractions = itinerary_data["attractions"]["morning_suitable"]
        
        # Weather-based selection
        if weather.precipitation_chance > 50:
            # Prefer indoor activities
            indoor_activities = [a for a in morning_attractions if "museum" in a.place_type.lower() or "gallery" in a.place_type.lower()]
            selected = indoor_activities[:2] if indoor_activities else morning_attractions[:2]
        else:
            # Mix of outdoor and indoor
            selected = morning_attractions[:2]
        
        return [f"{activity.name} ({self._estimate_duration(activity.place_type)} mins)" for activity in selected]
    
    def _select_afternoon_activities(self, itinerary_data: Dict[str, Any],
                                   weather: WeatherInfo, energy_level: str) -> List[str]:
        """Select appropriate afternoon activities"""
        afternoon_attractions = itinerary_data["attractions"]["afternoon_suitable"]
        
        # Energy level consideration
        if energy_level == "high":
            selected = afternoon_attractions[:3]  # More activities
        elif energy_level == "medium":
            selected = afternoon_attractions[:2]
        else:
            selected = afternoon_attractions[:1]  # Fewer activities when energy is low
        
        return [f"{activity.name} ({self._estimate_duration(activity.place_type)} mins)" for activity in selected]
    
    def _select_evening_activities(self, itinerary_data: Dict[str, Any],
                                 weather: WeatherInfo) -> List[str]:
        """Select appropriate evening activities"""
        evening_attractions = itinerary_data["attractions"]["evening_suitable"]
        
        # Usually lighter evening activities
        selected = evening_attractions[:2]
        
        return [f"{activity.name} ({self._estimate_duration(activity.place_type)} mins)" for activity in selected]
    
    def _select_daily_restaurants(self, restaurants: Dict[str, List]) -> List[PlaceRecommendation]:
        """Select restaurants for the day"""
        daily_restaurants = []
        
        # Select one from each meal category
        if restaurants["breakfast"]:
            daily_restaurants.append(restaurants["breakfast"][0])
        if restaurants["lunch"]:
            daily_restaurants.append(restaurants["lunch"][0])
        if restaurants["dinner"]:
            daily_restaurants.append(restaurants["dinner"][0])
        
        return daily_restaurants
    
    async def optimize_itinerary_flow(self, daily_plans: List[DailyPlan],
                                    itinerary_data: Dict[str, Any]) -> List[DailyPlan]:
        """
        Optimize the overall flow of the itinerary
        """
        self.log_action("Optimizing itinerary flow")
        
        # Apply optimization principles
        optimized_plans = []
        
        for i, plan in enumerate(daily_plans):
            optimized_plan = await self._optimize_single_day(plan, i + 1, len(daily_plans))
            optimized_plans.append(optimized_plan)
        
        return optimized_plans
    
    async def _optimize_single_day(self, daily_plan: DailyPlan,
                                 day_number: int, total_days: int) -> DailyPlan:
        """Optimize a single day's itinerary"""
        
        # Apply day-specific optimizations
        if day_number == 1:
            # First day: lighter schedule to adjust
            daily_plan.morning_activities = daily_plan.morning_activities[:1]
        elif day_number == total_days:
            # Last day: account for departure
            daily_plan.evening_activities = ["Pack and prepare for departure"]
        
        # Weather-based optimizations
        if daily_plan.weather.precipitation_chance > 60:
            # Rainy day: prioritize indoor activities
            daily_plan.morning_activities = [
                activity for activity in daily_plan.morning_activities
                if not any(keyword in activity.lower() for keyword in ["park", "garden", "outdoor"])
            ]
        
        return daily_plan
    
    async def create_itinerary_summary(self, daily_plans: List[DailyPlan],
                                     travel_request, itinerary_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive itinerary summary
        """
        self.log_action("Creating itinerary summary")
        
        # Calculate totals
        total_activities = sum(
            len(plan.morning_activities) + len(plan.afternoon_activities) + len(plan.evening_activities)
            for plan in daily_plans
        )
        
        total_restaurants = sum(len(plan.recommended_restaurants) for plan in daily_plans)
        
        # Estimate costs
        estimated_costs = self._calculate_estimated_costs(daily_plans, itinerary_data)
        
        # Activity distribution
        activity_distribution = self._analyze_activity_distribution(daily_plans)
        
        summary = {
            "trip_overview": {
                "destination": travel_request.destination,
                "duration": len(daily_plans),
                "total_activities": total_activities,
                "total_restaurants": total_restaurants
            },
            "cost_breakdown": estimated_costs,
            "activity_distribution": activity_distribution,
            "weather_adaptations": self._count_weather_adaptations(daily_plans),
            "pacing_analysis": self._analyze_pacing(daily_plans),
            "recommendations": [
                "Review each day's activities and adjust timing as needed",
                "Book popular attractions in advance",
                "Check opening hours before visiting",
                "Keep some flexibility for spontaneous discoveries"
            ]
        }
        
        return summary
    
    async def generate_optimization_notes(self, daily_plans: List[DailyPlan]) -> List[str]:
        """Generate notes about itinerary optimizations"""
        notes = []
        
        # Check for potential issues
        for i, plan in enumerate(daily_plans):
            day_num = i + 1
            
            # Check activity intensity
            activity_count = len(plan.morning_activities) + len(plan.afternoon_activities) + len(plan.evening_activities)
            if activity_count > 6:
                notes.append(f"Day {day_num}: Consider reducing activities to avoid fatigue")
            
            # Check weather adaptations
            if plan.weather.precipitation_chance > 50:
                indoor_count = sum(
                    1 for activities in [plan.morning_activities, plan.afternoon_activities, plan.evening_activities]
                    for activity in activities
                    if any(keyword in activity.lower() for keyword in ["museum", "gallery", "indoor"])
                )
                if indoor_count < 2:
                    notes.append(f"Day {day_num}: Consider more indoor options due to rain forecast")
        
        return notes
    
    def _categorize_attractions_by_time(self, attractions: List[PlaceRecommendation]) -> Dict[str, List[PlaceRecommendation]]:
        """Categorize attractions by optimal visit time"""
        categorized = {
            "morning": [],
            "afternoon": [],
            "evening": [],
            "flexible": []
        }
        
        for attraction in attractions:
            place_type = attraction.place_type.lower()
            
            # Time-based categorization logic
            if any(keyword in place_type for keyword in ["park", "garden", "outdoor"]):
                categorized["morning"].append(attraction)
            elif any(keyword in place_type for keyword in ["museum", "gallery"]):
                categorized["afternoon"].append(attraction)
            elif any(keyword in place_type for keyword in ["entertainment", "theater", "nightlife"]):
                categorized["evening"].append(attraction)
            else:
                categorized["flexible"].append(attraction)
        
        # Sort by rating within each category
        for category in categorized:
            categorized[category].sort(key=lambda x: x.rating, reverse=True)
        
        return categorized
    
    def _rank_restaurants_by_meal_type(self, restaurants: List[PlaceRecommendation]) -> Dict[str, List[PlaceRecommendation]]:
        """Rank restaurants by meal type"""
        # Sort all restaurants by rating
        sorted_restaurants = sorted(restaurants, key=lambda x: x.rating, reverse=True)
        
        # Distribute across meal types (simplified logic)
        total = len(sorted_restaurants)
        
        return {
            "breakfast": sorted_restaurants[:total//3] if total > 3 else sorted_restaurants,
            "lunch": sorted_restaurants[total//3:2*total//3] if total > 3 else sorted_restaurants,
            "dinner": sorted_restaurants[2*total//3:] if total > 3 else sorted_restaurants
        }
    
    def _get_weather_for_day(self, weather_forecast: List[WeatherInfo], day_index: int) -> WeatherInfo:
        """Get weather for specific day or return default"""
        if day_index < len(weather_forecast):
            return weather_forecast[day_index]
        
        # Return default weather if not available
        return WeatherInfo(
            date=datetime.now().strftime("%Y-%m-%d"),
            temperature_high=22.0,
            temperature_low=15.0,
            description="Partly cloudy",
            humidity=60,
            wind_speed=10.0,
            precipitation_chance=20
        )
    
    def _determine_day_theme(self, day_number: int, total_days: int) -> str:
        """Determine theme for the day"""
        if day_number == 1:
            return "arrival_and_orientation"
        elif day_number == total_days:
            return "departure_preparation"
        elif day_number <= total_days // 2:
            return "exploration_and_discovery"
        else:
            return "deep_dive_and_favorites"
    
    def _calculate_energy_level(self, day_number: int) -> str:
        """Calculate expected energy level for the day"""
        if day_number <= 2:
            return "high"
        elif day_number <= 4:
            return "medium"
        else:
            return "medium-low"
    
    def _estimate_duration(self, place_type: str) -> int:
        """Estimate visit duration for place type"""
        return ACTIVITY_DURATIONS.get(place_type.lower(), 90)
    
    def _determine_budget_level(self, budget: float, duration: int) -> str:
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
    
    def _calculate_estimated_costs(self, daily_plans: List[DailyPlan],
                                 itinerary_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate estimated costs for the itinerary"""
        budget_level = itinerary_data["budget_level"]
        
        # Base daily costs by budget level
        daily_costs = {
            "budget": {"activities": 30, "meals": 40, "transport": 15},
            "mid_range": {"activities": 60, "meals": 80, "transport": 25},
            "luxury": {"activities": 120, "meals": 150, "transport": 40},
            "ultra_luxury": {"activities": 200, "meals": 250, "transport": 60},
            "unknown": {"activities": 50, "meals": 60, "transport": 20}
        }
        
        costs = daily_costs.get(budget_level, daily_costs["unknown"])
        
        total_days = len(daily_plans)
        
        return {
            "activities_total": costs["activities"] * total_days,
            "meals_total": costs["meals"] * total_days,
            "transport_total": costs["transport"] * total_days,
            "daily_average": sum(costs.values()),
            "trip_total": sum(costs.values()) * total_days,
            "currency": "USD"
        }
    
    def _analyze_activity_distribution(self, daily_plans: List[DailyPlan]) -> Dict[str, Any]:
        """Analyze distribution of activities across days"""
        total_morning = sum(len(plan.morning_activities) for plan in daily_plans)
        total_afternoon = sum(len(plan.afternoon_activities) for plan in daily_plans)
        total_evening = sum(len(plan.evening_activities) for plan in daily_plans)
        total_activities = total_morning + total_afternoon + total_evening
        
        return {
            "morning_activities": total_morning,
            "afternoon_activities": total_afternoon,
            "evening_activities": total_evening,
            "total_activities": total_activities,
            "average_per_day": total_activities / len(daily_plans) if daily_plans else 0,
            "distribution": {
                "morning_percentage": (total_morning / total_activities * 100) if total_activities > 0 else 0,
                "afternoon_percentage": (total_afternoon / total_activities * 100) if total_activities > 0 else 0,
                "evening_percentage": (total_evening / total_activities * 100) if total_activities > 0 else 0
            }
        }
    
    def _count_weather_adaptations(self, daily_plans: List[DailyPlan]) -> Dict[str, int]:
        """Count weather-based adaptations in the itinerary"""
        rainy_days = sum(1 for plan in daily_plans if plan.weather.precipitation_chance > 50)
        hot_days = sum(1 for plan in daily_plans if plan.weather.temperature_high > 30)
        cold_days = sum(1 for plan in daily_plans if plan.weather.temperature_low < 10)
        
        return {
            "rainy_day_adaptations": rainy_days,
            "hot_weather_adaptations": hot_days,
            "cold_weather_adaptations": cold_days,
            "total_weather_considerations": rainy_days + hot_days + cold_days
        }
    
    def _analyze_pacing(self, daily_plans: List[DailyPlan]) -> Dict[str, Any]:
        """Analyze the pacing of the itinerary"""
        activity_counts = [
            len(plan.morning_activities) + len(plan.afternoon_activities) + len(plan.evening_activities)
            for plan in daily_plans
        ]
        
        if not activity_counts:
            return {"status": "no_data"}
        
        avg_activities = sum(activity_counts) / len(activity_counts)
        max_activities = max(activity_counts)
        min_activities = min(activity_counts)
        
        # Determine pacing assessment
        if max_activities - min_activities <= 2:
            pacing_assessment = "well_balanced"
        elif max_activities > avg_activities + 2:
            pacing_assessment = "some_intense_days"
        else:
            pacing_assessment = "variable_intensity"
        
        return {
            "average_activities_per_day": avg_activities,
            "max_activities_day": max_activities,
            "min_activities_day": min_activities,
            "pacing_assessment": pacing_assessment,
            "intensity_variation": max_activities - min_activities
        }