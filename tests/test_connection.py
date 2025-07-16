import asyncio
import aiohttp
import json

async def test_ollama():
    """Test Ollama connection"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:11434/api/tags") as response:
                if response.status == 200:
                    print("✅ Ollama is running")
                    return True
                else:
                    print("❌ Ollama not responding")
                    return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

async def test_google_api():
    """Test Google API with a simple request"""
    api_key = "AIzaSyA-hts7zA_2B0HzOrYJB-FIbhM4Z4VP5TQ"  # Replace with your actual key
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Paris&key={api_key}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "OK":
                        print("✅ Google API is working")
                        return True
                print("❌ Google API error")
                return False
    except Exception as e:
        print(f"❌ Google API connection failed: {e}")
        return False

async def main():
    print("🧪 Testing system components...")
    
    ollama_ok = await test_ollama()
    google_ok = await test_google_api()
    
    if ollama_ok and google_ok:
        print("🎉 All systems ready!")
    else:
        print("⚠️ Some components need attention")

if __name__ == "__main__":
    asyncio.run(main())