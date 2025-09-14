"""Order management API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.database import get_db
from app.schemas.schemas import (
    OrderCreate, Order, OrderWithDetails, OrderUpdate,
    OrderItemCreate, CustomerCreate, Customer
)
from app.models.models import Order as OrderModel, OrderItem as OrderItemModel, Customer as CustomerModel, Inventory
from app.services.order_service import OrderService
from app.services.inventory_service import InventoryService

router = APIRouter()


@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db)
):
    """Create a new customer order."""
    try:
        order_service = OrderService(db)
        inventory_service = InventoryService(db)
        
        # Check inventory availability for all items
        for item in order_data.items:
            inventory = inventory_service.get_inventory_by_product_id(item.product_id)
            if not inventory or inventory.available_stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for product ID {item.product_id}"
                )
        
        # Create the order
        order = await order_service.create_order(order_data)
        
        # Update inventory levels
        for item in order_data.items:
            await inventory_service.reduce_inventory(
                item.product_id, 
                item.quantity,
                f"Order {order.order_number}"
            )
        
        return order
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/", response_model=List[Order])
async def get_orders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all orders with pagination."""
    try:
        order_service = OrderService(db)
        orders = await order_service.get_orders(skip=skip, limit=limit)
        return orders
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=OrderWithDetails)
async def get_order(
    order_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific order by ID."""
    try:
        order_service = OrderService(db)
        order = await order_service.get_order_by_id(order_id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/{order_id}", response_model=Order)
async def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing order."""
    try:
        order_service = OrderService(db)
        order = await order_service.update_order(order_id, order_update)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return order
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/{order_id}/process-payment", response_model=dict)
async def process_payment(
    order_id: int,
    payment_data: dict,
    db: Session = Depends(get_db)
):
    """Process payment for an order (fake payment gateway)."""
    try:
        order_service = OrderService(db)
        
        # Simulate payment processing
        payment_result = await order_service.process_payment(order_id, payment_data)
        
        return {
            "success": True,
            "message": "Payment processed successfully",
            "payment_reference": payment_result.get("payment_reference"),
            "order_status": "confirmed"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/customer/{customer_id}", response_model=List[Order])
async def get_customer_orders(
    customer_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get orders for a specific customer."""
    try:
        order_service = OrderService(db)
        orders = await order_service.get_orders_by_customer_id(
            customer_id, skip=skip, limit=limit
        )
        return orders
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
