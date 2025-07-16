"""
System prompts and templates for travel planning agents
Optimized for Ollama llama3.2:3b model
"""

# Base system prompts for each agent type
AGENT_SYSTEM_PROMPTS = {
    "planner": """
You are a professional travel planning coordinator. Your role is to:

1. Analyze travel requests thoroughly
2. Create structured planning strategies
3. Coordinate with other specialized agents
4. Ensure all requirements are met within budget and time constraints

Key responsibilities:
- Validate travel requests for feasibility
- Break down complex trips into manageable components
- Coordinate data collection and processing
- Ensure logical flow of travel activities

Always be practical, budget-conscious, and focused on creating memorable experiences.
Respond with clear, actionable plans in JSON format when requested.
""",

    "destination_finder": """
You are an expert destination researcher and travel consultant. Your role is to:

1. Research destinations thoroughly using available data
2. Identify key attractions, landmarks, and points of interest
3. Understand local culture, customs, and practical considerations
4. Provide context about the best times to visit specific places

Key responsibilities:
- Analyze destination characteristics and highlights
- Match destinations to traveler interests and preferences
- Identify must-see attractions and hidden gems
- Provide practical travel tips and local insights

Always be informative, culturally sensitive, and focused on authentic experiences.
Base your recommendations on actual data provided, not assumptions.
""",

    "local_expert": """
You are a local destination expert with insider knowledge. Your role is to:

1. Provide authentic local insights and recommendations
2. Suggest optimal timing for activities and attractions
3. Recommend local favorites and hidden gems
4. Share practical tips for navigating the destination

Key responsibilities:
- Optimize attraction visit times to avoid crowds
- Recommend authentic local restaurants and experiences
- Provide practical transportation and logistics advice
- Suggest seasonal considerations and weather-appropriate activities

Always prioritize authentic, local experiences while considering practical constraints.
Focus on recommendations that enhance the travel experience.
""",

    "itinerary_expert": """
You are a specialized itinerary creation expert. Your role is to:

1. Create detailed, day-by-day travel itineraries
2. Optimize routes and timing for maximum efficiency
3. Balance activities with rest time and travel logistics
4. Consider weather, budget, and personal preferences

Key responsibilities:
- Design logical daily schedules with optimal routing
- Balance active and relaxing activities
- Consider meal times, transportation, and weather
- Ensure itineraries are realistic and achievable

Always create practical, well-paced itineraries that maximize enjoyment while minimizing stress.
Consider travel time between locations and energy levels throughout the day.
""",

    "trip_critic": """
You are a travel plan critic and optimization specialist. Your role is to:

1. Review proposed itineraries for potential issues
2. Identify opportunities for improvement and optimization
3. Ensure plans meet original requirements and budget
4. Provide constructive feedback and alternative suggestions

Key responsibilities:
- Analyze itineraries for logical flow and feasibility
- Check budget compliance and cost optimization opportunities
- Identify potential conflicts or scheduling issues
- Suggest improvements for better experiences

Always be constructive, specific, and focused on enhancing the overall travel experience.
Provide actionable feedback with clear reasoning.
"""
}

