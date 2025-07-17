"""
Complete LangGraph workflow definition for travel planning
Assembles all nodes into a coordinated graph execution
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from graph.state import TravelPlanningState, create_initial_state, StateManager
from graph.nodes import (
    planning_node,
    data_collection_node, 
    destination_research_node,
    local_expertise_node,
    should_continue_to_itinerary,
    handle_insufficient_data_node,
    itinerary_creation_node,
    trip_criticism_node,
    should_optimize_again,
    finalization_node
)
from core.models import TravelRequest, TravelItinerary
from core.exceptions import AgentError


logger = logging.getLogger("workflow")


class TravelPlanningWorkflow:
    """
    Main workflow orchestrator for travel planning
    Uses LangGraph to coordinate all agents and data flow
    """
    
    def __init__(self):
        self.graph = None
        self.state_manager = StateManager()
        self._build_graph()
    
    def _build_graph(self):
        """Build the complete LangGraph workflow"""
        logger.info("Building travel planning workflow graph")
        
        # Create the graph
        workflow = StateGraph(TravelPlanningState)
        
        # Add all nodes
        workflow.add_node("planning", planning_node)
        workflow.add_node("data_collection", data_collection_node)
        workflow.add_node("destination_research", destination_research_node)
        workflow.add_node("local_expertise", local_expertise_node)
        workflow.add_node("handle_insufficient_data", handle_insufficient_data_node)
        workflow.add_node("itinerary_creation", itinerary_creation_node)
        workflow.add_node("trip_criticism", trip_criticism_node)
        workflow.add_node("finalization", finalization_node)
        
        # Set entry point
        workflow.set_entry_point("planning")
        
        # Add edges for the workflow
        # Planning -> Data Collection
        workflow.add_edge("planning", "data_collection")
        
        # Data Collection -> Destination Research (parallel)
        workflow.add_edge("data_collection", "destination_research")
        
        # Destination Research -> Local Expertise
        workflow.add_edge("destination_research", "local_expertise")
        
        # Local Expertise -> Decision point
        workflow.add_conditional_edges(
            "local_expertise",
            should_continue_to_itinerary,
            {
                "create_itinerary": "itinerary_creation",
                "handle_insufficient_data": "handle_insufficient_data"
            }
        )
        
        # Insufficient data -> End
        workflow.add_edge("handle_insufficient_data", END)
        
        # Itinerary Creation -> Trip Criticism
        workflow.add_edge("itinerary_creation", "trip_criticism")
        
        # Trip Criticism -> Decision point for optimization
        workflow.add_conditional_edges(
            "trip_criticism",
            should_optimize_again,
            {
                "optimize_itinerary": "itinerary_creation",  # Loop back for re-optimization
                "finalization": "finalization"
            }
        )
        
        # Finalization -> End
        workflow.add_edge("finalization", END)
        
        # Compile the graph
        self.graph = workflow.compile()
        logger.info("Workflow graph compiled successfully")
    
    async def execute(self, travel_request: TravelRequest) -> TravelItinerary:
        """
        Execute the complete travel planning workflow
        """
        logger.info(f"Starting travel planning workflow for {travel_request.destination}")
        
        try:
            # Create initial state
            initial_state = create_initial_state(travel_request)
            self.state_manager.snapshot_state(initial_state, "initial")
            
            # Execute the graph
            logger.info("Executing workflow graph")
            final_state = await self.graph.ainvoke(initial_state)
            
            # Take final snapshot
            self.state_manager.snapshot_state(final_state, "final")
            
            # Check if we have a final itinerary
            if final_state.get("final_itinerary"):
                logger.info("Workflow completed successfully")
                return final_state["final_itinerary"]
            else:
                # Handle failure case
                error_messages = final_state.get("error_messages", [])
                error_summary = "; ".join(error_messages[-3:])  # Last 3 errors
                
                logger.error(f"Workflow failed to produce itinerary: {error_summary}")
                raise AgentError(f"Travel planning failed: {error_summary}")
        
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            raise
    
    async def execute_with_state_tracking(self, travel_request: TravelRequest) -> Dict[str, Any]:
        """
        Execute workflow with detailed state tracking for debugging
        """
        logger.info("Executing workflow with detailed state tracking")
        
        try:
            # Execute the workflow
            itinerary = await self.execute(travel_request)
            
            # Return results with state history
            return {
                "success": True,
                "itinerary": itinerary,
                "state_history": self.state_manager.get_state_history(),
                "execution_summary": self._create_execution_summary()
            }
            
        except Exception as e:
            logger.error(f"Workflow execution with tracking failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "state_history": self.state_manager.get_state_history(),
                "execution_summary": self._create_execution_summary()
            }
    
    def _create_execution_summary(self) -> Dict[str, Any]:
        """Create summary of workflow execution"""
        history = self.state_manager.get_state_history()
        
        if not history:
            return {"status": "no_execution_data"}
        
        initial_state = history[0] if history else {}
        final_state = history[-1] if history else {}
        
        return {
            "total_steps": len(history),
            "start_time": initial_state.get("timestamp"),
            "end_time": final_state.get("timestamp"),
            "completed_steps": final_state.get("summary", {}).get("completed_steps", []),
            "failed_steps": final_state.get("summary", {}).get("failed_steps", []),
            "final_status": "success" if final_state.get("summary", {}).get("has_final_itinerary") else "failed",
            "data_collected": final_state.get("summary", {}).get("data_collected", {}),
            "optimization_rounds": final_state.get("summary", {}).get("optimization_rounds", 0)
        }
    
    def reset_state_history(self):
        """Clear state history for new execution"""
        self.state_manager.clear_history()
    
    def get_workflow_diagram(self) -> str:
        """Get text representation of workflow structure"""
        return """
        Travel Planning Workflow:
        
        1. Planning Node
           ↓
        2. Data Collection Node (MCP → Google APIs)
           ↓  
        3. Destination Research Node (LLM Analysis)
           ↓
        4. Local Expertise Node (LLM Insights)
           ↓
        5. Decision: Sufficient Data?
           ├─ Yes → Itinerary Creation Node
           └─ No → Handle Insufficient Data → END
           
        6. Itinerary Creation Node (LLM Planning)
           ↓
        7. Trip Criticism Node (LLM Review)
           ↓
        8. Decision: Optimize Again?
           ├─ Yes → Loop back to Itinerary Creation
           └─ No → Finalization Node
           
        9. Finalization Node → END
        
        Key Features:
        - Parallel data collection from Google APIs
        - LLM-powered analysis and planning
        - Feedback loops for optimization
        - Error handling and recovery
        - State persistence throughout execution
        """


# Convenience function for simple execution
async def plan_travel(travel_request: TravelRequest) -> TravelItinerary:
    """
    Simple function to execute travel planning workflow
    """
    workflow = TravelPlanningWorkflow()
    return await workflow.execute(travel_request)


# Function for detailed execution with debugging
async def plan_travel_with_details(travel_request: TravelRequest) -> Dict[str, Any]:
    """
    Execute travel planning with detailed state tracking
    """
    workflow = TravelPlanningWorkflow()
    return await workflow.execute_with_state_tracking(travel_request)