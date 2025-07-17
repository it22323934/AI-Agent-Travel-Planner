"""
Configuration package for the travel planning system
"""

from .settings import settings, get_google_api_key, get_ollama_config, validate_settings

__all__ = [
    'settings',
    'get_google_api_key',
    'get_ollama_config',
    'validate_settings'
]

# Make settings available directly from config import
__version__ = "1.0.0"