"""
Output formatters for the Travel Planning System
"""

import json
from typing import Dict, Any, List
from datetime import datetime

from core.models import TravelItinerary, DailyPlan, PlaceRecommendation, WeatherInfo


def format_itinerary_output(itinerary: TravelItinerary, format_type: str = "detailed") -> str:
    """
    Format itinerary output in various formats
    
    Args:
        itinerary: TravelItinerary object
        format_type: "detailed", "summary", "json", or "markdown"
    
    Returns:
        Formatted string representation
    """
    
    if format_type == "json":
        return format_itinerary_json(itinerary)
    elif format_type == "markdown":
        return format_itinerary_markdown(itinerary)
    elif format_type == "summary":
        return format_itinerary_summary(itinerary)
    else:
        return format_itinerary_detailed(itinerary)


def format_itinerary_detailed(itinerary: TravelItinerary) -> str:
    """Format itinerary in detailed text format"""
    
    output = []
    
    # Header
    output.append("=" * 60)
    output.append(f"TRAVEL ITINERARY: {itinerary.destination.upper()}")
    output.append("=" * 60)
    output.append(f"Travel Dates: {itinerary.start_date} to {itinerary.end_date}")
    output.append(f"Duration: {itinerary.duration} days")
    if itinerary.total_estimated_cost:
        output.append(f"Estimated Cost: ${itinerary.total_estimated_cost:.0f} USD")
    output.append("")
    
    # Weather Forecast
    if itinerary.weather_forecast:
        output.append("🌤️  WEATHER FORECAST")
        output.append("-" * 30)
        for weather in itinerary.weather_forecast:
            temp_range = f"{weather.temperature_low}°C - {weather.temperature_high}°C"
            output.append(f"{weather.date}: {weather.description}, {temp_range}")
            if weather.precipitation_chance > 30:
                output.append(f"  ⚠️  Rain chance: {weather.precipitation_chance}%")
        output.append("")
    
    # Accommodations
    if itinerary.hotels:
        output.append("🏨 RECOMMENDED ACCOMMODATIONS")
        output.append("-" * 30)
        for i, hotel in enumerate(itinerary.hotels[:5], 1):
            price_stars = "💰" * max(hotel.price_level, 1)
            rating_stars = "⭐" * int(hotel.rating)
            output.append(f"{i}. {hotel.name}")
            output.append(f"   Rating: {hotel.rating}/5 {rating_stars}")
            output.append(f"   Price Level: {price_stars}")
            output.append(f"   Address: {hotel.address}")
            output.append("")
    
    # Daily Itinerary
    output.append("📅 DAILY ITINERARY")
    output.append("-" * 30)
    
    for day_plan in itinerary.daily_plans:
        output.append(f"\n📆 {day_plan.date}")
        output.append(f"Weather: {day_plan.weather.description} ({day_plan.weather.temperature_high}°C)")
        
        if day_plan.morning_activities:
            output.append("🌅 Morning:")
            for activity in day_plan.morning_activities:
                output.append(f"  • {activity}")
        
        if day_plan.afternoon_activities:
            output.append("☀️ Afternoon:")
            for activity in day_plan.afternoon_activities:
                output.append(f"  • {activity}")
        
        if day_plan.evening_activities:
            output.append("🌙 Evening:")
            for activity in day_plan.evening_activities:
                output.append(f"  • {activity}")
        
        if day_plan.recommended_restaurants:
            output.append("🍽️ Recommended Dining:")
            for restaurant in day_plan.recommended_restaurants:
                output.append(f"  • {restaurant.name} (★{restaurant.rating})")
        
        output.append("")
    
    # Top Attractions
    if itinerary.attractions:
        output.append("🎭 TOP ATTRACTIONS")
        output.append("-" * 30)
        for i, attraction in enumerate(itinerary.attractions[:10], 1):
            output.append(f"{i}. {attraction.name} (★{attraction.rating})")
            output.append(f"   Type: {attraction.place_type}")
            output.append(f"   Address: {attraction.address}")
            output.append("")
    
    # Recommendations
    if itinerary.recommendations:
        output.append("💡 RECOMMENDATIONS")
        output.append("-" * 30)
        for rec in itinerary.recommendations:
            output.append(f"• {rec}")
        output.append("")
    
    # Footer
    output.append("-" * 60)
    if itinerary.created_at:
        output.append(f"Generated: {itinerary.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    output.append("Happy travels! 🌍✈️")
    
    return "\n".join(output)


def format_itinerary_summary(itinerary: TravelItinerary) -> str:
    """Format itinerary in summary format"""
    
    summary = []
    
    summary.append(f"🌍 {itinerary.destination} - {itinerary.duration} days")
    summary.append(f"📅 {itinerary.start_date} to {itinerary.end_date}")
    
    if itinerary.total_estimated_cost:
        summary.append(f"💰 ${itinerary.total_estimated_cost:.0f} estimated")
    
    summary.append(f"🏨 {len(itinerary.hotels)} hotels found")
    summary.append(f"🎭 {len(itinerary.attractions)} attractions")
    summary.append(f"🍽️ {len(itinerary.restaurants)} restaurants")
    
    # Weather summary
    if itinerary.weather_forecast:
        avg_high = sum(w.temperature_high for w in itinerary.weather_forecast) / len(itinerary.weather_forecast)
        avg_low = sum(w.temperature_low for w in itinerary.weather_forecast) / len(itinerary.weather_forecast)
        summary.append(f"🌤️ {avg_low:.0f}°C - {avg_high:.0f}°C average")
    
    # Daily activities count
    total_activities = sum(
        len(day.morning_activities) + len(day.afternoon_activities) + len(day.evening_activities)
        for day in itinerary.daily_plans
    )
    summary.append(f"📋 {total_activities} activities planned")
    
    return "\n".join(summary)


def format_itinerary_json(itinerary: TravelItinerary) -> str:
    """Format itinerary as JSON"""
    return json.dumps(itinerary.to_dict(), indent=2, ensure_ascii=False)


def format_itinerary_markdown(itinerary: TravelItinerary) -> str:
    """Format itinerary in Markdown format"""
    
    md = []
    
    # Title
    md.append(f"# Travel Itinerary: {itinerary.destination}")
    md.append("")
    md.append(f"**Travel Dates:** {itinerary.start_date} to {itinerary.end_date}")
    md.append(f"**Duration:** {itinerary.duration} days")
    if itinerary.total_estimated_cost:
        md.append(f"**Estimated Cost:** ${itinerary.total_estimated_cost:.0f} USD")
    md.append("")
    
    # Weather
    if itinerary.weather_forecast:
        md.append("## 🌤️ Weather Forecast")
        md.append("")
        md.append("| Date | Condition | Temperature | Rain Chance |")
        md.append("|------|-----------|-------------|-------------|")
        for weather in itinerary.weather_forecast:
            temp_range = f"{weather.temperature_low}°C - {weather.temperature_high}°C"
            md.append(f"| {weather.date} | {weather.description} | {temp_range} | {weather.precipitation_chance}% |")
        md.append("")
    
    # Accommodations
    if itinerary.hotels:
        md.append("## 🏨 Recommended Accommodations")
        md.append("")
        for i, hotel in enumerate(itinerary.hotels[:5], 1):
            md.append(f"### {i}. {hotel.name}")
            md.append(f"- **Rating:** {hotel.rating}/5 ⭐")
            md.append(f"- **Price Level:** {'💰' * max(hotel.price_level, 1)}")
            md.append(f"- **Address:** {hotel.address}")
            md.append("")
    
    # Daily Itinerary
    md.append("## 📅 Daily Itinerary")
    md.append("")
    
    for day_plan in itinerary.daily_plans:
        md.append(f"### 📆 {day_plan.date}")
        md.append(f"**Weather:** {day_plan.weather.description} ({day_plan.weather.temperature_high}°C)")
        md.append("")
        
        if day_plan.morning_activities:
            md.append("#### 🌅 Morning")
            for activity in day_plan.morning_activities:
                md.append(f"- {activity}")
            md.append("")
        
        if day_plan.afternoon_activities:
            md.append("#### ☀️ Afternoon")
            for activity in day_plan.afternoon_activities:
                md.append(f"- {activity}")
            md.append("")
        
        if day_plan.evening_activities:
            md.append("#### 🌙 Evening")
            for activity in day_plan.evening_activities:
                md.append(f"- {activity}")
            md.append("")
        
        if day_plan.recommended_restaurants:
            md.append("#### 🍽️ Recommended Dining")
            for restaurant in day_plan.recommended_restaurants:
                md.append(f"- **{restaurant.name}** (★{restaurant.rating})")
            md.append("")
    
    # Top Attractions
    if itinerary.attractions:
        md.append("## 🎭 Top Attractions")
        md.append("")
        for i, attraction in enumerate(itinerary.attractions[:10], 1):
            md.append(f"### {i}. {attraction.name}")
            md.append(f"- **Rating:** {attraction.rating}/5 ⭐")
            md.append(f"- **Type:** {attraction.place_type}")
            md.append(f"- **Address:** {attraction.address}")
            md.append("")
    
    # Restaurants
    if itinerary.restaurants:
        md.append("## 🍽️ Restaurant Recommendations")
        md.append("")
        for i, restaurant in enumerate(itinerary.restaurants[:8], 1):
            md.append(f"### {i}. {restaurant.name}")
            md.append(f"- **Rating:** {restaurant.rating}/5 ⭐")
            md.append(f"- **Price Level:** {'💰' * max(restaurant.price_level, 1)}")
            md.append(f"- **Address:** {restaurant.address}")
            md.append("")
    
    # Recommendations
    if itinerary.recommendations:
        md.append("## 💡 Travel Tips & Recommendations")
        md.append("")
        for rec in itinerary.recommendations:
            md.append(f"- {rec}")
        md.append("")
    
    # Footer
    md.append("---")
    if itinerary.created_at:
        md.append(f"*Generated on {itinerary.created_at.strftime('%Y-%m-%d %H:%M:%S')}*")
    md.append("")
    md.append("Happy travels! 🌍✈️")
    
    return "\n".join(md)


def format_execution_summary(execution_details: Dict[str, Any]) -> str:
    """Format execution summary for debugging"""
    
    summary = []
    
    summary.append("🔍 EXECUTION SUMMARY")
    summary.append("=" * 40)
    
    exec_summary = execution_details.get("execution_summary", {})
    
    summary.append(f"Total Steps: {exec_summary.get('total_steps', 'Unknown')}")
    summary.append(f"Final Status: {exec_summary.get('final_status', 'Unknown')}")
    summary.append(f"Processing Time: {exec_summary.get('processing_time', 'Unknown')}")
    summary.append(f"Optimization Rounds: {exec_summary.get('optimization_rounds', 0)}")
    
    # Data collection summary
    data_collected = exec_summary.get("data_collected", {})
    if data_collected:
        summary.append("\n📊 Data Collected:")
        summary.append(f"  Hotels: {data_collected.get('hotels', 0)}")
        summary.append(f"  Restaurants: {data_collected.get('restaurants', 0)}")
        summary.append(f"  Attractions: {data_collected.get('attractions', 0)}")
        summary.append(f"  Weather Days: {data_collected.get('weather_days', 0)}")
    
    # Completed steps
    completed_steps = exec_summary.get("completed_steps", [])
    if completed_steps:
        summary.append("\n✅ Completed Steps:")
        for step in completed_steps:
            summary.append(f"  • {step}")
    
    # Failed steps
    failed_steps = exec_summary.get("failed_steps", [])
    if failed_steps:
        summary.append("\n❌ Failed Steps:")
        for step in failed_steps:
            summary.append(f"  • {step}")
    
    return "\n".join(summary)


def format_agent_performance(state_history: List[Dict[str, Any]]) -> str:
    """Format agent performance analysis"""
    
    performance = []
    
    performance.append("🤖 AGENT PERFORMANCE")
    performance.append("=" * 40)
    
    if not state_history:
        performance.append("No performance data available")
        return "\n".join(performance)
    
    # Extract timing information
    step_times = []
    for i in range(1, len(state_history)):
        prev_time = datetime.fromisoformat(state_history[i-1]["timestamp"])
        curr_time = datetime.fromisoformat(state_history[i]["timestamp"])
        step_duration = (curr_time - prev_time).total_seconds()
        step_times.append({
            "step": state_history[i]["step"],
            "duration": step_duration
        })
    
    # Show step performance
    performance.append("⏱️ Step Performance:")
    for step_info in step_times:
        performance.append(f"  {step_info['step']}: {step_info['duration']:.2f}s")
    
    if step_times:
        total_time = sum(s["duration"] for s in step_times)
        avg_time = total_time / len(step_times)
        performance.append(f"\nTotal Time: {total_time:.2f}s")
        performance.append(f"Average Step Time: {avg_time:.2f}s")
    
    return "\n".join(performance)


def format_criticism_report(criticism_data: Dict[str, Any]) -> str:
    """Format trip criticism report"""
    
    report = []
    
    report.append("📝 TRIP CRITICISM REPORT")
    report.append("=" * 40)
    
    overall = criticism_data.get("overall_assessment", {})
    
    report.append(f"Overall Score: {overall.get('overall_score', 'N/A')}/10")
    report.append(f"Overall Rating: {overall.get('overall_rating', 'Unknown').upper()}")
    
    # Component scores
    component_scores = overall.get("component_scores", {})
    if component_scores:
        report.append("\n📊 Component Scores:")
        for component, score in component_scores.items():
            report.append(f"  {component.title()}: {score}/10")
    
    # Strengths
    strengths = overall.get("strengths", [])
    if strengths:
        report.append("\n✅ Strengths:")
        for strength in strengths:
            report.append(f"  • {strength}")
    
    # Areas for improvement
    improvements = overall.get("areas_for_improvement", [])
    if improvements:
        report.append("\n🔧 Areas for Improvement:")
        for improvement in improvements:
            report.append(f"  • {improvement}")
    
    # Recommendations
    recommendations = criticism_data.get("improvement_recommendations", [])
    if recommendations:
        high_priority = [r for r in recommendations if r.get("priority") == "high"]
        medium_priority = [r for r in recommendations if r.get("priority") == "medium"]
        
        if high_priority:
            report.append("\n🚨 High Priority Recommendations:")
            for rec in high_priority:
                report.append(f"  • {rec.get('recommendation', 'N/A')}")
                report.append(f"    Reason: {rec.get('reasoning', 'N/A')}")
        
        if medium_priority:
            report.append("\n⚠️ Medium Priority Recommendations:")
            for rec in medium_priority:
                report.append(f"  • {rec.get('recommendation', 'N/A')}")
    
    # Overall recommendation
    overall_rec = overall.get("recommendation", "")
    if overall_rec:
        report.append(f"\n💡 Overall Recommendation:")
        report.append(f"  {overall_rec}")
    
    return "\n".join(report)


def create_travel_report(itinerary: TravelItinerary, 
                        execution_details: Dict[str, Any] = None,
                        criticism_data: Dict[str, Any] = None) -> str:
    """Create comprehensive travel report"""
    
    report_sections = []
    
    # Main itinerary
    report_sections.append(format_itinerary_detailed(itinerary))
    
    # Execution details if available
    if execution_details:
        report_sections.append("\n" + "=" * 60)
        report_sections.append(format_execution_summary(execution_details))
        
        state_history = execution_details.get("state_history", [])
        if state_history:
            report_sections.append("\n" + format_agent_performance(state_history))
    
    # Criticism report if available
    if criticism_data:
        report_sections.append("\n" + "=" * 60)
        report_sections.append(format_criticism_report(criticism_data))
    
    return "\n".join(report_sections)


def save_itinerary_to_file(itinerary: TravelItinerary, 
                          filename: str = None,
                          format_type: str = "markdown") -> str:
    """Save itinerary to file"""
    
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_clean = "".join(c for c in itinerary.destination if c.isalnum() or c in (' ', '-', '_')).rstrip()
        destination_clean = destination_clean.replace(' ', '_')
        filename = f"itinerary_{destination_clean}_{timestamp}"
    
    # Add appropriate extension
    extensions = {
        "markdown": ".md",
        "json": ".json",
        "detailed": ".txt",
        "summary": ".txt"
    }
    
    if not any(filename.endswith(ext) for ext in extensions.values()):
        filename += extensions.get(format_type, ".txt")
    
    # Format content
    content = format_itinerary_output(itinerary, format_type)
    
    # Save to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return filename
    except Exception as e:
        raise Exception(f"Failed to save itinerary to {filename}: {e}")


# Utility functions for formatting
def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    if currency == "USD":
        return f"${amount:,.0f}"
    else:
        return f"{amount:,.0f} {currency}"


def format_rating(rating: float) -> str:
    """Format rating with stars"""
    full_stars = int(rating)
    half_star = 1 if rating - full_stars >= 0.5 else 0
    empty_stars = 5 - full_stars - half_star
    
    return "⭐" * full_stars + "✨" * half_star + "☆" * empty_stars