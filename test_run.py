import asyncio
from src.main import TravelPlannerApp

async def plan_my_trip():
    app = TravelPlannerApp()
    await app.setup()
    
    # Your travel request
    request = {
        "destination": "Tokyo, Japan",
        "start_date": "2024-10-01",
        "end_date": "2024-10-07",
        "budget": 3000.0,
        "interests": ["culture", "food", "technology"],
        "travelers": 1
    }
    
    result = await app.plan_trip(request)
    
    if result["success"]:
        print("✅ Trip planned successfully!")
        print(f"Destination: {result['itinerary']['destination']}")
        print(f"Duration: {result['itinerary']['travel_dates']['duration']} days")
    else:
        print(f"❌ Planning failed: {result['error']}")

# Run it
asyncio.run(plan_my_trip())