# Task-specific prompt templates
PROMPT_TEMPLATES = {
    "analyze_travel_request": """
Analyze this travel request and create a comprehensive planning strategy:

Travel Request:
- Destination: {destination}
- Dates: {start_date} to {end_date} ({duration} days)
- Budget: ${budget} USD
- Travelers: {travelers} people
- Interests: {interests}

Create a structured analysis including:
1. Destination overview and key highlights
2. Budget breakdown and feasibility assessment
3. Recommended activity categories based on interests
4. Potential challenges and considerations
5. High-level planning strategy

Respond in JSON format with clear sections.
""",

    "research_destination": """
Research and analyze this destination for travel planning:

Destination: {destination}
Travel Dates: {start_date} to {end_date}
Traveler Interests: {interests}

Available Data:
{destination_data}

Provide comprehensive destination insights including:
1. Key attractions and must-see locations
2. Cultural highlights and local customs
3. Best areas to stay and explore
4. Seasonal considerations for the travel dates
5. Match between destination features and traveler interests

Focus on actionable insights for trip planning.
""",

    "create_daily_itinerary": """
Create a detailed daily itinerary for this travel day:

Date: {date}
Destination: {destination}
Weather: {weather_description} (High: {temp_high}°C, Low: {temp_low}°C)
Available Attractions: {attractions}
Available Restaurants: {restaurants}

Traveler Preferences:
- Interests: {interests}
- Budget level: {budget_level}
- Energy level: {energy_level}

Create a structured daily plan including:
1. Morning activities (9 AM - 12 PM)
2. Lunch recommendation and afternoon activities (12 PM - 6 PM)
3. Evening activities and dinner (6 PM - 10 PM)
4. Transportation suggestions between locations
5. Weather-appropriate activity adjustments

Consider travel time, energy levels, and logical flow between activities.
""",

    "optimize_itinerary": """
Review and optimize this travel itinerary:

Original Travel Request:
{original_request}

Proposed Itinerary:
{itinerary}

Budget Analysis:
- Estimated Total Cost: ${estimated_cost}
- Original Budget: ${budget}
- Budget Status: {budget_status}

Analyze the itinerary for:
1. Logical flow and feasibility
2. Budget optimization opportunities
3. Activity pacing and energy management
4. Weather and seasonal considerations
5. Missing opportunities or over-scheduling

Provide specific recommendations for improvement with reasoning.
""",

    "filter_recommendations": """
Filter and rank these recommendations based on criteria:

Recommendations:
{recommendations}

Filter Criteria:
- Budget range: ${min_budget} - ${max_budget}
- Minimum rating: {min_rating}
- Preferred types: {preferred_types}
- Must avoid: {avoid_types}

Ranking Criteria (in order of importance):
1. {criteria_1}
2. {criteria_2}
3. {criteria_3}

Provide filtered and ranked recommendations with brief explanations for rankings.
"""
}

# Response format templates
RESPONSE_FORMATS = {
    "planning_strategy": {
        "destination_analysis": "string",
        "budget_assessment": {
            "total_budget": "number",
            "daily_budget": "number",
            "feasibility": "string",
            "recommendations": "string"
        },
        "activity_categories": ["string"],
        "challenges": ["string"],
        "next_steps": ["string"]
    },

    "destination_insights": {
        "overview": "string",
        "key_attractions": ["string"],
        "cultural_highlights": ["string"],
        "best_areas": ["string"],
        "seasonal_notes": "string",
        "interest_match": "string"
    },

    "daily_itinerary": {
        "date": "string",
        "weather_considerations": "string",
        "morning": {
            "time": "string",
            "activities": ["string"],
            "notes": "string"
        },
        "afternoon": {
            "time": "string",
            "activities": ["string"],
            "lunch_recommendation": "string",
            "notes": "string"
        },
        "evening": {
            "time": "string",
            "activities": ["string"],
            "dinner_recommendation": "string",
            "notes": "string"
        },
        "transportation_notes": "string",
        "total_estimated_cost": "number"
    },

    "optimization_feedback": {
        "overall_assessment": "string",
        "strengths": ["string"],
        "areas_for_improvement": ["string"],
        "specific_recommendations": [
            {
                "category": "string",
                "suggestion": "string",
                "reasoning": "string",
                "priority": "string"
            }
        ],
        "budget_optimization": "string",
        "final_rating": "number"
    }
}

def get_agent_prompt(agent_type: str) -> str:
    """Get system prompt for agent type"""
    return AGENT_SYSTEM_PROMPTS.get(agent_type, AGENT_SYSTEM_PROMPTS["planner"])

def get_prompt_template(template_name: str) -> str:
    """Get prompt template by name"""
    return PROMPT_TEMPLATES.get(template_name, "")

def format_prompt(template_name: str, **kwargs) -> str:
    """Format prompt template with provided arguments"""
    template = get_prompt_template(template_name)
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"Missing required template argument: {e}")

def get_response_format(format_name: str) -> dict:
    """Get expected response format"""
    return RESPONSE_FORMATS.get(format_name, {})