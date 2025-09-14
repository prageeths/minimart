"""Logistics Agent for managing supplier performance and logistics coordination."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
from app.agents.base_agent import BaseAgent
from app.models.models import (
    AgentType, Supplier, Shipment, SupplierPerformance, 
    ProcurementTransaction, ShipmentStatus
)
from app.database.database import SessionLocal


class LogisticsAgent(BaseAgent):
    """Agent responsible for logistics coordination, supplier performance tracking, and delivery management."""
    
    def __init__(self):
        super().__init__(AgentType.LOGISTICS)
        self.performance_tracking_period_days = 90  # Track performance over 90 days
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute logistics agent operations."""
        start_time = datetime.utcnow()
        
        try:
            action = input_data.get('action', 'track_shipments')
            
            if action == 'track_shipments':
                return await self._track_shipments(input_data)
            elif action == 'evaluate_supplier_performance':
                return await self._evaluate_supplier_performance(input_data)
            elif action == 'optimize_supplier_selection':
                return await self._optimize_supplier_selection(input_data)
            elif action == 'handle_delivery_issues':
                return await self._handle_delivery_issues(input_data)
            elif action == 'update_shipment_status':
                return await self._update_shipment_status(input_data)
            else:
                return self.create_error_response(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error in logistics agent: {e}")
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.log_action(
                action=input_data.get('action', 'unknown'),
                input_data=input_data,
                output_data={},
                status="error",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            return self.create_error_response(f"Logistics agent failed: {str(e)}")
    
    async def _track_shipments(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track active shipments and identify potential issues."""
        start_time = datetime.utcnow()
        
        db = SessionLocal()
        try:
            # Get all active shipments
            active_shipments = db.query(Shipment).filter(
                Shipment.status.in_([
                    ShipmentStatus.PENDING,
                    ShipmentStatus.CONFIRMED,
                    ShipmentStatus.IN_TRANSIT
                ])
            ).all()
            
            shipment_status = []
            delayed_shipments = []
            at_risk_shipments = []
            
            current_date = datetime.utcnow()
            
            for shipment in active_shipments:
                # Calculate days since shipment creation
                days_since_created = (current_date - shipment.created_at).days
                
                # Check if shipment is delayed
                if shipment.expected_delivery_date:
                    days_until_expected = (shipment.expected_delivery_date - current_date).days
                    
                    if days_until_expected < 0:
                        # Shipment is overdue
                        delayed_shipments.append({
                            'shipment_id': shipment.id,
                            'shipment_number': shipment.shipment_number,
                            'supplier_id': shipment.supplier_id,
                            'expected_delivery': shipment.expected_delivery_date.isoformat(),
                            'days_overdue': abs(days_until_expected),
                            'status': shipment.status.value
                        })
                    elif days_until_expected <= 2:
                        # Shipment is at risk of being delayed
                        at_risk_shipments.append({
                            'shipment_id': shipment.id,
                            'shipment_number': shipment.shipment_number,
                            'supplier_id': shipment.supplier_id,
                            'expected_delivery': shipment.expected_delivery_date.isoformat(),
                            'days_until_delivery': days_until_expected,
                            'status': shipment.status.value
                        })
                
                shipment_status.append({
                    'shipment_id': shipment.id,
                    'shipment_number': shipment.shipment_number,
                    'supplier_id': shipment.supplier_id,
                    'status': shipment.status.value,
                    'created_at': shipment.created_at.isoformat(),
                    'expected_delivery': shipment.expected_delivery_date.isoformat() if shipment.expected_delivery_date else None,
                    'days_since_created': days_since_created,
                    'tracking_number': shipment.tracking_number
                })
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'total_active_shipments': len(active_shipments),
                'delayed_shipments': delayed_shipments,
                'at_risk_shipments': at_risk_shipments,
                'shipment_status': shipment_status,
                'tracked_at': current_date.isoformat()
            }
            
            await self.log_action(
                action="track_shipments",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _evaluate_supplier_performance(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate supplier performance based on historical data."""
        start_time = datetime.utcnow()
        
        db = SessionLocal()
        try:
            # Get evaluation period
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.performance_tracking_period_days)
            
            # Get all suppliers
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
            
            performance_results = []
            
            for supplier in suppliers:
                # Get shipments for this supplier in the evaluation period
                shipments = db.query(Shipment).filter(
                    Shipment.supplier_id == supplier.id,
                    Shipment.created_at >= start_date,
                    Shipment.created_at <= end_date
                ).all()
                
                if not shipments:
                    continue
                
                # Calculate performance metrics
                total_shipments = len(shipments)
                on_time_deliveries = 0
                delayed_deliveries = 0
                total_delivery_time = 0
                quality_issues = 0
                
                for shipment in shipments:
                    if shipment.actual_delivery_date and shipment.expected_delivery_date:
                        if shipment.actual_delivery_date <= shipment.expected_delivery_date:
                            on_time_deliveries += 1
                        else:
                            delayed_deliveries += 1
                        
                        delivery_time = (shipment.actual_delivery_date - shipment.created_at).days
                        total_delivery_time += delivery_time
                    elif shipment.status == ShipmentStatus.DELAYED:
                        delayed_deliveries += 1
                
                # Calculate performance scores
                on_time_rate = (on_time_deliveries / total_shipments) * 100 if total_shipments > 0 else 0
                average_delivery_time = total_delivery_time / total_shipments if total_shipments > 0 else 0
                
                # Quality score (simulated - in real implementation, this would be based on return rates, etc.)
                quality_score = max(0, 100 - (quality_issues * 10))
                
                # Overall performance score
                overall_score = (on_time_rate * 0.4 + quality_score * 0.3 + 
                               max(0, 100 - average_delivery_time) * 0.3)
                
                performance_results.append({
                    'supplier_id': supplier.id,
                    'supplier_name': supplier.name,
                    'evaluation_period_days': self.performance_tracking_period_days,
                    'total_shipments': total_shipments,
                    'on_time_deliveries': on_time_deliveries,
                    'delayed_deliveries': delayed_deliveries,
                    'on_time_delivery_rate': on_time_rate,
                    'average_delivery_time_days': average_delivery_time,
                    'quality_score': quality_score,
                    'overall_performance_score': overall_score,
                    'performance_grade': self._get_performance_grade(overall_score)
                })
            
            # Sort by overall performance score
            performance_results.sort(key=lambda x: x['overall_performance_score'], reverse=True)
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'evaluation_period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': self.performance_tracking_period_days
                },
                'total_suppliers_evaluated': len(performance_results),
                'performance_results': performance_results,
                'top_performers': performance_results[:3] if len(performance_results) >= 3 else performance_results,
                'underperformers': [p for p in performance_results if p['overall_performance_score'] < 70],
                'evaluated_at': end_date.isoformat()
            }
            
            await self.log_action(
                action="evaluate_supplier_performance",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _optimize_supplier_selection(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize supplier selection based on performance and cost."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['product_id']):
            return self.create_error_response("Missing required field: product_id")
        
        product_id = input_data['product_id']
        
        db = SessionLocal()
        try:
            # Get suppliers for this product
            supplier_products = db.query(SupplierProduct).filter(
                SupplierProduct.product_id == product_id
            ).all()
            
            if not supplier_products:
                return self.create_error_response("No suppliers found for this product")
            
            # Get recent performance data
            performance_data = await self._get_supplier_performance_data(
                [sp.supplier_id for sp in supplier_products]
            )
            
            # Evaluate each supplier
            supplier_evaluations = []
            
            for supplier_product in supplier_products:
                supplier_id = supplier_product.supplier_id
                performance = performance_data.get(supplier_id, {})
                
                # Calculate composite score
                cost_score = self._calculate_cost_score(supplier_product.unit_cost)
                performance_score = performance.get('overall_performance_score', 50)
                reliability_score = performance.get('on_time_delivery_rate', 50)
                
                # Weighted composite score
                composite_score = (
                    cost_score * 0.4 +           # 40% cost
                    performance_score * 0.35 +   # 35% performance
                    reliability_score * 0.25     # 25% reliability
                )
                
                supplier_evaluations.append({
                    'supplier_id': supplier_id,
                    'supplier_name': db.query(Supplier).filter(Supplier.id == supplier_id).first().name,
                    'unit_cost': supplier_product.unit_cost,
                    'lead_time_days': supplier_product.lead_time_days,
                    'minimum_order_quantity': supplier_product.minimum_order_quantity,
                    'is_preferred': supplier_product.is_preferred,
                    'cost_score': cost_score,
                    'performance_score': performance_score,
                    'reliability_score': reliability_score,
                    'composite_score': composite_score,
                    'recommendation': self._get_supplier_recommendation(composite_score, supplier_product.is_preferred)
                })
            
            # Sort by composite score
            supplier_evaluations.sort(key=lambda x: x['composite_score'], reverse=True)
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'product_id': product_id,
                'total_suppliers': len(supplier_evaluations),
                'supplier_evaluations': supplier_evaluations,
                'recommended_supplier': supplier_evaluations[0] if supplier_evaluations else None,
                'optimization_criteria': {
                    'cost_weight': 0.4,
                    'performance_weight': 0.35,
                    'reliability_weight': 0.25
                },
                'optimized_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="optimize_supplier_selection",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _handle_delivery_issues(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle delivery issues and coordinate resolution."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['shipment_id', 'issue_type']):
            return self.create_error_response("Missing required fields: shipment_id, issue_type")
        
        shipment_id = input_data['shipment_id']
        issue_type = input_data['issue_type']
        issue_description = input_data.get('issue_description', '')
        
        db = SessionLocal()
        try:
            # Get shipment information
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                return self.create_error_response("Shipment not found")
            
            # Get supplier information
            supplier = db.query(Supplier).filter(Supplier.id == shipment.supplier_id).first()
            if not supplier:
                return self.create_error_response("Supplier not found")
            
            # Determine resolution strategy based on issue type
            resolution_strategy = self._determine_resolution_strategy(issue_type, shipment)
            
            # Update shipment status
            if issue_type in ['delayed', 'lost', 'damaged']:
                shipment.status = ShipmentStatus.DELAYED
                shipment.notes = f"Issue: {issue_type} - {issue_description}"
                db.commit()
            
            # Notify supplier about the issue
            notification_result = await self._notify_supplier_about_issue(
                supplier, shipment, issue_type, issue_description, resolution_strategy
            )
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'issue_handled': True,
                'shipment_id': shipment_id,
                'shipment_number': shipment.shipment_number,
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'issue_type': issue_type,
                'issue_description': issue_description,
                'resolution_strategy': resolution_strategy,
                'supplier_notified': notification_result['notified'],
                'updated_status': shipment.status.value,
                'handled_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="handle_delivery_issues",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _update_shipment_status(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update shipment status based on tracking information."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['shipment_id', 'new_status']):
            return self.create_error_response("Missing required fields: shipment_id, new_status")
        
        shipment_id = input_data['shipment_id']
        new_status = input_data['new_status']
        tracking_info = input_data.get('tracking_info', {})
        
        db = SessionLocal()
        try:
            # Get shipment information
            shipment = db.query(Shipment).filter(Shipment.id == shipment_id).first()
            if not shipment:
                return self.create_error_response("Shipment not found")
            
            # Update shipment status
            old_status = shipment.status
            shipment.status = ShipmentStatus(new_status)
            
            # Update tracking information
            if 'tracking_number' in tracking_info:
                shipment.tracking_number = tracking_info['tracking_number']
            
            if 'actual_delivery_date' in tracking_info:
                shipment.actual_delivery_date = datetime.fromisoformat(tracking_info['actual_delivery_date'])
            
            if 'notes' in tracking_info:
                shipment.notes = tracking_info['notes']
            
            db.commit()
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'status_updated': True,
                'shipment_id': shipment_id,
                'shipment_number': shipment.shipment_number,
                'old_status': old_status.value,
                'new_status': new_status,
                'tracking_info': tracking_info,
                'updated_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="update_shipment_status",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _get_supplier_performance_data(self, supplier_ids: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get performance data for suppliers."""
        db = SessionLocal()
        try:
            # Get recent performance records
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.performance_tracking_period_days)
            
            performance_records = db.query(SupplierPerformance).filter(
                SupplierPerformance.supplier_id.in_(supplier_ids),
                SupplierPerformance.period_start >= start_date
            ).all()
            
            performance_data = {}
            for record in performance_records:
                performance_data[record.supplier_id] = {
                    'overall_performance_score': record.performance_score,
                    'on_time_delivery_rate': (record.on_time_deliveries / record.total_orders * 100) if record.total_orders > 0 else 0,
                    'average_delivery_time': record.average_delivery_time_days,
                    'quality_issues': record.quality_issues
                }
            
            return performance_data
            
        finally:
            db.close()
    
    def _calculate_cost_score(self, unit_cost: float) -> float:
        """Calculate cost score (lower cost = higher score)."""
        # This is a simplified scoring - in reality, you'd compare against market rates
        if unit_cost <= 10:
            return 100
        elif unit_cost <= 20:
            return 90
        elif unit_cost <= 50:
            return 80
        elif unit_cost <= 100:
            return 70
        else:
            return max(0, 100 - (unit_cost - 100) * 0.5)
    
    def _get_supplier_recommendation(self, composite_score: float, is_preferred: bool) -> str:
        """Get supplier recommendation based on score."""
        if is_preferred and composite_score >= 70:
            return "preferred"
        elif composite_score >= 85:
            return "highly_recommended"
        elif composite_score >= 70:
            return "recommended"
        elif composite_score >= 50:
            return "acceptable"
        else:
            return "not_recommended"
    
    def _get_performance_grade(self, score: float) -> str:
        """Convert performance score to letter grade."""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def _determine_resolution_strategy(self, issue_type: str, shipment: Shipment) -> Dict[str, Any]:
        """Determine resolution strategy for delivery issues."""
        strategies = {
            'delayed': {
                'action': 'expedite_delivery',
                'priority': 'high',
                'timeline': '24-48 hours',
                'escalation': 'contact_supplier_manager'
            },
            'lost': {
                'action': 'investigate_and_replace',
                'priority': 'critical',
                'timeline': 'immediate',
                'escalation': 'contact_supplier_executive'
            },
            'damaged': {
                'action': 'quality_inspection_and_replacement',
                'priority': 'high',
                'timeline': '48-72 hours',
                'escalation': 'quality_team_review'
            },
            'wrong_item': {
                'action': 'return_and_replace',
                'priority': 'medium',
                'timeline': '3-5 days',
                'escalation': 'inventory_team_coordination'
            }
        }
        
        return strategies.get(issue_type, {
            'action': 'investigate',
            'priority': 'medium',
            'timeline': '48 hours',
            'escalation': 'standard_procedure'
        })
    
    async def _notify_supplier_about_issue(
        self, 
        supplier: Supplier, 
        shipment: Shipment, 
        issue_type: str, 
        issue_description: str,
        resolution_strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Notify supplier about delivery issue."""
        try:
            # Simulate notification to supplier
            self.logger.info(f"Notifying supplier {supplier.name} about {issue_type} issue for shipment {shipment.shipment_number}")
            
            # In a real implementation, this would send an email or make an API call
            return {
                'notified': True,
                'notification_method': 'email',
                'notification_sent_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Failed to notify supplier: {e}")
            return {
                'notified': False,
                'error': str(e)
            }
