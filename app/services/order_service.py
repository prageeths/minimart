"""Order service for handling order business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
from app.models.models import Order as OrderModel, OrderItem as OrderItemModel, Customer as CustomerModel
from app.schemas.schemas import OrderCreate, OrderUpdate, Order, OrderWithDetails
from app.database.database import SessionLocal


class OrderService:
    """Service for handling order operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_order(self, order_data: OrderCreate) -> Order:
        """Create a new order."""
        try:
            # Generate order number
            order_number = f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Calculate total amount
            total_amount = sum(item.quantity * item.unit_price for item in order_data.items)
            
            # Create order
            order = OrderModel(
                customer_id=order_data.customer_id,
                order_number=order_number,
                total_amount=total_amount,
                notes=order_data.notes
            )
            
            self.db.add(order)
            self.db.flush()  # Get the order ID
            
            # Create order items
            for item_data in order_data.items:
                order_item = OrderItemModel(
                    order_id=order.id,
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=item_data.unit_price,
                    total_price=item_data.quantity * item_data.unit_price
                )
                self.db.add(order_item)
            
            self.db.commit()
            self.db.refresh(order)
            
            return Order.from_orm(order)
            
        except Exception as e:
            self.db.rollback()
            raise e
    
    async def get_order_by_id(self, order_id: int) -> Optional[OrderWithDetails]:
        """Get order by ID with all details."""
        order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        
        if not order:
            return None
        
        return OrderWithDetails.from_orm(order)
    
    async def get_orders(self, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders with pagination."""
        orders = self.db.query(OrderModel).offset(skip).limit(limit).all()
        return [Order.from_orm(order) for order in orders]
    
    async def get_orders_by_customer_id(self, customer_id: int, skip: int = 0, limit: int = 50) -> List[Order]:
        """Get orders for a specific customer."""
        orders = self.db.query(OrderModel).filter(
            OrderModel.customer_id == customer_id
        ).offset(skip).limit(limit).all()
        
        return [Order.from_orm(order) for order in orders]
    
    async def update_order(self, order_id: int, order_update: OrderUpdate) -> Optional[Order]:
        """Update an existing order."""
        order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        
        if not order:
            return None
        
        # Update fields
        update_data = order_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        self.db.commit()
        self.db.refresh(order)
        
        return Order.from_orm(order)
    
    async def process_payment(self, order_id: int, payment_data: dict) -> dict:
        """Process payment for an order (fake payment gateway)."""
        order = self.db.query(OrderModel).filter(OrderModel.id == order_id).first()
        
        if not order:
            raise ValueError("Order not found")
        
        # Simulate payment processing
        payment_reference = f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Update order status
        order.status = "confirmed"
        order.payment_status = "paid"
        order.payment_method = payment_data.get("payment_method", "credit_card")
        order.payment_reference = payment_reference
        
        self.db.commit()
        
        return {
            "payment_reference": payment_reference,
            "status": "success",
            "amount": order.total_amount
        }
