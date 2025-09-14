"""Order Placement Agent for managing inventory reordering decisions."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from app.agents.base_agent import BaseAgent
from app.agents.demand_forecast_agent import DemandForecastAgent
from app.models.models import (
    AgentType, Product, Inventory, SupplierProduct, 
    OrderStatus, ProcurementTransaction, Shipment
)
from app.database.database import SessionLocal
from app.core.config import settings


class OrderPlacementAgent(BaseAgent):
    """Agent responsible for making reordering decisions based on inventory levels and demand forecasts."""
    
    def __init__(self):
        super().__init__(AgentType.ORDER_PLACEMENT)
        self.demand_forecast_agent = DemandForecastAgent()
        self.reorder_check_interval_hours = 6  # Check every 6 hours
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute order placement logic."""
        start_time = datetime.utcnow()
        
        try:
            action = input_data.get('action', 'check_reorder_points')
            
            if action == 'check_reorder_points':
                return await self._check_reorder_points(input_data)
            elif action == 'place_emergency_order':
                return await self._place_emergency_order(input_data)
            elif action == 'optimize_order_quantities':
                return await self._optimize_order_quantities(input_data)
            else:
                return self.create_error_response(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error in order placement: {e}")
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.log_action(
                action=input_data.get('action', 'unknown'),
                input_data=input_data,
                output_data={},
                status="error",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            return self.create_error_response(f"Order placement failed: {str(e)}")
    
    async def _check_reorder_points(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if any products need reordering."""
        start_time = datetime.utcnow()
        
        db = SessionLocal()
        try:
            # Get all products with their inventory levels
            products_with_inventory = db.query(Product, Inventory).join(
                Inventory, Product.id == Inventory.product_id
            ).filter(Product.is_active == True).all()
            
            reorder_candidates = []
            emergency_reorders = []
            
            for product, inventory in products_with_inventory:
                # Check if current stock is below reorder point
                if inventory.current_stock <= inventory.reorder_point:
                    # Check if it's an emergency (below safety stock)
                    if inventory.current_stock <= inventory.safety_stock:
                        emergency_reorders.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'current_stock': inventory.current_stock,
                            'safety_stock': inventory.safety_stock,
                            'reorder_point': inventory.reorder_point,
                            'urgency': 'emergency'
                        })
                    else:
                        reorder_candidates.append({
                            'product_id': product.id,
                            'product_name': product.name,
                            'current_stock': inventory.current_stock,
                            'reorder_point': inventory.reorder_point,
                            'reorder_quantity': inventory.reorder_quantity,
                            'urgency': 'normal'
                        })
            
            # Get demand forecasts for reorder candidates
            if reorder_candidates or emergency_reorders:
                all_product_ids = [item['product_id'] for item in reorder_candidates + emergency_reorders]
                
                # Request demand forecast
                forecast_request = {
                    'product_ids': all_product_ids,
                    'forecast_period_days': 30
                }
                
                await self.send_request(AgentType.DEMAND_FORECAST, forecast_request)
                forecast_result = await self.demand_forecast_agent.execute(forecast_request)
                
                # Enhance reorder decisions with forecast data
                enhanced_candidates = await self._enhance_reorder_decisions(
                    reorder_candidates, forecast_result
                )
                enhanced_emergency = await self._enhance_reorder_decisions(
                    emergency_reorders, forecast_result
                )
            else:
                enhanced_candidates = reorder_candidates
                enhanced_emergency = emergency_reorders
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'reorder_candidates': enhanced_candidates,
                'emergency_reorders': enhanced_emergency,
                'total_products_checked': len(products_with_inventory),
                'checked_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="check_reorder_points",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _place_emergency_order(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place emergency orders for products below safety stock."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['product_id', 'quantity']):
            return self.create_error_response("Missing required fields: product_id, quantity")
        
        product_id = input_data['product_id']
        quantity = input_data['quantity']
        
        db = SessionLocal()
        try:
            # Get product and inventory information
            product = db.query(Product).filter(Product.id == product_id).first()
            inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
            
            if not product or not inventory:
                return self.create_error_response("Product or inventory not found")
            
            # Get suppliers for this product
            suppliers = db.query(SupplierProduct).filter(
                SupplierProduct.product_id == product_id
            ).all()
            
            if not suppliers:
                return self.create_error_response("No suppliers found for this product")
            
            # Select best supplier (preferred or lowest cost)
            best_supplier = min(suppliers, key=lambda s: s.unit_cost if not s.is_preferred else 0)
            
            # Create shipment record
            shipment = Shipment(
                supplier_id=best_supplier.supplier_id,
                shipment_number=f"EMERGENCY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                status='pending',
                expected_delivery_date=datetime.utcnow() + timedelta(days=best_supplier.lead_time_days),
                notes=f"Emergency reorder for {product.name} - Stock: {inventory.current_stock}"
            )
            db.add(shipment)
            db.commit()
            db.refresh(shipment)
            
            # Create procurement transaction
            procurement = ProcurementTransaction(
                product_id=product_id,
                supplier_id=best_supplier.supplier_id,
                shipment_id=shipment.id,
                quantity=quantity,
                unit_cost=best_supplier.unit_cost,
                total_cost=quantity * best_supplier.unit_cost
            )
            db.add(procurement)
            db.commit()
            
            # Notify supplier agent
            supplier_request = {
                'action': 'send_emergency_rfq',
                'product_id': product_id,
                'quantity': quantity,
                'supplier_id': best_supplier.supplier_id,
                'shipment_id': shipment.id,
                'urgency': 'emergency'
            }
            
            await self.send_request(AgentType.SUPPLIER, supplier_request)
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'order_placed': True,
                'product_id': product_id,
                'product_name': product.name,
                'quantity': quantity,
                'supplier_id': best_supplier.supplier_id,
                'shipment_id': shipment.id,
                'shipment_number': shipment.shipment_number,
                'total_cost': procurement.total_cost,
                'expected_delivery': shipment.expected_delivery_date.isoformat(),
                'order_type': 'emergency'
            }
            
            await self.log_action(
                action="place_emergency_order",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _optimize_order_quantities(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize order quantities using EOQ and demand forecasts."""
        start_time = datetime.utcnow()
        
        db = SessionLocal()
        try:
            # Get all products that need reordering
            products_with_inventory = db.query(Product, Inventory).join(
                Inventory, Product.id == Inventory.product_id
            ).filter(Product.is_active == True).all()
            
            optimization_results = []
            
            for product, inventory in products_with_inventory:
                # Get demand forecast for this product
                forecast_request = {
                    'product_ids': [product.id],
                    'forecast_period_days': 90
                }
                
                forecast_result = await self.demand_forecast_agent.execute(forecast_request)
                
                if forecast_result.get('success'):
                    forecast_data = forecast_result['data']['forecasts'].get(str(product.id))
                    
                    if forecast_data:
                        # Calculate EOQ
                        annual_demand = sum(forecast_data['combined_forecast'][:30]) * 12  # Annual from 30-day forecast
                        ordering_cost = 50  # Fixed ordering cost
                        holding_cost_rate = 0.2  # 20% of product cost
                        holding_cost_per_unit = product.cost_price * holding_cost_rate
                        
                        if annual_demand > 0 and holding_cost_per_unit > 0:
                            eoq = (2 * annual_demand * ordering_cost / holding_cost_per_unit) ** 0.5
                            
                            # Adjust for supplier minimum order quantities
                            suppliers = db.query(SupplierProduct).filter(
                                SupplierProduct.product_id == product.id
                            ).all()
                            
                            if suppliers:
                                min_order_qty = min(s.minimum_order_quantity for s in suppliers)
                                max_order_qty = max(s.quantity for s in suppliers if hasattr(s, 'quantity'))
                                
                                optimized_qty = max(min_order_qty, min(eoq, max_order_qty))
                                
                                optimization_results.append({
                                    'product_id': product.id,
                                    'product_name': product.name,
                                    'current_reorder_quantity': inventory.reorder_quantity,
                                    'optimized_reorder_quantity': int(optimized_qty),
                                    'annual_demand_forecast': annual_demand,
                                    'eoq': eoq,
                                    'cost_savings_potential': self._calculate_cost_savings(
                                        inventory.reorder_quantity, 
                                        optimized_qty, 
                                        annual_demand, 
                                        ordering_cost, 
                                        holding_cost_per_unit
                                    )
                                })
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'optimization_results': optimization_results,
                'total_products_analyzed': len(products_with_inventory),
                'optimized_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="optimize_order_quantities",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _enhance_reorder_decisions(
        self, 
        reorder_candidates: List[Dict[str, Any]], 
        forecast_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Enhance reorder decisions with demand forecast data."""
        if not forecast_result.get('success'):
            return reorder_candidates
        
        enhanced_candidates = []
        forecasts = forecast_result['data']['forecasts']
        
        for candidate in reorder_candidates:
            product_id = candidate['product_id']
            forecast_data = forecasts.get(str(product_id))
            
            if forecast_data:
                # Calculate expected demand during lead time
                lead_time_days = 7  # Default lead time
                expected_demand = sum(forecast_data['combined_forecast'][:lead_time_days])
                
                # Adjust reorder quantity based on forecast
                base_quantity = candidate.get('reorder_quantity', 50)
                forecast_adjusted_quantity = max(base_quantity, int(expected_demand * 1.2))
                
                candidate.update({
                    'expected_demand_lead_time': expected_demand,
                    'forecast_adjusted_quantity': forecast_adjusted_quantity,
                    'forecast_confidence': forecast_data.get('data_quality', 'unknown')
                })
            
            enhanced_candidates.append(candidate)
        
        return enhanced_candidates
    
    def _calculate_cost_savings(
        self, 
        current_qty: int, 
        optimized_qty: int, 
        annual_demand: float, 
        ordering_cost: float, 
        holding_cost_per_unit: float
    ) -> Dict[str, float]:
        """Calculate potential cost savings from optimization."""
        if annual_demand <= 0:
            return {'total_savings': 0, 'ordering_savings': 0, 'holding_savings': 0}
        
        # Current costs
        current_orders_per_year = annual_demand / current_qty if current_qty > 0 else 0
        current_ordering_cost = current_orders_per_year * ordering_cost
        current_holding_cost = (current_qty / 2) * holding_cost_per_unit
        current_total_cost = current_ordering_cost + current_holding_cost
        
        # Optimized costs
        optimized_orders_per_year = annual_demand / optimized_qty if optimized_qty > 0 else 0
        optimized_ordering_cost = optimized_orders_per_year * ordering_cost
        optimized_holding_cost = (optimized_qty / 2) * holding_cost_per_unit
        optimized_total_cost = optimized_ordering_cost + optimized_holding_cost
        
        return {
            'total_savings': current_total_cost - optimized_total_cost,
            'ordering_savings': current_ordering_cost - optimized_ordering_cost,
            'holding_savings': current_holding_cost - optimized_holding_cost,
            'current_total_cost': current_total_cost,
            'optimized_total_cost': optimized_total_cost
        }
