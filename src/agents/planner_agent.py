"""
Planner Agent - Main coordination agent for travel planning
Implements the Planning pillar of the multi-agent system
"""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta

from agents.base_agent import LLMAgent
from agents.prompts import get_agent_prompt, format_prompt
from core.models import TravelRequest, TaskStatus
from core.exceptions import AgentError, ValidationError
from core.constants import BUDGET_RANGES, INTEREST_TO_PLACE_TYPES


class PlannerAgent(LLMAgent):
    """
    Main planning agent that coordinates the entire travel planning workflow
    
    Responsibilities:
    - Validate and analyze travel requests
    - Create comprehensive planning strategies
    - Coordinate workflow execution
    - Ensure requirements are met within constraints
    """
    
    def __init__(self):
        super().__init__(
            agent_name="planner",
            system_prompt=get_agent_prompt("planner"),
            reasoning_steps=[
                "Analyze destination feasibility and characteristics",
                "Assess budget requirements and realistic expectations",
                "Identify activity categories based on traveler interests",
                "Create structured timeline and coordination strategy",
                "Identify potential challenges and mitigation approaches"
            ]
        )
        
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main processing method for the planner agent
        """
        self.log_action("Starting travel planning analysis")
        
        # Validate input
        await self.validate_input(input_data, ["travel_request"])
        travel_request = input_data["travel_request"]
        
        # Perform comprehensive planning analysis
        planning_result = await self.create_planning_strategy(travel_request)
        
        return {
            "planning_strategy": planning_result,
            "agent_name": self.agent_name,
            "processing_time": (datetime.utcnow() - self.start_time).total_seconds(),
            "status": "completed"
        }
    
    async def create_planning_strategy(self, travel_request: TravelRequest) -> Dict[str, Any]:
        """
        Create comprehensive planning strategy for the travel request
        """
        self.log_action("Creating planning strategy")
        
        # Validate travel request
        validation_result = await self.validate_travel_request(travel_request)
        if not validation_result["is_valid"]:
            raise ValidationError(f"Invalid travel request: {validation_result['issues']}")
        
        # Analyze destination and requirements
        destination_analysis = await self.analyze_destination_requirements(travel_request)
        
        # Assess budget feasibility
        budget_analysis = await self.analyze_budget_feasibility(travel_request)
        
        # Create activity plan
        activity_plan = await self.create_activity_plan(travel_request)
        
        # Identify challenges and risks
        risk_assessment = await self.assess_risks_and_challenges(travel_request)
        
        # Create coordination strategy
        coordination_strategy = await self.create_coordination_strategy(travel_request)
        
        # Combine all analyses into comprehensive strategy
        planning_strategy = {
            "destination_analysis": destination_analysis,
            "budget_analysis": budget_analysis,
            "activity_plan": activity_plan,
            "risk_assessment": risk_assessment,
            "coordination_strategy": coordination_strategy,
            "validation_result": validation_result,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.log_action("Planning strategy created successfully")
        return planning_strategy
    
    async def validate_travel_request(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Validate travel request for feasibility and completeness
        """
        self.log_action("Validating travel request")
        
        issues = []
        warnings = []
        
        # Basic validation
        if not request.destination or len(request.destination.strip()) < 3:
            issues.append("Destination must be specified and at least 3 characters")
        
        # Date validation
        try:
            start_date = datetime.fromisoformat(request.start_date)
            end_date = datetime.fromisoformat(request.end_date)
            duration = (end_date - start_date).days
            
            if duration < 1:
                issues.append("Trip duration must be at least 1 day")
            elif duration > 30:
                issues.append("Trip duration cannot exceed 30 days")
            elif duration > 14:
                warnings.append("Long trips (>14 days) may require more detailed planning")
                
        except ValueError as e:
            issues.append(f"Invalid date format: {e}")
        
        # Budget validation
        if request.budget is not None:
            if request.budget < 0:
                issues.append("Budget cannot be negative")
            elif request.budget < 50 * getattr(request, 'duration', 1):
                warnings.append("Budget may be insufficient for destination and duration")
        else:
            warnings.append("No budget specified - recommendations may not be cost-optimized")
        
        # Interests validation
        if not request.interests:
            warnings.append("No interests specified - will use general recommendations")
        else:
            unknown_interests = [
                interest for interest in request.interests 
                if interest.lower() not in INTEREST_TO_PLACE_TYPES
            ]
            if unknown_interests:
                warnings.append(f"Unknown interests may have limited recommendations: {unknown_interests}")
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    
    async def analyze_destination_requirements(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Analyze destination-specific requirements and characteristics
        """
        self.log_action(f"Analyzing destination requirements for {request.destination}")
        
        # Create prompt for destination analysis
        analysis_prompt = f"""
        Analyze this travel destination for planning purposes:
        
        Destination: {request.destination}
        Travel Dates: {request.start_date} to {request.end_date}
        Duration: {getattr(request, 'duration', 0)} days
        Traveler Interests: {', '.join(request.interests)}
        
        Provide analysis covering:
        1. Destination overview and key characteristics
        2. Seasonal considerations for the travel dates
        3. Major attractions and activity types available
        4. Transportation and logistics considerations
        5. Cultural or practical considerations for travelers
        
        Focus on information relevant for trip planning.
        """
        
        context_data = {
            "destination": request.destination,
            "travel_period": f"{request.start_date} to {request.end_date}",
            "interests": request.interests,
            "duration": getattr(request, 'duration', 0)
        }
        
        analysis_result = await self.query_ollama(analysis_prompt, context_data)
        
        return {
            "destination": request.destination,
            "analysis": analysis_result,
            "travel_period": f"{request.start_date} to {request.end_date}",
            "duration": getattr(request, 'duration', 0),
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    async def analyze_budget_feasibility(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Analyze budget feasibility and provide recommendations
        """
        self.log_action("Analyzing budget feasibility")
        
        if not request.budget:
            return {
                "budget_specified": False,
                "recommendation": "Budget not specified - will provide general recommendations",
                "budget_category": "unknown"
            }
        
        duration = getattr(request, 'duration', 1)
        daily_budget = request.budget / duration
        
        # Determine budget category
        budget_category = "ultra_luxury"
        for category, (min_val, max_val) in BUDGET_RANGES.items():
            if min_val <= daily_budget <= max_val:
                budget_category = category
                break
        
        # Create budget analysis prompt
        budget_prompt = f"""
        Analyze budget feasibility for this trip:
        
        Total Budget: ${request.budget}
        Duration: {duration} days
        Daily Budget: ${daily_budget:.2f}
        Destination: {request.destination}
        Budget Category: {budget_category}
        
        Provide analysis of:
        1. Budget adequacy for the destination and duration
        2. Recommended budget allocation (accommodation, food, activities, transportation)
        3. Cost-saving opportunities if budget is tight
        4. Premium options if budget allows
        5. Realistic expectations for this budget level
        """
        
        context_data = {
            "total_budget": request.budget,
            "daily_budget": daily_budget,
            "duration": duration,
            "destination": request.destination,
            "budget_category": budget_category
        }
        
        budget_analysis = await self.query_ollama(budget_prompt, context_data)
        
        return {
            "total_budget": request.budget,
            "daily_budget": daily_budget,
            "duration": duration,
            "budget_category": budget_category,
            "feasibility_analysis": budget_analysis,
            "budget_allocation": self._suggest_budget_allocation(daily_budget),
            "analyzed_at": datetime.utcnow().isoformat()
        }
    
    async def create_activity_plan(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Create high-level activity plan based on interests
        """
        self.log_action("Creating activity plan")
        
        # Map interests to activity categories
        activity_categories = []
        for interest in request.interests:
            if interest.lower() in INTEREST_TO_PLACE_TYPES:
                place_types = INTEREST_TO_PLACE_TYPES[interest.lower()]
                activity_categories.extend(place_types)
        
        # Remove duplicates while preserving order
        activity_categories = list(dict.fromkeys(activity_categories))
        
        # Create activity planning prompt
        activity_prompt = f"""
        Create a high-level activity plan for this trip:
        
        Destination: {request.destination}
        Duration: {getattr(request, 'duration', 1)} days
        Interests: {', '.join(request.interests)}
        Mapped Activity Types: {', '.join(activity_categories)}
        
        Provide recommendations for:
        1. Priority activities and attractions to include
        2. Activity mix and pacing for the duration
        3. Must-see vs. optional activities
        4. Activity sequencing and timing considerations
        5. Balance between planned activities and free time
        """
        
        context_data = {
            "destination": request.destination,
            "duration": getattr(request, 'duration', 1),
            "interests": request.interests,
            "activity_categories": activity_categories
        }
        
        activity_plan_result = await self.query_ollama(activity_prompt, context_data)
        
        return {
            "original_interests": request.interests,
            "mapped_activity_categories": activity_categories,
            "activity_plan": activity_plan_result,
            "priority_categories": activity_categories[:5],  # Top 5 priorities
            "created_at": datetime.utcnow().isoformat()
        }
    
    async def assess_risks_and_challenges(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Assess potential risks and challenges for the trip
        """
        self.log_action("Assessing risks and challenges")
        
        # Identify potential challenges
        challenges = []
        
        # Duration-based challenges
        duration = getattr(request, 'duration', 1)
        if duration > 10:
            challenges.append("Long trip duration may cause fatigue")
        elif duration < 3:
            challenges.append("Short trip requires efficient planning")
        
        # Budget-based challenges
        if request.budget:
            daily_budget = request.budget / duration
            if daily_budget < 100:
                challenges.append("Limited budget requires careful cost management")
        
        # Seasonal considerations
        travel_date = datetime.fromisoformat(request.start_date)
        month = travel_date.month
        if month in [12, 1, 2]:
            challenges.append("Winter travel may have weather-related constraints")
        elif month in [6, 7, 8]:
            challenges.append("Peak season travel may have higher costs and crowds")
        
        return {
            "identified_challenges": challenges,
            "risk_level": "medium" if len(challenges) > 2 else "low",
            "mitigation_strategies": [
                "Build flexibility into itinerary",
                "Have backup indoor activities for weather",
                "Book accommodations early for peak seasons",
                "Set aside contingency budget"
            ],
            "assessed_at": datetime.utcnow().isoformat()
        }
    
    async def create_coordination_strategy(self, request: TravelRequest) -> Dict[str, Any]:
        """
        Create strategy for coordinating workflow execution
        """
        self.log_action("Creating coordination strategy")
        
        # Define workflow steps and priorities
        workflow_steps = [
            {"step": "data_collection", "priority": "high", "dependencies": []},
            {"step": "destination_research", "priority": "high", "dependencies": ["data_collection"]},
            {"step": "local_expertise", "priority": "medium", "dependencies": ["destination_research"]},
            {"step": "itinerary_creation", "priority": "high", "dependencies": ["data_collection", "destination_research"]},
            {"step": "trip_criticism", "priority": "medium", "dependencies": ["itinerary_creation"]},
            {"step": "finalization", "priority": "high", "dependencies": ["trip_criticism"]}
        ]
        
        # Estimate processing time
        estimated_time = self._estimate_processing_time(request)
        
        return {
            "workflow_steps": workflow_steps,
            "execution_strategy": "parallel_where_possible",
            "estimated_processing_time": estimated_time,
            "quality_gates": [
                "Minimum data collection requirements met",
                "Budget constraints respected", 
                "All days have planned activities",
                "Transportation logistics addressed"
            ],
            "success_criteria": [
                "Complete daily itineraries created",
                "Budget compliance achieved",
                "All interests addressed",
                "Practical logistics covered"
            ],
            "created_at": datetime.utcnow().isoformat()
        }
    
    def _suggest_budget_allocation(self, daily_budget: float) -> Dict[str, float]:
        """Suggest budget allocation across categories"""
        return {
            "accommodation": daily_budget * 0.4,
            "food": daily_budget * 0.3,
            "activities": daily_budget * 0.2,
            "transportation": daily_budget * 0.1
        }
    
    def _estimate_processing_time(self, request: TravelRequest) -> Dict[str, int]:
        """Estimate processing time for workflow steps"""
        base_time = 30  # Base processing time in seconds
        duration_factor = getattr(request, 'duration', 1)
        
        return {
            "data_collection": base_time + (duration_factor * 2),
            "destination_research": base_time,
            "local_expertise": base_time,
            "itinerary_creation": base_time + (duration_factor * 5),
            "trip_criticism": base_time,
            "finalization": base_time // 2,
            "total_estimated": base_time * 6 + (duration_factor * 7)
        }