"""Inventory service for handling inventory business logic."""

from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.models import Inventory as InventoryModel, Product, SalesTransaction
from app.schemas.schemas import InventoryUpdate, InventoryWithProduct, InventoryAlert
from app.database.database import SessionLocal


class InventoryService:
    """Service for handling inventory operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_all_inventory(self, skip: int = 0, limit: int = 100) -> List[InventoryWithProduct]:
        """Get all inventory items with product details."""
        inventory_items = self.db.query(InventoryModel, Product).join(
            Product, InventoryModel.product_id == Product.id
        ).offset(skip).limit(limit).all()
        
        result = []
        for inventory, product in inventory_items:
            inventory_with_product = InventoryWithProduct.from_orm(inventory)
            inventory_with_product.product = product
            result.append(inventory_with_product)
        
        return result
    
    async def get_inventory_by_product_id(self, product_id: int) -> Optional[InventoryWithProduct]:
        """Get inventory for a specific product."""
        inventory = self.db.query(InventoryModel, Product).join(
            Product, InventoryModel.product_id == Product.id
        ).filter(InventoryModel.product_id == product_id).first()
        
        if not inventory:
            return None
        
        inventory_model, product = inventory
        inventory_with_product = InventoryWithProduct.from_orm(inventory_model)
        inventory_with_product.product = product
        
        return inventory_with_product
    
    async def update_inventory(self, product_id: int, inventory_update: InventoryUpdate) -> Optional[InventoryModel]:
        """Update inventory for a specific product."""
        inventory = self.db.query(InventoryModel).filter(
            InventoryModel.product_id == product_id
        ).first()
        
        if not inventory:
            return None
        
        # Update fields
        update_data = inventory_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(inventory, field, value)
        
        # Recalculate available stock
        inventory.available_stock = inventory.current_stock - inventory.reserved_stock
        
        self.db.commit()
        self.db.refresh(inventory)
        
        return inventory
    
    async def reduce_inventory(self, product_id: int, quantity: int, reason: str = "") -> bool:
        """Reduce inventory for a product."""
        inventory = self.db.query(InventoryModel).filter(
            InventoryModel.product_id == product_id
        ).first()
        
        if not inventory:
            return False
        
        if inventory.available_stock < quantity:
            return False
        
        # Reduce current stock
        inventory.current_stock -= quantity
        inventory.available_stock = inventory.current_stock - inventory.reserved_stock
        inventory.last_updated = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    async def increase_inventory(self, product_id: int, quantity: int, reason: str = "") -> bool:
        """Increase inventory for a product."""
        inventory = self.db.query(InventoryModel).filter(
            InventoryModel.product_id == product_id
        ).first()
        
        if not inventory:
            return False
        
        # Increase current stock
        inventory.current_stock += quantity
        inventory.available_stock = inventory.current_stock - inventory.reserved_stock
        inventory.last_updated = datetime.utcnow()
        
        self.db.commit()
        
        return True
    
    async def reserve_inventory(self, product_id: int, quantity: int) -> bool:
        """Reserve inventory for a pending order."""
        inventory = self.db.query(InventoryModel).filter(
            InventoryModel.product_id == product_id
        ).first()
        
        if not inventory:
            return False
        
        if inventory.available_stock < quantity:
            return False
        
        # Reserve stock
        inventory.reserved_stock += quantity
        inventory.available_stock = inventory.current_stock - inventory.reserved_stock
        
        self.db.commit()
        
        return True
    
    async def release_reserved_inventory(self, product_id: int, quantity: int) -> bool:
        """Release reserved inventory."""
        inventory = self.db.query(InventoryModel).filter(
            InventoryModel.product_id == product_id
        ).first()
        
        if not inventory:
            return False
        
        # Release reserved stock
        inventory.reserved_stock = max(0, inventory.reserved_stock - quantity)
        inventory.available_stock = inventory.current_stock - inventory.reserved_stock
        
        self.db.commit()
        
        return True
    
    async def get_low_stock_alerts(self) -> List[InventoryAlert]:
        """Get low stock alerts."""
        inventory_items = self.db.query(InventoryModel, Product).join(
            Product, InventoryModel.product_id == Product.id
        ).all()
        
        alerts = []
        for inventory, product in inventory_items:
            if inventory.current_stock <= inventory.safety_stock:
                alert_type = "out_of_stock" if inventory.current_stock == 0 else "low_stock"
                
                alerts.append(InventoryAlert(
                    product_id=product.id,
                    product_name=product.name,
                    current_stock=inventory.current_stock,
                    reorder_point=inventory.reorder_point,
                    alert_type=alert_type
                ))
        
        return alerts
    
    async def get_sales_trends(self, days: int = 30) -> dict:
        """Get sales trends for the specified period."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get sales transactions for the period
        sales_data = self.db.query(SalesTransaction, Product).join(
            Product, SalesTransaction.product_id == Product.id
        ).filter(
            SalesTransaction.transaction_date >= start_date,
            SalesTransaction.transaction_date <= end_date
        ).all()
        
        # Group by product
        product_sales = {}
        for transaction, product in sales_data:
            if product.id not in product_sales:
                product_sales[product.id] = {
                    'product_name': product.name,
                    'total_quantity': 0,
                    'total_revenue': 0,
                    'transaction_count': 0
                }
            
            product_sales[product.id]['total_quantity'] += transaction.quantity
            product_sales[product.id]['total_revenue'] += transaction.total_amount
            product_sales[product.id]['transaction_count'] += 1
        
        # Calculate trends
        trends = []
        for product_id, sales in product_sales.items():
            avg_daily_sales = sales['total_quantity'] / days
            avg_daily_revenue = sales['total_revenue'] / days
            
            trends.append({
                'product_id': product_id,
                'product_name': sales['product_name'],
                'total_quantity': sales['total_quantity'],
                'total_revenue': sales['total_revenue'],
                'transaction_count': sales['transaction_count'],
                'avg_daily_sales': avg_daily_sales,
                'avg_daily_revenue': avg_daily_revenue
            })
        
        # Sort by total revenue
        trends.sort(key=lambda x: x['total_revenue'], reverse=True)
        
        return {
            'period_days': days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'total_products': len(trends),
            'trends': trends
        }
    
    async def get_inventory_performance(self) -> dict:
        """Get inventory performance metrics."""
        # Get all inventory items
        inventory_items = self.db.query(InventoryModel, Product).join(
            Product, InventoryModel.product_id == Product.id
        ).all()
        
        total_products = len(inventory_items)
        low_stock_count = 0
        out_of_stock_count = 0
        overstock_count = 0
        total_inventory_value = 0
        
        for inventory, product in inventory_items:
            # Check stock levels
            if inventory.current_stock <= inventory.safety_stock:
                if inventory.current_stock == 0:
                    out_of_stock_count += 1
                else:
                    low_stock_count += 1
            elif inventory.current_stock > inventory.maximum_stock:
                overstock_count += 1
            
            # Calculate inventory value
            total_inventory_value += inventory.current_stock * product.cost_price
        
        # Calculate performance metrics
        stock_availability = ((total_products - out_of_stock_count) / total_products * 100) if total_products > 0 else 0
        optimal_stock_level = ((total_products - low_stock_count - overstock_count) / total_products * 100) if total_products > 0 else 0
        
        return {
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'out_of_stock_count': out_of_stock_count,
            'overstock_count': overstock_count,
            'stock_availability_percentage': stock_availability,
            'optimal_stock_percentage': optimal_stock_level,
            'total_inventory_value': total_inventory_value,
            'generated_at': datetime.utcnow().isoformat()
        }
