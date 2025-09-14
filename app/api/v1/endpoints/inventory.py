"""Inventory management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.schemas.schemas import (
    Inventory, InventoryWithProduct, InventoryUpdate, InventoryAlert
)
from app.services.inventory_service import InventoryService
from app.agents.supervisor_agent import SupervisorAgent

router = APIRouter()


@router.get("/", response_model=List[InventoryWithProduct])
async def get_inventory(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all inventory items with product details."""
    try:
        inventory_service = InventoryService(db)
        inventory_items = await inventory_service.get_all_inventory(skip=skip, limit=limit)
        return inventory_items
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{product_id}", response_model=InventoryWithProduct)
async def get_inventory_by_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get inventory for a specific product."""
    try:
        inventory_service = InventoryService(db)
        inventory = await inventory_service.get_inventory_by_product_id(product_id)
        
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found for this product"
            )
        
        return inventory
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{product_id}", response_model=Inventory)
async def update_inventory(
    product_id: int,
    inventory_update: InventoryUpdate,
    db: Session = Depends(get_db)
):
    """Update inventory for a specific product."""
    try:
        inventory_service = InventoryService(db)
        inventory = await inventory_service.update_inventory(product_id, inventory_update)
        
        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found for this product"
            )
        
        return inventory
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/alerts/low-stock", response_model=List[InventoryAlert])
async def get_low_stock_alerts(
    db: Session = Depends(get_db)
):
    """Get low stock alerts."""
    try:
        inventory_service = InventoryService(db)
        alerts = await inventory_service.get_low_stock_alerts()
        return alerts
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reorder-check", response_model=dict)
async def check_reorder_points(
    db: Session = Depends(get_db)
):
    """Trigger reorder point check using AI agents."""
    try:
        supervisor_agent = SupervisorAgent()
        
        # Get all product IDs for reorder check
        inventory_service = InventoryService(db)
        all_inventory = await inventory_service.get_all_inventory()
        product_ids = [inv.product_id for inv in all_inventory]
        
        # Execute inventory management workflow
        result = await supervisor_agent.execute_inventory_management_workflow(product_ids)
        
        return {
            "success": True,
            "message": "Reorder check completed",
            "workflow_result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/emergency-reorder/{product_id}", response_model=dict)
async def emergency_reorder(
    product_id: int,
    quantity: int,
    db: Session = Depends(get_db)
):
    """Trigger emergency reorder for a specific product."""
    try:
        supervisor_agent = SupervisorAgent()
        
        # Execute emergency reorder workflow
        result = await supervisor_agent.execute_emergency_reorder_workflow(product_id, quantity)
        
        return {
            "success": True,
            "message": f"Emergency reorder initiated for product {product_id}",
            "workflow_result": result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/analytics/sales-trends", response_model=dict)
async def get_sales_trends(
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get sales trends and analytics."""
    try:
        inventory_service = InventoryService(db)
        trends = await inventory_service.get_sales_trends(days=days)
        return trends
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/analytics/performance", response_model=dict)
async def get_inventory_performance(
    db: Session = Depends(get_db)
):
    """Get inventory performance metrics."""
    try:
        inventory_service = InventoryService(db)
        performance = await inventory_service.get_inventory_performance()
        return performance
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
