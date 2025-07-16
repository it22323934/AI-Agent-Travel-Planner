"""
Custom exceptions for the travel planning system
"""


class TravelPlannerError(Exception):
    """Base exception for travel planner"""
    pass


class ValidationError(TravelPlannerError):
    """Input validation error"""
    pass


class APIError(TravelPlannerError):
    """External API error"""
    def __init__(self, message: str, service: str = "unknown"):
        self.service = service
        super().__init__(message)


class GoogleAPIError(APIError):
    """Google API specific error"""
    def __init__(self, message: str, api_name: str = "google"):
        super().__init__(message, api_name)


class AgentError(TravelPlannerError):
    """Agent processing error"""
    def __init__(self, message: str, agent_name: str = "unknown"):
        self.agent_name = agent_name
        super().__init__(message)


class MCPError(TravelPlannerError):
    """MCP connector error"""
    pass


class OllamaError(TravelPlannerError):
    """Ollama LLM error"""
    pass