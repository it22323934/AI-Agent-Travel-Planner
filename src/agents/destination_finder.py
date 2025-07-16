"""
Destination Finder Agent - Destination research and analysis specialist
Implements destination research capabilities using collected data
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime

from agents.base_agent import LLMAgent, DataProcessingAgent
from agents.prompts import get_agent_prompt, format_prompt
from core.models import PlaceRecommendation, WeatherInfo
from core.exceptions import AgentError
from core.constants import INTEREST_TO_PLACE_TYPES, ACTIVITY_DURATIONS


class DestinationFinder(LLMAgent):
    """
    Destination research agent that analyzes destinations and provides insights
    
    Responsibilities:
    - Research destination characteristics and highlights
    - Analyze available attractions and places
    - Match destination features to traveler interests
    - Provide cultural and practical insights
    - Recommend optimal timing and sequencing
    """
    
    def __init__(self):
        super().__init__(
            agent_name="destination_finder",
            system_prompt=get_agent_prompt("destination_finder"),
            reasoning_steps=[
                "Analyze destination data and available attractions",
                "Evaluate attraction quality and relevance to interests",
                "Identify cultural and seasonal considerations",
                "Assess destination suitability for travel requirements",
                "Provide strategic recommendations for exploration"
            ]
        )
        
        self.data_processor = DataProcessingAgent(
            "destination_data_processor",
            "Specialized in processing and filtering destination data"
        )
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for destination research
        """
        self.log_action("Starting destination research and analysis")
        
        # Validate input
        await self.validate_input(input_data, ["travel_request", "collected_data"])
        
        travel_request = input_data["travel_request"]
        collected_data = input_data["collected_data"]
        
        # Perform comprehensive destination analysis
        research_result = await self.research_destination(travel_request, collected_data)
        
        return {
            "destination_research": research_result,
            "agent_name": self.agent_name,
            "processing_time": (datetime.utcnow() - self.start_time).total_seconds(),
            "status": "completed"
        }
    
    async def research_destination(self, travel_request, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Conduct comprehensive destination research
        """
        self.log_action(f"Researching destination: {travel_request.destination}")
        
        # Analyze collected places data
        places_analysis = await self.analyze_places_data(
            collected_data.get("hotels", []),
            collected_data.get("restaurants", []),
            collected_data.get("attractions", []),
            travel_request.interests
        )
        
        # Analyze weather patterns
        weather_analysis = await self.analyze_weather_patterns(
            collected_data.get("weather", []),
            travel_request.start_date,
            travel_request.end_date
        )
        
        # Create destination insights
        destination_insights = await self.create_destination_insights(
            travel_request.destination,
            places_analysis,
            weather_analysis,
            travel_request.interests
        )
        
        # Generate recommendations
        recommendations = await self.generate_destination_recommendations(
            travel_request,
            places_analysis,
            weather_analysis
        )
        
        return {
            "destination": travel_request.destination,
            "places_analysis": places_analysis,
            "weather_analysis": weather_analysis,
            "destination_insights": destination_insights,
            "recommendations": recommendations,
            "research_timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_places_data(self, hotels: List[PlaceRecommendation], 
                                restaurants: List[PlaceRecommendation],
                                attractions: List[PlaceRecommendation],
                                interests: List[str]) -> Dict[str, Any]:
        """
        Analyze collected places data for quality and relevance
        """
        self.log_action("Analyzing places data")
        
        # Filter and rank places by quality
        quality_filters = {"rating": {"min": 3.0}}
        
        quality_hotels = await self.data_processor.process_and_filter_data(
            [hotel.__dict__ for hotel in hotels], quality_filters
        )
        
        quality_restaurants = await self.data_processor.process_and_filter_data(
            [restaurant.__dict__ for restaurant in restaurants], quality_filters
        )
        
        quality_attractions = await self.data_processor.process_and_filter_data(
            [attraction.__dict__ for attraction in attractions], quality_filters
        )
        
        # Analyze interest alignment
        interest_match_analysis = await self.analyze_interest_alignment(
            attractions, interests
        )
        
        # Create places summary
        places_summary = {
            "total_places": {
                "hotels": len(hotels),
                "restaurants": len(restaurants),
                "attractions": len(attractions)
            },
            "quality_places": {
                "hotels": len(quality_hotels),
                "restaurants": len(quality_restaurants),
                "attractions": len(quality_attractions)
            },
            "average_ratings": {
                "hotels": sum(h.rating for h in hotels) / len(hotels) if hotels else 0,
                "restaurants": sum(r.rating for r in restaurants) / len(restaurants) if restaurants else 0,
                "attractions": sum(a.rating for a in attractions) / len(attractions) if attractions else 0
            },
            "interest_alignment": interest_match_analysis
        }
        
        return places_summary
    
    async def analyze_interest_alignment(self, attractions: List[PlaceRecommendation], 
                                       interests: List[str]) -> Dict[str, Any]:
        """
        Analyze how well available attractions match user interests
        """
        self.log_action("Analyzing interest alignment")
        
        # Map user interests to place types
        expected_place_types = []
        for interest in interests:
            if interest.lower() in INTEREST_TO_PLACE_TYPES:
                expected_place_types.extend(INTEREST_TO_PLACE_TYPES[interest.lower()])
        
        # Analyze available attraction types
        available_types = [attraction.place_type for attraction in attractions]
        type_counts = {}
        for place_type in available_types:
            type_counts[place_type] = type_counts.get(place_type, 0) + 1
        
        # Calculate alignment score
        matched_types = set(expected_place_types) & set(available_types)
        alignment_score = len(matched_types) / len(expected_place_types) if expected_place_types else 0
        
        return {
            "user_interests": interests,
            "expected_place_types": expected_place_types,
            "available_place_types": list(type_counts.keys()),
            "matched_types": list(matched_types),
            "alignment_score": alignment_score,
            "missing_types": list(set(expected_place_types) - set(available_types)),
            "type_distribution": type_counts
        }
    
    async def analyze_weather_patterns(self, weather_forecast: List[WeatherInfo],
                                     start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Analyze weather patterns for the travel period
        """
        self.log_action("Analyzing weather patterns")
        
        if not weather_forecast:
            return {
                "status": "no_weather_data",
                "recommendation": "Check weather closer to travel dates"
            }
        
        # Calculate weather statistics
        temperatures_high = [w.temperature_high for w in weather_forecast]
        temperatures_low = [w.temperature_low for w in weather_forecast]
        precipitation_chances = [w.precipitation_chance for w in weather_forecast]
        
        weather_stats = {
            "average_high": sum(temperatures_high) / len(temperatures_high),
            "average_low": sum(temperatures_low) / len(temperatures_low),
            "max_temp": max(temperatures_high),
            "min_temp": min(temperatures_low),
            "average_precipitation_chance": sum(precipitation_chances) / len(precipitation_chances),
            "rainy_days": len([p for p in precipitation_chances if p > 50]),
            "total_days": len(weather_forecast)
        }
        
        # Assess weather suitability
        weather_suitability = await self.assess_weather_suitability(weather_stats, weather_forecast)
        
        return {
            "forecast_period": f"{start_date} to {end_date}",
            "weather_statistics": weather_stats,
            "daily_forecast": [
                {
                    "date": w.date,
                    "high": w.temperature_high,
                    "low": w.temperature_low,
                    "condition": w.description,
                    "rain_chance": w.precipitation_chance
                }
                for w in weather_forecast
            ],
            "suitability_assessment": weather_suitability
        }
    
    async def assess_weather_suitability(self, weather_stats: Dict[str, Any], 
                                       weather_forecast: List[WeatherInfo]) -> Dict[str, Any]:
        """
        Assess weather suitability for different activities
        """
        self.log_action("Assessing weather suitability")
        
        # Determine overall weather rating
        avg_temp = (weather_stats["average_high"] + weather_stats["average_low"]) / 2
        rain_probability = weather_stats["average_precipitation_chance"]
        
        # Weather suitability for different activity types
        outdoor_suitability = "excellent"
        if rain_probability > 60 or avg_temp < 5 or avg_temp > 35:
            outdoor_suitability = "poor"
        elif rain_probability > 30 or avg_temp < 10 or avg_temp > 30:
            outdoor_suitability = "fair"
        elif rain_probability > 15 or avg_temp < 15 or avg_temp > 25:
            outdoor_suitability = "good"
        
        return {
            "overall_rating": outdoor_suitability,
            "outdoor_activities_suitable": outdoor_suitability in ["good", "excellent"],
            "indoor_activities_recommended": weather_stats["rainy_days"] > 2,
            "temperature_comfortable": 15 <= avg_temp <= 25,
            "clothing_recommendations": self._get_clothing_recommendations(avg_temp, rain_probability),
            "best_weather_days": [
                w.date for w in weather_forecast 
                if w.precipitation_chance < 30 and 15 <= (w.temperature_high + w.temperature_low) / 2 <= 25
            ],
            "challenging_weather_days": [
                w.date for w in weather_forecast
                if w.precipitation_chance > 60 or w.temperature_high > 30 or w.temperature_low < 5
            ]
        }
    
    async def create_destination_insights(self, destination: str, 
                                        places_analysis: Dict[str, Any],
                                        weather_analysis: Dict[str, Any],
                                        interests: List[str]) -> Dict[str, Any]:
        """
        Create comprehensive destination insights using LLM analysis
        """
        self.log_action("Creating destination insights")
        
        # Prepare insight generation prompt
        insights_prompt = f"""
        Create comprehensive destination insights for travel planning:
        
        Destination: {destination}
        Traveler Interests: {', '.join(interests)}
        
        Available Data Analysis:
        - Total attractions found: {places_analysis['total_places']['attractions']}
        - Quality attractions (>3.0 rating): {places_analysis['quality_places']['attractions']}
        - Interest alignment score: {places_analysis['interest_alignment']['alignment_score']:.2f}
        - Weather suitability: {weather_analysis.get('suitability_assessment', {}).get('overall_rating', 'unknown')}
        
        Provide insights on:
        1. Destination highlights and unique characteristics
        2. How well the destination matches the traveler's interests
        3. Best strategies for exploring the destination
        4. Cultural considerations and local customs
        5. Optimal timing and sequencing recommendations
        6. Any limitations or considerations to be aware of
        
        Focus on actionable insights for trip planning.
        """
        
        context_data = {
            "destination": destination,
            "places_analysis": places_analysis,
            "weather_analysis": weather_analysis,
            "interests": interests
        }
        
        insights_result = await self.query_ollama(insights_prompt, context_data)
        
        return {
            "destination": destination,
            "insights_summary": insights_result,
            "data_quality_score": self._calculate_data_quality_score(places_analysis),
            "research_confidence": self._assess_research_confidence(places_analysis, weather_analysis),
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def generate_destination_recommendations(self, travel_request,
                                                 places_analysis: Dict[str, Any],
                                                 weather_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate specific recommendations for the destination
        """
        self.log_action("Generating destination recommendations")
        
        recommendations = {
            "priority_recommendations": [],
            "activity_timing": {},
            "practical_tips": [],
            "weather_considerations": []
        }
        
        # Priority recommendations based on interest alignment
        alignment_score = places_analysis["interest_alignment"]["alignment_score"]
        if alignment_score > 0.7:
            recommendations["priority_recommendations"].append("Excellent match for your interests - focus on top-rated attractions")
        elif alignment_score > 0.4:
            recommendations["priority_recommendations"].append("Good destination match - some adaptation of expectations may be needed")
        else:
            recommendations["priority_recommendations"].append("Consider broadening interests or exploring alternative activities")
        
        # Weather-based recommendations
        weather_assessment = weather_analysis.get("suitability_assessment", {})
        if weather_assessment.get("indoor_activities_recommended"):
            recommendations["weather_considerations"].append("Plan indoor alternatives for rainy days")
        
        if weather_assessment.get("best_weather_days"):
            recommendations["weather_considerations"].append(
                f"Optimal weather on: {', '.join(weather_assessment['best_weather_days'][:3])}"
            )
        
        # Activity timing recommendations
        recommendations["activity_timing"] = {
            "morning": "Outdoor attractions and sightseeing",
            "afternoon": "Museums and indoor activities during peak heat",
            "evening": "Dining and cultural experiences"
        }
        
        # Practical tips
        recommendations["practical_tips"] = [
            "Book popular attractions in advance",
            "Consider local transportation options",
            "Research local customs and etiquette",
            "Check opening hours and seasonal closures"
        ]
        
        return recommendations
    
    def _get_clothing_recommendations(self, avg_temp: float, rain_probability: float) -> List[str]:
        """Get clothing recommendations based on weather"""
        recommendations = []
        
        if avg_temp < 10:
            recommendations.append("Warm clothing and layers")
        elif avg_temp < 20:
            recommendations.append("Light layers and comfortable walking shoes")
        else:
            recommendations.append("Light, breathable clothing")
        
        if rain_probability > 30:
            recommendations.append("Rain gear or umbrella")
        
        return recommendations
    
    def _calculate_data_quality_score(self, places_analysis: Dict[str, Any]) -> float:
        """Calculate data quality score based on available information"""
        total_places = sum(places_analysis["total_places"].values())
        quality_places = sum(places_analysis["quality_places"].values())
        
        if total_places == 0:
            return 0.0
        
        quality_ratio = quality_places / total_places
        data_coverage = min(total_places / 50, 1.0)  # Normalize to 50 places as "full coverage"
        
        return (quality_ratio * 0.6 + data_coverage * 0.4)
    
    def _assess_research_confidence(self, places_analysis: Dict[str, Any], 
                                  weather_analysis: Dict[str, Any]) -> str:
        """Assess confidence level in research results"""
        data_quality = self._calculate_data_quality_score(places_analysis)
        has_weather = weather_analysis.get("status") != "no_weather_data"
        alignment_score = places_analysis["interest_alignment"]["alignment_score"]
        
        confidence_factors = [
            data_quality > 0.7,
            has_weather,
            alignment_score > 0.5,
            places_analysis["total_places"]["attractions"] > 10
        ]
        
        confidence_score = sum(confidence_factors) / len(confidence_factors)
        
        if confidence_score > 0.8:
            return "high"
        elif confidence_score > 0.6:
            return "medium"
        else:
            return "low"