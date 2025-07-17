"""
Simple configuration settings for the travel planning system
Compatible with your existing .env file
"""

import os
from typing import Optional
from pathlib import Path

# Try to load from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove inline comments
                        if '#' in value:
                            value = value.split('#')[0].strip()
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

# Load environment variables
load_env_file()


class SimpleSettings:
    """Simple settings class that accepts all your environment variables"""
    
    def __init__(self):
        # Google API Configuration
        self.google_api_key = os.getenv("GOOGLE_API_KEY", "")
        self.google_places_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        self.google_weather_api_key = os.getenv("GOOGLE_WEATHER_API_KEY")
        
        # Ollama Configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        self.ollama_temperature = float(os.getenv("OLLAMA_TEMPERATURE", "0.7"))
        self.ollama_max_tokens = int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
        
        # Application Settings
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_workers = int(os.getenv("MAX_WORKERS", "4"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        
        # Rate Limiting
        self.google_api_rate_limit = int(os.getenv("GOOGLE_API_RATE_LIMIT", "100"))
        self.requests_per_minute = int(os.getenv("REQUESTS_PER_MINUTE", "60"))
        
        # Travel Planning Settings
        self.max_trip_duration = int(os.getenv("MAX_TRIP_DURATION", "30"))
        self.default_search_radius = int(os.getenv("DEFAULT_SEARCH_RADIUS", "5000"))
        self.max_recommendations_per_type = int(os.getenv("MAX_RECOMMENDATIONS_PER_TYPE", "20"))
        
        # MCP Configuration (from your .env)
        self.mcp_host = os.getenv("MCP_HOST", "localhost")
        self.mcp_port = int(os.getenv("MCP_PORT", "8000"))
        self.mcp_timeout = int(os.getenv("MCP_TIMEOUT", "30"))
        
        # Additional settings (from your .env)
        self.default_budget_currency = os.getenv("DEFAULT_BUDGET_CURRENCY", "USD")
        self.development_mode = os.getenv("DEVELOPMENT_MODE", "False").lower() == "true"
        self.debug_agents = os.getenv("DEBUG_AGENTS", "False").lower() == "true"
        self.save_intermediate_results = os.getenv("SAVE_INTERMEDIATE_RESULTS", "True").lower() == "true"


# Global settings instance
settings = SimpleSettings()


def get_google_api_key(service: str = "default") -> str:
    """Get Google API key for specific service"""
    service_keys = {
        "places": settings.google_places_api_key or settings.google_api_key,
        "weather": settings.google_weather_api_key or settings.google_api_key,
        "default": settings.google_api_key
    }
    return service_keys.get(service, settings.google_api_key)


def get_ollama_config() -> dict:
    """Get Ollama configuration dictionary"""
    return {
        "base_url": settings.ollama_base_url,
        "model": settings.ollama_model,
        "temperature": settings.ollama_temperature,
        "max_tokens": settings.ollama_max_tokens
    }


def validate_settings():
    """Validate critical settings"""
    print("🔍 Checking configuration...")
    
    if settings.google_api_key:
        print("✅ Google API key is configured")
        print(f"   Key starts with: {settings.google_api_key[:10]}...")
    else:
        print("⚠️ Google API key not set")
    
    print(f"✅ Ollama URL: {settings.ollama_base_url}")
    print(f"✅ Ollama Model: {settings.ollama_model}")
    print(f"✅ Development Mode: {settings.development_mode}")
    print(f"✅ Max Trip Duration: {settings.max_trip_duration} days")
    
    return bool(settings.google_api_key)


# Print settings info when imported
if __name__ != "__main__":
    print("📝 Configuration loaded successfully!")
    validate_settings()