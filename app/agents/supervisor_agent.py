"""Supervisor Agent for orchestrating multi-agent workflows using LangGraph."""

import asyncio
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from datetime import datetime
import json
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from app.agents.base_agent import BaseAgent
from app.agents.demand_forecast_agent import DemandForecastAgent
from app.agents.order_placement_agent import OrderPlacementAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.logistics_agent import LogisticsAgent
from app.models.models import AgentType


class AgentState(TypedDict):
    """State for the multi-agent workflow."""
    messages: Annotated[List[Dict[str, Any]], add_messages]
    current_task: str
    task_data: Dict[str, Any]
    agent_results: Dict[str, Any]
    workflow_status: str
    error_message: Optional[str]
    execution_log: List[Dict[str, Any]]


class SupervisorAgent(BaseAgent):
    """Supervisor agent that orchestrates the multi-agent workflow using LangGraph."""
    
    def __init__(self):
        super().__init__(AgentType.SUPERVISOR)
        self.demand_forecast_agent = DemandForecastAgent()
        self.order_placement_agent = OrderPlacementAgent()
        self.supplier_agent = SupplierAgent()
        self.logistics_agent = LogisticsAgent()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for multi-agent coordination."""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes for each agent
        workflow.add_node("demand_forecast", self._demand_forecast_node)
        workflow.add_node("order_placement", self._order_placement_node)
        workflow.add_node("supplier_negotiation", self._supplier_negotiation_node)
        workflow.add_node("logistics_coordination", self._logistics_coordination_node)
        workflow.add_node("decision_making", self._decision_making_node)
        workflow.add_node("error_handling", self._error_handling_node)
        
        # Define the workflow edges
        workflow.set_entry_point("decision_making")
        
        # Decision making routes to appropriate agents
        workflow.add_conditional_edges(
            "decision_making",
            self._route_decision,
            {
                "demand_forecast": "demand_forecast",
                "order_placement": "order_placement",
                "supplier_negotiation": "supplier_negotiation",
                "logistics_coordination": "logistics_coordination",
                "error": "error_handling",
                "end": END
            }
        )
        
        # Agent execution flows
        workflow.add_edge("demand_forecast", "decision_making")
        workflow.add_edge("order_placement", "decision_making")
        workflow.add_edge("supplier_negotiation", "decision_making")
        workflow.add_edge("logistics_coordination", "decision_making")
        workflow.add_edge("error_handling", END)
        
        return workflow.compile()
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the supervisor workflow."""
        start_time = datetime.utcnow()
        
        try:
            # Initialize the workflow state
            initial_state = AgentState(
                messages=[],
                current_task=input_data.get('task', 'inventory_management'),
                task_data=input_data,
                agent_results={},
                workflow_status='running',
                error_message=None,
                execution_log=[]
            )
            
            # Execute the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'workflow_completed': True,
                'final_status': final_state['workflow_status'],
                'agent_results': final_state['agent_results'],
                'execution_log': final_state['execution_log'],
                'total_execution_time_ms': execution_time,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="supervisor_workflow",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        except Exception as e:
            self.logger.error(f"Error in supervisor workflow: {e}")
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.log_action(
                action="supervisor_workflow",
                input_data=input_data,
                output_data={},
                status="error",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            return self.create_error_response(f"Supervisor workflow failed: {str(e)}")
    
    async def _decision_making_node(self, state: AgentState) -> AgentState:
        """Decision making node that routes to appropriate agents."""
        try:
            task = state['current_task']
            task_data = state['task_data']
            
            # Log the decision
            state['execution_log'].append({
                'node': 'decision_making',
                'timestamp': datetime.utcnow().isoformat(),
                'task': task,
                'action': 'routing_decision'
            })
            
            # Route based on task type
            if task == 'demand_forecast':
                state['workflow_status'] = 'routing_to_demand_forecast'
            elif task == 'check_reorder_points':
                state['workflow_status'] = 'routing_to_order_placement'
            elif task == 'supplier_negotiation':
                state['workflow_status'] = 'routing_to_supplier_negotiation'
            elif task == 'logistics_tracking':
                state['workflow_status'] = 'routing_to_logistics_coordination'
            elif task == 'inventory_management':
                # Complex workflow - start with demand forecast
                state['workflow_status'] = 'routing_to_demand_forecast'
            else:
                state['workflow_status'] = 'error'
                state['error_message'] = f"Unknown task: {task}"
            
            return state
            
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = str(e)
            return state
    
    async def _demand_forecast_node(self, state: AgentState) -> AgentState:
        """Execute demand forecasting."""
        try:
            task_data = state['task_data']
            
            # Log the execution
            state['execution_log'].append({
                'node': 'demand_forecast',
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'executing_demand_forecast'
            })
            
            # Execute demand forecasting
            if 'product_ids' in task_data:
                forecast_result = await self.demand_forecast_agent.execute(task_data)
                state['agent_results']['demand_forecast'] = forecast_result
                
                # If this is part of inventory management workflow, continue to order placement
                if state['current_task'] == 'inventory_management':
                    state['current_task'] = 'check_reorder_points'
                    # Add forecast data to task data for order placement
                    if forecast_result.get('success'):
                        state['task_data']['forecast_data'] = forecast_result['data']
            
            state['workflow_status'] = 'demand_forecast_completed'
            return state
            
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = f"Demand forecast failed: {str(e)}"
            return state
    
    async def _order_placement_node(self, state: AgentState) -> AgentState:
        """Execute order placement logic."""
        try:
            task_data = state['task_data']
            
            # Log the execution
            state['execution_log'].append({
                'node': 'order_placement',
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'executing_order_placement'
            })
            
            # Execute order placement
            order_result = await self.order_placement_agent.execute(task_data)
            state['agent_results']['order_placement'] = order_result
            
            # If orders were placed, continue to supplier negotiation
            if order_result.get('success') and order_result['data'].get('reorder_candidates'):
                state['current_task'] = 'supplier_negotiation'
                # Add order data to task data for supplier negotiation
                state['task_data']['order_data'] = order_result['data']
            
            state['workflow_status'] = 'order_placement_completed'
            return state
            
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = f"Order placement failed: {str(e)}"
            return state
    
    async def _supplier_negotiation_node(self, state: AgentState) -> AgentState:
        """Execute supplier negotiation."""
        try:
            task_data = state['task_data']
            
            # Log the execution
            state['execution_log'].append({
                'node': 'supplier_negotiation',
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'executing_supplier_negotiation'
            })
            
            # Execute supplier negotiation
            supplier_result = await self.supplier_agent.execute(task_data)
            state['agent_results']['supplier_negotiation'] = supplier_result
            
            # If supplier negotiations are successful, continue to logistics
            if supplier_result.get('success'):
                state['current_task'] = 'logistics_tracking'
                # Add supplier data to task data for logistics
                state['task_data']['supplier_data'] = supplier_result['data']
            
            state['workflow_status'] = 'supplier_negotiation_completed'
            return state
            
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = f"Supplier negotiation failed: {str(e)}"
            return state
    
    async def _logistics_coordination_node(self, state: AgentState) -> AgentState:
        """Execute logistics coordination."""
        try:
            task_data = state['task_data']
            
            # Log the execution
            state['execution_log'].append({
                'node': 'logistics_coordination',
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'executing_logistics_coordination'
            })
            
            # Execute logistics coordination
            logistics_result = await self.logistics_agent.execute(task_data)
            state['agent_results']['logistics_coordination'] = logistics_result
            
            state['workflow_status'] = 'logistics_coordination_completed'
            return state
            
        except Exception as e:
            state['workflow_status'] = 'error'
            state['error_message'] = f"Logistics coordination failed: {str(e)}"
            return state
    
    async def _error_handling_node(self, state: AgentState) -> AgentState:
        """Handle errors in the workflow."""
        try:
            # Log the error
            state['execution_log'].append({
                'node': 'error_handling',
                'timestamp': datetime.utcnow().isoformat(),
                'action': 'handling_error',
                'error': state['error_message']
            })
            
            # Implement error recovery strategies
            error_recovery = await self._implement_error_recovery(state)
            state['agent_results']['error_recovery'] = error_recovery
            
            state['workflow_status'] = 'error_handled'
            return state
            
        except Exception as e:
            state['workflow_status'] = 'critical_error'
            state['error_message'] = f"Error handling failed: {str(e)}"
            return state
    
    def _route_decision(self, state: AgentState) -> str:
        """Route decision based on current state."""
        if state['workflow_status'] == 'error':
            return "error"
        elif state['workflow_status'] == 'routing_to_demand_forecast':
            return "demand_forecast"
        elif state['workflow_status'] == 'routing_to_order_placement':
            return "order_placement"
        elif state['workflow_status'] == 'routing_to_supplier_negotiation':
            return "supplier_negotiation"
        elif state['workflow_status'] == 'routing_to_logistics_coordination':
            return "logistics_coordination"
        elif state['workflow_status'] in ['demand_forecast_completed', 'order_placement_completed', 
                                        'supplier_negotiation_completed', 'logistics_coordination_completed']:
            return "end"
        else:
            return "error"
    
    async def _implement_error_recovery(self, state: AgentState) -> Dict[str, Any]:
        """Implement error recovery strategies."""
        error_message = state['error_message']
        
        recovery_strategies = {
            'retry': {
                'action': 'retry_failed_operation',
                'max_retries': 3,
                'backoff_seconds': 5
            },
            'fallback': {
                'action': 'use_fallback_method',
                'fallback_agent': 'manual_intervention'
            },
            'escalation': {
                'action': 'escalate_to_human',
                'priority': 'high',
                'notification_method': 'email'
            }
        }
        
        # Determine recovery strategy based on error type
        if 'timeout' in error_message.lower():
            return recovery_strategies['retry']
        elif 'connection' in error_message.lower():
            return recovery_strategies['retry']
        elif 'validation' in error_message.lower():
            return recovery_strategies['fallback']
        else:
            return recovery_strategies['escalation']
    
    async def execute_inventory_management_workflow(self, product_ids: List[int]) -> Dict[str, Any]:
        """Execute the complete inventory management workflow."""
        workflow_input = {
            'task': 'inventory_management',
            'product_ids': product_ids,
            'forecast_period_days': 30,
            'action': 'check_reorder_points'
        }
        
        return await self.execute(workflow_input)
    
    async def execute_emergency_reorder_workflow(self, product_id: int, quantity: int) -> Dict[str, Any]:
        """Execute emergency reorder workflow."""
        workflow_input = {
            'task': 'emergency_reorder',
            'product_id': product_id,
            'quantity': quantity,
            'urgency': 'emergency',
            'action': 'place_emergency_order'
        }
        
        return await self.execute(workflow_input)
    
    async def execute_supplier_performance_review(self) -> Dict[str, Any]:
        """Execute supplier performance review workflow."""
        workflow_input = {
            'task': 'supplier_performance_review',
            'action': 'evaluate_supplier_performance'
        }
        
        return await self.execute(workflow_input)
