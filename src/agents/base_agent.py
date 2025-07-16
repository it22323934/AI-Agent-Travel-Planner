"""
Base agent class with Ollama integration
Foundation for all travel planning agents
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime

from core.models import TaskStatus, OllamaConfig
from core.exceptions import AgentError, OllamaError
from config.settings import get_ollama_config


class BaseAgent(ABC):
    """
    Abstract base class for all travel planning agents
    Provides Ollama LLM integration and common functionality
    """
    
    def __init__(self, agent_name: str, system_prompt: str):
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.status = TaskStatus.PENDING
        self.logger = logging.getLogger(f"agent.{agent_name}")
        
        # Ollama configuration
        self.ollama_config = get_ollama_config()
        self.ollama_url = f"{self.ollama_config['base_url']}/api/generate"
        
        # Processing state
        self.current_task: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.output_data: Optional[Dict[str, Any]] = None
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent task with error handling and status tracking
        """
        try:
            self.set_status(TaskStatus.IN_PROGRESS)
            self.start_time = datetime.utcnow()
            self.log_action("Starting task execution")
            
            # Process the input data
            result = await self.process(input_data)
            
            self.output_data = result
            self.set_status(TaskStatus.COMPLETED)
            self.log_action("Task completed successfully")
            
            return result
            
        except Exception as e:
            self.error_message = str(e)
            self.set_status(TaskStatus.FAILED)
            self.log_action(f"Task failed: {e}")
            raise AgentError(f"Agent {self.agent_name} failed: {e}", self.agent_name)
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Abstract method for agent-specific processing
        Must be implemented by each agent
        """
        pass
    
    async def query_ollama(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Query Ollama LLM with prompt and optional context
        """
        try:
            # Prepare the full prompt with system context
            full_prompt = f"{self.system_prompt}\n\nUser Query: {prompt}"
            
            if context:
                context_str = json.dumps(context, indent=2)
                full_prompt += f"\n\nContext Data:\n{context_str}"
            
            # Prepare request payload
            payload = {
                "model": self.ollama_config["model"],
                "prompt": full_prompt,
                "temperature": self.ollama_config["temperature"],
                "max_tokens": self.ollama_config["max_tokens"],
                "stream": False
            }
            
            self.logger.debug(f"Querying Ollama with model: {self.ollama_config['model']}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.ollama_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        raise OllamaError(f"Ollama API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if "response" not in result:
                        raise OllamaError("Invalid response from Ollama")
                    
                    return result["response"].strip()
                    
        except aiohttp.ClientError as e:
            raise OllamaError(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            raise OllamaError(f"Ollama query failed: {e}")
    
    def set_status(self, status: TaskStatus, message: Optional[str] = None):
        """Update agent status"""
        self.status = status
        if message:
            self.error_message = message
        
        self.log_action(f"Status changed to {status.value}")
    
    def log_action(self, message: str, level: str = "info"):
        """Log agent actions"""
        log_message = f"[{self.agent_name}] {message}"
        
        if level == "debug":
            self.logger.debug(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        else:
            self.logger.info(log_message)
    
    def get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state"""
        return {
            "agent_name": self.agent_name,
            "status": self.status.value,
            "current_task": self.current_task,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "error_message": self.error_message,
            "has_output": self.output_data is not None
        }
    
    def format_prompt_with_data(self, template: str, **kwargs) -> str:
        """Format prompt template with provided data"""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            self.log_action(f"Missing template variable: {e}", "warning")
            return template
    
    async def validate_input(self, input_data: Dict[str, Any], required_fields: List[str]) -> bool:
        """Validate input data has required fields"""
        missing_fields = []
        
        for field in required_fields:
            if field not in input_data or input_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise AgentError(
                f"Missing required fields: {missing_fields}",
                self.agent_name
            )
        
        return True


class LLMAgent(BaseAgent):
    """
    Specialized agent for LLM-heavy tasks
    Provides advanced prompting and reasoning capabilities
    """
    
    def __init__(self, agent_name: str, system_prompt: str, reasoning_steps: List[str] = None):
        super().__init__(agent_name, system_prompt)
        self.reasoning_steps = reasoning_steps or []
    
    async def reason_through_problem(self, problem: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use step-by-step reasoning to solve a problem
        """
        reasoning_results = {}
        
        for i, step in enumerate(self.reasoning_steps):
            step_prompt = f"""
            Problem: {problem}
            
            Step {i+1}: {step}
            
            Previous reasoning: {json.dumps(reasoning_results, indent=2)}
            
            Provide your reasoning for this step:
            """
            
            step_result = await self.query_ollama(step_prompt, context)
            reasoning_results[f"step_{i+1}"] = {
                "description": step,
                "reasoning": step_result
            }
            
            self.log_action(f"Completed reasoning step {i+1}: {step}")
        
        # Final synthesis
        final_prompt = f"""
        Problem: {problem}
        
        Complete reasoning chain: {json.dumps(reasoning_results, indent=2)}
        
        Provide your final conclusion and recommendation:
        """
        
        final_result = await self.query_ollama(final_prompt, context)
        
        return {
            "problem": problem,
            "reasoning_steps": reasoning_results,
            "final_conclusion": final_result
        }
    
    async def analyze_and_recommend(self, data: Dict[str, Any], criteria: List[str]) -> Dict[str, Any]:
        """
        Analyze data against criteria and provide recommendations
        """
        analysis_prompt = f"""
        Analyze the following data against these criteria:
        {json.dumps(criteria, indent=2)}
        
        Provide:
        1. Analysis of how well the data meets each criterion
        2. Specific recommendations for improvement
        3. Risk assessment and mitigation strategies
        4. Priority ranking of recommendations
        
        Format your response as structured analysis with clear sections.
        """
        
        analysis_result = await self.query_ollama(analysis_prompt, data)
        
        return {
            "criteria": criteria,
            "analysis": analysis_result,
            "timestamp": datetime.utcnow().isoformat()
        }


class DataProcessingAgent(BaseAgent):
    """
    Specialized agent for data processing and transformation tasks
    """
    
    def __init__(self, agent_name: str, system_prompt: str):
        super().__init__(agent_name, system_prompt)
    
    async def process_and_filter_data(self, data: List[Dict[str, Any]], 
                                    filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process and filter data based on criteria
        """
        filtered_data = []
        
        for item in data:
            if self._meets_criteria(item, filters):
                filtered_data.append(item)
        
        self.log_action(f"Filtered {len(data)} items to {len(filtered_data)} items")
        return filtered_data
    
    def _meets_criteria(self, item: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """Check if item meets filter criteria"""
        for key, value in filters.items():
            if key not in item:
                continue
            
            item_value = item[key]
            
            # Handle different filter types
            if isinstance(value, dict):
                if "min" in value and item_value < value["min"]:
                    return False
                if "max" in value and item_value > value["max"]:
                    return False
            elif isinstance(value, list):
                if item_value not in value:
                    return False
            else:
                if item_value != value:
                    return False
        
        return True
    
    async def rank_items(self, items: List[Dict[str, Any]], 
                        ranking_criteria: List[str]) -> List[Dict[str, Any]]:
        """
        Rank items using LLM-based scoring
        """
        ranking_prompt = f"""
        Rank the following items based on these criteria:
        {json.dumps(ranking_criteria, indent=2)}
        
        For each item, provide a score from 1-10 for each criterion and explain your reasoning.
        Return the items in ranked order with scores.
        """
        
        ranking_result = await self.query_ollama(ranking_prompt, {"items": items})
        
        # For now, return original items (in production, parse LLM response)
        return items