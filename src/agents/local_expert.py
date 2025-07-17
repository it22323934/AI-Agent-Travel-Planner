"""
Local Expert Agent - Provides insider knowledge and local optimization
Implements local expertise and practical travel insights
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


class LocalExpert(LLMAgent):
    """
    Local expert agent that provides insider knowledge and optimization
    
    Responsibilities:
    - Provide authentic local insights and recommendations
    - Optimize timing for attractions and activities
    - Suggest hidden gems and local favorites
    - Share practical transportation and logistics advice
    - Adapt recommendations based on weather and seasons
    """
    
    def __init__(self):
        super().__init__(
            agent_name="local_expert",
            system_prompt=get_agent_prompt("local_expert"),
            reasoning_steps=[
                "Analyze local context and seasonal considerations",
                "Identify optimal timing for attractions and activities",
                "Evaluate transportation and logistics requirements",
                "Consider local customs and practical constraints",
                "Provide insider recommendations and hidden gems"
            ]
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for local expertise
        """
        self.log_action("Starting local expertise analysis")
        
        # Validate input
        await self.validate_input(input_data, ["travel_request", "collected_data", "destination_research"])
        
        travel_request = input_data["travel_request"]
        collected_data = input_data["collected_data"]
        destination_research = input_data["destination_research"]
        
        # Perform local expertise analysis
        expertise_result = await self.provide_local_expertise(
            travel_request, collected_data, destination_research
        )
        
        return {
            "local_expertise": expertise_result,
            "agent_name": self.agent_name,
            "processing_time": (datetime.utcnow() - self.start_time).total_seconds(),
            "status": "completed"
        }
    
    async def provide_local_expertise(self, travel_request, collected_data: Dict[str, Any],
                                    destination_research: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide comprehensive local expertise and insights
        """
        self.log_action(f"Providing local expertise for {travel_request.destination}")
        
        # Analyze timing optimization opportunities
        timing_optimization = await self.optimize_attraction_timing(
            collected_data.get("attractions", []),
            collected_data.get("weather", []),
            travel_request.start_date,
            travel_request.end_date
        )
        
        # Provide transportation insights
        transportation_insights = await self.analyze_transportation_options(
            travel_request.destination,
            collected_data.get("attractions", []),
            getattr(travel_request, 'duration', 1)
        )
        
        # Generate local recommendations
        local_recommendations = await self.generate_local_recommendations(
            travel_request,
            collected_data,
            destination_research
        )
        
        # Provide practical tips
        practical_tips = await self.provide_practical_tips(
            travel_request.destination,
            travel_request.start_date,
            collected_data.get("weather", [])
        )
        
        # Cultural insights
        cultural_insights = await self.provide_cultural_insights(
            travel_request.destination,
            travel_request.interests
        )
        
        return {
            "destination": travel_request.destination,
            "timing_optimization": timing_optimization,
            "transportation_insights": transportation_insights,
            "local_recommendations": local_recommendations,
            "practical_tips": practical_tips,
            "cultural_insights": cultural_insights,
            "expertise_confidence": self._assess_expertise_confidence(collected_data),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def optimize_attraction_timing(self, attractions: List[PlaceRecommendation],
                                       weather_forecast: List[WeatherInfo],
                                       start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Optimize timing for attractions based on weather and crowd patterns
        """
        self.log_action("Optimizing attraction timing")
        
        # Categorize attractions by type
        attraction_categories = self._categorize_attractions(attractions)
        
        # Create timing recommendations based on weather
        weather_based_timing = self._create_weather_based_timing(
            attraction_categories, weather_forecast
        )
        
        # Generate crowd avoidance strategies
        crowd_strategies = await self._generate_crowd_strategies(attractions)
        
        # Create optimal visit times
        optimal_timing = await self._create_optimal_timing_recommendations(
            attractions, weather_forecast
        )
        
        return {
            "attraction_categories": attraction_categories,
            "weather_based_timing": weather_based_timing,
            "crowd_avoidance": crowd_strategies,
            "optimal_timing": optimal_timing,
            "timing_principles": [
                "Visit outdoor attractions during best weather",
                "Plan indoor activities for rainy periods",
                "Start early to avoid crowds at popular sites",
                "Save evening activities for cultural experiences"
            ]
        }
    
    async def analyze_transportation_options(self, destination: str,
                                           attractions: List[PlaceRecommendation],
                                           duration: int) -> Dict[str, Any]:
        """
        Analyze transportation options and provide logistics insights
        """
        self.log_action("Analyzing transportation options")
        
        # Create transportation analysis prompt
        transport_prompt = f"""
        Analyze transportation options for this destination:
        
        Destination: {destination}
        Trip Duration: {duration} days
        Number of Attractions: {len(attractions)}
        
        Sample Attractions and Locations:
        {json.dumps([{"name": a.name, "address": a.address} for a in attractions[:5]], indent=2)}
        
        Provide analysis of:
        1. Best transportation methods for getting around
        2. Cost estimates for different transportation options
        3. Transportation passes or deals available
        4. Walking vs. public transport recommendations
        5. Areas where rideshare/taxi might be necessary
        6. Transportation timing considerations
        
        Focus on practical, cost-effective recommendations.
        """
        
        context_data = {
            "destination": destination,
            "duration": duration,
            "attractions_count": len(attractions),
            "sample_locations": [a.address for a in attractions[:10]]
        }
        
        transport_analysis = await self.query_ollama(transport_prompt, context_data)
        
        # Generate specific recommendations
        transport_recommendations = {
            "primary_method": "public_transport",  # Default recommendation
            "secondary_method": "walking",
            "cost_estimate_per_day": self._estimate_transport_costs(destination, duration),
            "recommended_passes": [],
            "walking_friendly_areas": [],
            "transport_apps": ["Google Maps", "Local transit apps"],
            "analysis": transport_analysis
        }
        
        return transport_recommendations
    
    async def generate_local_recommendations(self, travel_request,
                                           collected_data: Dict[str, Any],
                                           destination_research: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate local recommendations including hidden gems
        """
        self.log_action("Generating local recommendations")
        
        # Create local recommendations prompt
        local_prompt = f"""
        Provide local expert recommendations for this trip:
        
        Destination: {travel_request.destination}
        Traveler Interests: {', '.join(travel_request.interests)}
        Trip Duration: {getattr(travel_request, 'duration', 1)} days
        Budget Level: {self._determine_budget_level(travel_request.budget, getattr(travel_request, 'duration', 1))}
        
        Available Attractions: {len(collected_data.get('attractions', []))}
        Available Restaurants: {len(collected_data.get('restaurants', []))}
        
        Provide recommendations for:
        1. Hidden gems and local favorites not in typical guides
        2. Best local restaurants and food experiences
        3. Authentic cultural experiences and events
        4. Local markets, neighborhoods worth exploring
        5. Seasonal activities and events during travel dates
        6. Local etiquette and customs to be aware of
        7. Money-saving tips and local deals
        8. What to avoid or be cautious about
        
        Focus on authentic, insider knowledge that enhances the experience.
        """
        
        context_data = {
            "destination": travel_request.destination,
            "interests": travel_request.interests,
            "duration": getattr(travel_request, 'duration', 1),
            "budget_level": self._determine_budget_level(travel_request.budget, getattr(travel_request, 'duration', 1)),
            "available_data": {
                "attractions": len(collected_data.get('attractions', [])),
                "restaurants": len(collected_data.get('restaurants', [])),
                "hotels": len(collected_data.get('hotels', []))
            }
        }
        
        local_insights = await self.query_ollama(local_prompt, context_data)
        
        # Structure the recommendations
        recommendations = {
            "hidden_gems": await self._identify_hidden_gems(collected_data.get('attractions', [])),
            "local_dining": await self._recommend_local_dining(collected_data.get('restaurants', [])),
            "cultural_experiences": [],
            "neighborhoods": [],
            "seasonal_activities": [],
            "local_tips": [],
            "expert_insights": local_insights
        }
        
        return recommendations
    
    async def provide_practical_tips(self, destination: str, start_date: str,
                                   weather_forecast: List[WeatherInfo]) -> Dict[str, Any]:
        """
        Provide practical travel tips for the destination
        """
        self.log_action("Providing practical tips")
        
        # Seasonal considerations
        travel_date = datetime.fromisoformat(start_date)
        season = self._determine_season(travel_date.month)
        
        # Weather-based tips
        weather_tips = []
        if weather_forecast:
            avg_temp = sum(w.temperature_high + w.temperature_low for w in weather_forecast) / (2 * len(weather_forecast))
            avg_rain = sum(w.precipitation_chance for w in weather_forecast) / len(weather_forecast)
            
            if avg_rain > 40:
                weather_tips.append("Pack waterproof clothing and plan indoor backup activities")
            if avg_temp < 10:
                weather_tips.append("Bring warm layers and consider indoor attractions during cold spells")
            if avg_temp > 30:
                weather_tips.append("Stay hydrated and plan activities during cooler parts of the day")
        
        practical_tips = {
            "season": season,
            "weather_tips": weather_tips,
            "packing_essentials": self._get_packing_essentials(destination, season, weather_forecast),
            "money_tips": [
                "Notify bank of travel plans",
                "Research local tipping customs",
                "Consider local payment methods",
                "Keep emergency cash in local currency"
            ],
            "safety_tips": [
                "Keep copies of important documents",
                "Research local emergency numbers",
                "Be aware of common tourist scams",
                "Trust your instincts in unfamiliar areas"
            ],
            "communication_tips": [
                "Download offline maps",
                "Learn basic local phrases",
                "Consider local SIM card or roaming plan",
                "Save important contacts and addresses"
            ],
            "health_tips": [
                "Check if vaccinations are needed",
                "Pack basic first aid supplies",
                "Research local healthcare options",
                "Consider travel insurance"
            ]
        }
        
        return practical_tips
    
    async def provide_cultural_insights(self, destination: str, interests: List[str]) -> Dict[str, Any]:
        """
        Provide cultural insights and etiquette guidance
        """
        self.log_action("Providing cultural insights")
        
        # Create cultural insights prompt
        cultural_prompt = f"""
        Provide cultural insights and etiquette guidance for:
        
        Destination: {destination}
        Traveler Interests: {', '.join(interests)}
        
        Cover these aspects:
        1. Local customs and etiquette do's and don'ts
        2. Appropriate dress codes for different venues
        3. Dining etiquette and local food customs
        4. Greeting customs and social interactions
        5. Religious or cultural sites protocol
        6. Tipping practices and service expectations
        7. Business hours and local rhythms
        8. Festivals or cultural events to be aware of
        
        Focus on practical advice to help travelers show respect and avoid misunderstandings.
        """
        
        context_data = {
            "destination": destination,
            "interests": interests
        }
        
        cultural_analysis = await self.query_ollama(cultural_prompt, context_data)
        
        cultural_insights = {
            "cultural_overview": cultural_analysis,
            "etiquette_highlights": [
                "Research local greeting customs",
                "Understand tipping expectations",
                "Respect dress codes at religious sites",
                "Be mindful of photography restrictions"
            ],
            "cultural_sensitivity": [
                "Learn about local values and beliefs",
                "Show respect for traditions and customs", 
                "Be patient with language barriers",
                "Observe and follow local behavior cues"
            ],
            "interaction_tips": [
                "Smile and be friendly",
                "Learn basic phrases in local language",
                "Be patient and understanding",
                "Show genuine interest in local culture"
            ]
        }
        
        return cultural_insights
    
    def _categorize_attractions(self, attractions: List[PlaceRecommendation]) -> Dict[str, List[str]]:
        """Categorize attractions by type for timing optimization"""
        categories = {
            "outdoor": [],
            "indoor": [],
            "museums": [],
            "religious": [],
            "entertainment": []
        }
        
        for attraction in attractions:
            place_type = attraction.place_type.lower()
            name = attraction.name
            
            if any(keyword in place_type for keyword in ["park", "garden", "outdoor"]):
                categories["outdoor"].append(name)
            elif any(keyword in place_type for keyword in ["museum", "gallery"]):
                categories["museums"].append(name)
            elif any(keyword in place_type for keyword in ["church", "temple", "mosque", "synagogue"]):
                categories["religious"].append(name)
            elif any(keyword in place_type for keyword in ["theater", "cinema", "entertainment"]):
                categories["entertainment"].append(name)
            else:
                categories["indoor"].append(name)
        
        return categories
    
    def _create_weather_based_timing(self, attraction_categories: Dict[str, List[str]],
                                   weather_forecast: List[WeatherInfo]) -> Dict[str, Any]:
        """Create timing recommendations based on weather"""
        weather_timing = {
            "good_weather_days": [],
            "indoor_activity_days": [],
            "flexible_days": []
        }
        
        for weather in weather_forecast:
            if weather.precipitation_chance < 20 and 15 <= (weather.temperature_high + weather.temperature_low) / 2 <= 25:
                weather_timing["good_weather_days"].append({
                    "date": weather.date,
                    "recommended": "outdoor attractions, walking tours, parks"
                })
            elif weather.precipitation_chance > 50:
                weather_timing["indoor_activity_days"].append({
                    "date": weather.date,
                    "recommended": "museums, galleries, shopping, indoor dining"
                })
            else:
                weather_timing["flexible_days"].append({
                    "date": weather.date,
                    "recommended": "mix of indoor and outdoor with backup plans"
                })
        
        return weather_timing
    
    async def _generate_crowd_strategies(self, attractions: List[PlaceRecommendation]) -> Dict[str, Any]:
        """Generate strategies for avoiding crowds"""
        return {
            "early_morning": "Visit popular outdoor attractions at opening time",
            "late_afternoon": "Museums and galleries are often less crowded before closing",
            "weekday_preference": "If possible, visit major attractions on weekdays",
            "lunch_timing": "Many attractions are less crowded during lunch hours (12-2 PM)",
            "booking_advice": "Book timed entries for popular attractions in advance",
            "alternative_timing": "Consider visiting popular sites during dinner time if they're open late"
        }
    
    async def _create_optimal_timing_recommendations(self, attractions: List[PlaceRecommendation],
                                                   weather_forecast: List[WeatherInfo]) -> Dict[str, Any]:
        """Create optimal timing recommendations for specific attractions"""
        timing_recommendations = {}
        
        for attraction in attractions[:10]:  # Top 10 attractions
            optimal_time = "morning"  # Default
            
            # Determine optimal time based on attraction type
            place_type = attraction.place_type.lower()
            if "museum" in place_type or "gallery" in place_type:
                optimal_time = "afternoon"
            elif "park" in place_type or "outdoor" in place_type:
                optimal_time = "morning"
            elif "restaurant" in place_type:
                optimal_time = "evening"
            
            timing_recommendations[attraction.name] = {
                "optimal_time": optimal_time,
                "estimated_duration": ACTIVITY_DURATIONS.get(place_type.split()[0], 60),
                "weather_dependent": place_type in ["park", "outdoor", "garden"],
                "booking_required": attraction.rating > 4.5  # High-rated attractions likely need booking
            }
        
        return timing_recommendations
    
    async def _identify_hidden_gems(self, attractions: List[PlaceRecommendation]) -> List[Dict[str, Any]]:
        """Identify potential hidden gems from attraction data"""
        hidden_gems = []
        
        # Look for highly rated but lesser-known places
        for attraction in attractions:
            if attraction.rating >= 4.0 and attraction.rating < 4.5:  # Good but not overly popular
                hidden_gems.append({
                    "name": attraction.name,
                    "type": attraction.place_type,
                    "rating": attraction.rating,
                    "reason": "Highly rated local favorite"
                })
        
        return hidden_gems[:5]  # Top 5 hidden gems
    
    async def _recommend_local_dining(self, restaurants: List[PlaceRecommendation]) -> List[Dict[str, Any]]:
        """Recommend local dining experiences"""
        dining_recommendations = []
        
        # Categorize restaurants by price level
        budget_friendly = [r for r in restaurants if r.price_level <= 2]
        mid_range = [r for r in restaurants if r.price_level == 3]
        upscale = [r for r in restaurants if r.price_level >= 4]
        
        # Recommend from each category
        if budget_friendly:
            top_budget = max(budget_friendly, key=lambda x: x.rating)
            dining_recommendations.append({
                "name": top_budget.name,
                "category": "budget_friendly",
                "rating": top_budget.rating,
                "price_level": top_budget.price_level
            })
        
        if mid_range:
            top_mid = max(mid_range, key=lambda x: x.rating)
            dining_recommendations.append({
                "name": top_mid.name,
                "category": "mid_range",
                "rating": top_mid.rating,
                "price_level": top_mid.price_level
            })
        
        return dining_recommendations
    
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
    
    def _determine_season(self, month: int) -> str:
        """Determine season based on month"""
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "autumn"
    
    def _get_packing_essentials(self, destination: str, season: str,
                              weather_forecast: List[WeatherInfo]) -> List[str]:
        """Get packing essentials based on destination and weather"""
        essentials = ["comfortable walking shoes", "phone charger", "camera"]
        
        if season == "winter":
            essentials.extend(["warm clothing", "waterproof jacket", "gloves"])
        elif season == "summer":
            essentials.extend(["sunscreen", "hat", "light clothing", "water bottle"])
        
        if weather_forecast and any(w.precipitation_chance > 40 for w in weather_forecast):
            essentials.append("umbrella or rain jacket")
        
        return essentials
    
    def _estimate_transport_costs(self, destination: str, duration: int) -> Dict[str, float]:
        """Estimate transportation costs (simplified)"""
        # This would be more sophisticated in production
        base_daily_cost = 15.0  # USD
        
        return {
            "public_transport_daily": base_daily_cost,
            "taxi_rideshare_daily": base_daily_cost * 3,
            "walking": 0.0,
            "total_estimated": base_daily_cost * duration
        }
    
    def _assess_expertise_confidence(self, collected_data: Dict[str, Any]) -> str:
        """Assess confidence in local expertise recommendations"""
        data_points = sum([
            len(collected_data.get("attractions", [])),
            len(collected_data.get("restaurants", [])),
            len(collected_data.get("weather", []))
        ])
        
        if data_points > 50:
            return "high"
        elif data_points > 20:
            return "medium"
        else:
            return "low"