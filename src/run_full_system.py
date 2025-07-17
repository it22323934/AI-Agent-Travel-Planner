"""
Complete launcher for the AI Agent Travel Planning System
Handles all imports and runs the full workflow
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List

# Add src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

print("🚀 AI AGENT TRAVEL PLANNER - COMPLETE LAUNCHER")
print("=" * 50)
print(f"📁 Project root: {project_root}")
print(f"📁 Source path: {src_path}")

# Global storage for imported modules
components = {}

def safe_import(module_path: str, component_name: str, description: str):
    """Safely import a module with detailed error handling"""
    try:
        parts = module_path.split('.')
        if len(parts) == 2:
            module = __import__(f"{parts[0]}.{parts[1]}", fromlist=[component_name])
            component = getattr(module, component_name, None)
            if component:
                components[component_name] = component
                print(f"   ✅ {description}")
                return component
            else:
                print(f"   ❌ {description}: {component_name} not found in {module_path}")
        else:
            module = __import__(module_path, fromlist=[component_name])
            component = getattr(module, component_name, None)
            if component:
                components[component_name] = component
                print(f"   ✅ {description}")
                return component
    except ImportError as e:
        print(f"   ❌ {description}: Import error - {e}")
    except AttributeError as e:
        print(f"   ❌ {description}: Attribute error - {e}")
    except Exception as e:
        print(f"   ⚠️ {description}: Unexpected error - {e}")
    return None

# Import all components
print("\n📦 Loading Core Components...")
safe_import("core.models", "TravelRequest", "Travel Request Model")
safe_import("core.models", "TravelItinerary", "Travel Itinerary Model")
safe_import("core.exceptions", "TravelPlannerError", "Travel Planner Error")
safe_import("core.exceptions", "ValidationError", "Validation Error")

print("\n⚙️ Loading Configuration...")
safe_import("config", "settings", "Settings Configuration")

print("\n🔌 Loading MCP Components...")
safe_import("mcp", "MCPManager", "MCP Manager")
safe_import("mcp.base_connector", "BaseMCPConnector", "Base MCP Connector")
safe_import("mcp.google_places", "GooglePlacesConnector", "Google Places Connector")
safe_import("mcp.google_weather", "GoogleWeatherConnector", "Google Weather Connector")

print("\n🤖 Loading Agent Components...")
safe_import("agents.base_agent", "BaseAgent", "Base Agent")
safe_import("agents.destination_finder", "DestinationFinder", "Destination Finder Agent")
safe_import("agents.itinerary_expert", "ItineraryExpert", "Itinerary Expert Agent")
safe_import("agents.local_expert", "LocalExpert", "Local Expert Agent")
safe_import("agents.planner_agent", "PlannerAgent", "Planner Agent")
safe_import("agents.prompts", "get_agent_prompt", "Agent Prompts")
safe_import("agents.trip_critic", "ItineraryExpert", "Trip Critic Agent")

print("\n🌐 Loading Workflow Components...")
safe_import("graph.workflow", "TravelPlanningWorkflow", "Travel Planning Workflow")
safe_import("graph.state", "TravelPlanningState", "Travel Planning State")
safe_import("graph.nodes", "create_nodes", "Graph Nodes")

print("\n🛠️ Loading Utility Components...")
# safe_import("utils.validators", "validate_dates", "Date Validator")
# safe_import("utils.validators", "validate_budget", "Budget Validator")
safe_import("utils.formatters", "format_itinerary_output", "Itinerary Formatter")
safe_import("utils.logger", "setup_logging", "Logger Setup")

# Count loaded components
loaded_count = len(components)
total_expected = 25  # Adjust based on your actual components

print(f"\n📊 System Status: {loaded_count}/{total_expected} components loaded")
print("=" * 50)

# Test basic functionality
async def test_system():
    """Test the travel planning system with available components"""
    
    print("\n🧪 SYSTEM FUNCTIONALITY TEST")
    print("=" * 40)
    
    # Test configuration
    if 'settings' in components:
        settings = components['settings']
        print(f"\n📝 Configuration:")
        # print(f"   Google API Key: {'✅ Set' if settings.google_api_key() else '❌ Missing'}")
        # print(f"   Ollama URL: {settings.ollama_url()}")
        # print(f"   Ollama Model: {settings.ollama_model()}")
    
    # Test travel request creation
    if 'TravelRequest' in components:
        print(f"\n📋 Travel Request Test:")
        try:
            TravelRequest = components['TravelRequest']
            test_request = TravelRequest(
                destination="Paris, France",
                start_date="2024-09-15",
                end_date="2024-09-20",
                budget=2000.0,
                interests=["museums", "food", "architecture"],
                constraints=["wheelchair accessible", "vegetarian options"]
            )
            print(f"   ✅ Created: {test_request.destination}")
            print(f"   Duration: {test_request.duration} days")
            print(f"   Budget: ${test_request.budget}")
        except Exception as e:
            print(f"   ❌ Failed: {e}")
    
    # Test MCP connections
    if 'MCPManager' in components:
        print(f"\n🔌 MCP Connections Test:")
        try:
            MCPManager = components['MCPManager']
            async with MCPManager() as mcp:
                status = await mcp.test_all_connections()
                for service, connected in status.items():
                    print(f"   {service}: {'✅ Connected' if connected else '❌ Disconnected'}")
        except Exception as e:
            print(f"   ❌ MCP test failed: {e}")
    
    # Test workflow if available
    if 'TravelPlanningWorkflow' in components and 'TravelRequest' in components:
        print(f"\n🌐 Workflow Test:")
        try:
            TravelPlanningWorkflow = components['TravelPlanningWorkflow']
            workflow = TravelPlanningWorkflow()
            print(f"   ✅ Workflow initialized")
            
            # Show available nodes
            if hasattr(workflow, 'graph'):
                print(f"   Available nodes: {len(workflow.graph.nodes)} nodes configured")
        except Exception as e:
            print(f"   ❌ Workflow test failed: {e}")

async def run_travel_planner():
    """Run the complete travel planning workflow"""
    
    print("\n🎯 TRAVEL PLANNER EXECUTION")
    print("=" * 40)
    
    # Check if we have minimum components
    required = ['TravelRequest', 'TravelPlanningWorkflow', 'MCPManager']
    missing = [comp for comp in required if comp not in components]
    
    if missing:
        print(f"❌ Missing required components: {', '.join(missing)}")
        print("\n🔧 To fix:")
        for comp in missing:
            print(f"   - Ensure {comp} is properly implemented")
        return
    
    try:
        # Get user input
        print("\n📝 Enter your travel details:")
        destination = input("   Destination: ") or "Paris, France"
        start_date = input("   Start date (YYYY-MM-DD): ") or "2024-09-15"
        end_date = input("   End date (YYYY-MM-DD): ") or "2024-09-20"
        budget = float(input("   Budget ($): ") or "2000")
        interests = input("   Interests (comma-separated): ").split(",") or ["museums", "food"]
        
        # Create travel request
        TravelRequest = components['TravelRequest']
        request = TravelRequest(
            destination=destination,
            start_date=start_date,
            end_date=end_date,
            budget=budget,
            interests=[i.strip() for i in interests]
        )
        
        print(f"\n🚀 Planning your {request.duration}-day trip to {request.destination}...")
        
        # Run workflow
        TravelPlanningWorkflow = components['TravelPlanningWorkflow']
        workflow = TravelPlanningWorkflow()
        
        # Execute the workflow
        result = await workflow.execute(request)
        
        # Display results
        if result and hasattr(result, 'itinerary'):
            print(f"\n✅ TRAVEL PLAN COMPLETE!")
            print("=" * 40)
            
            if 'format_itinerary' in components:
                formatter = components['format_itinerary']
                formatted = formatter(result.itinerary)
                print(formatted)
            else:
                print(result.itinerary)
        else:
            print(f"\n⚠️ Workflow completed but no itinerary generated")
            
    except Exception as e:
        print(f"\n❌ Error running travel planner: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main entry point"""
    
    # First test the system
    await test_system()
    
    # Show options
    print("\n📋 OPTIONS:")
    print("1. Run full travel planner")
    print("2. Test individual components")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        await run_travel_planner()
    elif choice == "2":
        print("\n🔧 Component testing not yet implemented")
        print("You can manually test components using the Python REPL")
    else:
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Travel planner terminated by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()