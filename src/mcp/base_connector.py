"""
Base MCP connector for Google APIs
Model Context Protocol implementation for external service communication
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from core.exceptions import MCPError, GoogleAPIError
from config.settings import settings


class BaseMCPConnector(ABC):
    """
    Base class for all MCP connectors
    Implements common functionality for Google API communication
    """
    
    def __init__(self, api_key: str, service_name: str):
        self.api_key = api_key
        self.service_name = service_name
        self.session: Optional[aiohttp.ClientSession] = None
        self.logger = logging.getLogger(f"mcp.{service_name}")
        
        # Rate limiting
        self.request_count = 0
        self.last_request_time = datetime.now()
        self.rate_limit_delay = 60 / settings.requests_per_minute  # seconds between requests
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.request_timeout),
            headers={"User-Agent": "TravelPlanner/1.0"}
        )
        self.logger.info(f"MCP connector for {self.service_name} initialized")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        self.logger.info(f"MCP connector for {self.service_name} closed")
    
    async def _rate_limit(self):
        """Implement rate limiting"""
        now = datetime.now()
        time_since_last = (now - self.last_request_time).total_seconds()
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
    
    async def _make_request(self, method: str, url: str, params: Optional[Dict] = None, 
                           data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make HTTP request with error handling and retry logic
        """
        if not self.session:
            raise MCPError("Session not initialized. Use async context manager.")
        
        # Apply rate limiting
        await self._rate_limit()
        
        # Add API key to parameters
        if params is None:
            params = {}
        params['key'] = self.api_key
        
        # Retry logic
        for attempt in range(settings.max_retries):
            try:
                self.logger.debug(f"Making {method} request to {url} (attempt {attempt + 1})")
                
                async with self.session.request(method, url, params=params, json=data) as response:
                    self.request_count += 1
                    self.last_request_time = datetime.now()
                    
                    if response.status == 200:
                        result = await response.json()
                        self.logger.debug(f"Request successful: {response.status}")
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.warning(f"Request failed: {response.status} - {error_text}")
                        
                        if attempt == settings.max_retries - 1:
                            raise GoogleAPIError(
                                f"{self.service_name} API error: {response.status}",
                                self.service_name
                            )
                        
            except aiohttp.ClientError as e:
                self.logger.error(f"Request attempt {attempt + 1} failed: {e}")
                if attempt == settings.max_retries - 1:
                    raise MCPError(f"Max retries exceeded for {self.service_name}: {e}")
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        raise MCPError(f"Failed to complete request to {self.service_name}")
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test API connectivity"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connector statistics"""
        return {
            "service_name": self.service_name,
            "request_count": self.request_count,
            "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None,
            "session_active": self.session is not None
        }