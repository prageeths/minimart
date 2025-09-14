"""AI Agents API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database.database import get_db
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.demand_forecast_agent import DemandForecastAgent
from app.agents.order_placement_agent import OrderPlacementAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.logistics_agent import LogisticsAgent
from app.rag.rag_system import RAGSystem

router = APIRouter()


@router.post("/workflow/inventory-management", response_model=dict)
async def execute_inventory_management_workflow(
    product_ids: List[int],
    db: Session = Depends(get_db)
):
    """Execute the complete inventory management workflow."""
    try:
        supervisor_agent = SupervisorAgent()
        result = await supervisor_agent.execute_inventory_management_workflow(product_ids)
        
        return {
            "success": True,
            "message": "Inventory management workflow completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/workflow/emergency-reorder", response_model=dict)
async def execute_emergency_reorder_workflow(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    """Execute emergency reorder workflow."""
    try:
        supervisor_agent = SupervisorAgent()
        result = await supervisor_agent.execute_emergency_reorder_workflow(product_id, quantity)
        
        return {
            "success": True,
            "message": "Emergency reorder workflow completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/workflow/supplier-performance-review", response_model=dict)
async def execute_supplier_performance_review(
    db: Session = Depends(get_db)
):
    """Execute supplier performance review workflow."""
    try:
        supervisor_agent = SupervisorAgent()
        result = await supervisor_agent.execute_supplier_performance_review()
        
        return {
            "success": True,
            "message": "Supplier performance review completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/demand-forecast", response_model=dict)
async def execute_demand_forecast(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute demand forecasting for products."""
    try:
        demand_forecast_agent = DemandForecastAgent()
        result = await demand_forecast_agent.execute(request_data)
        
        return {
            "success": True,
            "message": "Demand forecasting completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/order-placement", response_model=dict)
async def execute_order_placement(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute order placement logic."""
    try:
        order_placement_agent = OrderPlacementAgent()
        result = await order_placement_agent.execute(request_data)
        
        return {
            "success": True,
            "message": "Order placement completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/supplier-negotiation", response_model=dict)
async def execute_supplier_negotiation(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute supplier negotiation."""
    try:
        supplier_agent = SupplierAgent()
        result = await supplier_agent.execute(request_data)
        
        return {
            "success": True,
            "message": "Supplier negotiation completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/logistics-tracking", response_model=dict)
async def execute_logistics_tracking(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Execute logistics tracking and coordination."""
    try:
        logistics_agent = LogisticsAgent()
        result = await logistics_agent.execute(request_data)
        
        return {
            "success": True,
            "message": "Logistics tracking completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rag/query", response_model=dict)
async def query_knowledge_base(
    query: str,
    collection: str = "all",
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """Query the RAG knowledge base."""
    try:
        rag_system = RAGSystem()
        result = await rag_system.query_knowledge_base(query, collection, limit)
        
        return {
            "success": True,
            "message": "Knowledge base query completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/rag/build-knowledge-base", response_model=dict)
async def build_knowledge_base(
    db: Session = Depends(get_db)
):
    """Build or rebuild the RAG knowledge base."""
    try:
        rag_system = RAGSystem()
        result = await rag_system.build_knowledge_base()
        
        return {
            "success": True,
            "message": "Knowledge base build completed",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rag/product-insights/{product_id}", response_model=dict)
async def get_product_insights(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive insights for a specific product using RAG."""
    try:
        rag_system = RAGSystem()
        result = await rag_system.get_product_insights(product_id)
        
        return {
            "success": True,
            "message": f"Product insights generated for product {product_id}",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rag/inventory-recommendations", response_model=dict)
async def get_inventory_recommendations(
    db: Session = Depends(get_db)
):
    """Get inventory management recommendations using RAG."""
    try:
        rag_system = RAGSystem()
        result = await rag_system.get_inventory_recommendations()
        
        return {
            "success": True,
            "message": "Inventory recommendations generated",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/rag/agent-decisions", response_model=dict)
async def search_agent_decisions(
    search_term: str,
    db: Session = Depends(get_db)
):
    """Search through agent decision logs using RAG."""
    try:
        rag_system = RAGSystem()
        result = await rag_system.search_agent_decisions(search_term)
        
        return {
            "success": True,
            "message": f"Agent decisions search completed for: {search_term}",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
