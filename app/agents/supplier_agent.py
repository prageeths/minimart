"""Supplier Agent for managing supplier communications and negotiations."""

import asyncio
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import random
from app.agents.base_agent import BaseAgent
from app.models.models import (
    AgentType, Product, Supplier, SupplierProduct, 
    Shipment, ProcurementTransaction
)
from app.database.database import SessionLocal
from app.core.config import settings


class SupplierAgent(BaseAgent):
    """Agent responsible for supplier communications, RFQ management, and price negotiations."""
    
    def __init__(self):
        super().__init__(AgentType.SUPPLIER)
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.supplier_emails = settings.supplier_emails
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute supplier agent operations."""
        start_time = datetime.utcnow()
        
        try:
            action = input_data.get('action', 'send_rfq')
            
            if action == 'send_rfq':
                return await self._send_rfq(input_data)
            elif action == 'send_emergency_rfq':
                return await self._send_emergency_rfq(input_data)
            elif action == 'negotiate_pricing':
                return await self._negotiate_pricing(input_data)
            elif action == 'evaluate_supplier_proposals':
                return await self._evaluate_supplier_proposals(input_data)
            elif action == 'send_order_confirmation':
                return await self._send_order_confirmation(input_data)
            else:
                return self.create_error_response(f"Unknown action: {action}")
                
        except Exception as e:
            self.logger.error(f"Error in supplier agent: {e}")
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            await self.log_action(
                action=input_data.get('action', 'unknown'),
                input_data=input_data,
                output_data={},
                status="error",
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
            return self.create_error_response(f"Supplier agent failed: {str(e)}")
    
    async def _send_rfq(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send Request for Quotation (RFQ) to suppliers."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['product_id', 'quantity']):
            return self.create_error_response("Missing required fields: product_id, quantity")
        
        product_id = input_data['product_id']
        quantity = input_data['quantity']
        urgency = input_data.get('urgency', 'normal')
        
        db = SessionLocal()
        try:
            # Get product information
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return self.create_error_response("Product not found")
            
            # Get suppliers for this product
            suppliers = db.query(SupplierProduct).filter(
                SupplierProduct.product_id == product_id
            ).all()
            
            if not suppliers:
                return self.create_error_response("No suppliers found for this product")
            
            # Send RFQ to all suppliers
            rfq_results = []
            for supplier_product in suppliers:
                supplier = db.query(Supplier).filter(
                    Supplier.id == supplier_product.supplier_id
                ).first()
                
                if supplier and supplier.is_active:
                    rfq_result = await self._send_rfq_email(
                        supplier, product, quantity, urgency, supplier_product
                    )
                    rfq_results.append(rfq_result)
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'rfq_sent': True,
                'product_id': product_id,
                'product_name': product.name,
                'quantity': quantity,
                'urgency': urgency,
                'suppliers_contacted': len(rfq_results),
                'rfq_results': rfq_results,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="send_rfq",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _send_emergency_rfq(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send emergency RFQ for urgent reorders."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['product_id', 'quantity', 'supplier_id']):
            return self.create_error_response("Missing required fields for emergency RFQ")
        
        product_id = input_data['product_id']
        quantity = input_data['quantity']
        supplier_id = input_data['supplier_id']
        shipment_id = input_data.get('shipment_id')
        
        db = SessionLocal()
        try:
            # Get product and supplier information
            product = db.query(Product).filter(Product.id == product_id).first()
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            supplier_product = db.query(SupplierProduct).filter(
                SupplierProduct.product_id == product_id,
                SupplierProduct.supplier_id == supplier_id
            ).first()
            
            if not all([product, supplier, supplier_product]):
                return self.create_error_response("Product, supplier, or supplier-product relationship not found")
            
            # Send emergency RFQ
            rfq_result = await self._send_emergency_rfq_email(
                supplier, product, quantity, supplier_product, shipment_id
            )
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'emergency_rfq_sent': True,
                'product_id': product_id,
                'product_name': product.name,
                'quantity': quantity,
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'shipment_id': shipment_id,
                'rfq_result': rfq_result,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="send_emergency_rfq",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _negotiate_pricing(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate price negotiations with suppliers."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['product_id', 'supplier_id', 'current_price']):
            return self.create_error_response("Missing required fields for negotiation")
        
        product_id = input_data['product_id']
        supplier_id = input_data['supplier_id']
        current_price = input_data['current_price']
        target_price = input_data.get('target_price', current_price * 0.9)  # 10% discount target
        
        db = SessionLocal()
        try:
            # Get supplier and product information
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            product = db.query(Product).filter(Product.id == product_id).first()
            
            if not supplier or not product:
                return self.create_error_response("Supplier or product not found")
            
            # Simulate negotiation process
            negotiation_result = await self._simulate_negotiation(
                supplier, product, current_price, target_price
            )
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'negotiation_completed': True,
                'product_id': product_id,
                'supplier_id': supplier_id,
                'original_price': current_price,
                'negotiated_price': negotiation_result['final_price'],
                'discount_achieved': negotiation_result['discount_percentage'],
                'negotiation_rounds': negotiation_result['rounds'],
                'supplier_response': negotiation_result['supplier_response'],
                'completed_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="negotiate_pricing",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _evaluate_supplier_proposals(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate and rank supplier proposals."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['product_id', 'proposals']):
            return self.create_error_response("Missing required fields: product_id, proposals")
        
        product_id = input_data['product_id']
        proposals = input_data['proposals']
        
        db = SessionLocal()
        try:
            # Get product information
            product = db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return self.create_error_response("Product not found")
            
            # Evaluate each proposal
            evaluated_proposals = []
            for proposal in proposals:
                evaluation = await self._evaluate_single_proposal(proposal, product)
                evaluated_proposals.append(evaluation)
            
            # Rank proposals by overall score
            ranked_proposals = sorted(
                evaluated_proposals, 
                key=lambda x: x['overall_score'], 
                reverse=True
            )
            
            # Select best proposal
            best_proposal = ranked_proposals[0] if ranked_proposals else None
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'evaluation_completed': True,
                'product_id': product_id,
                'total_proposals': len(proposals),
                'ranked_proposals': ranked_proposals,
                'best_proposal': best_proposal,
                'evaluated_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="evaluate_supplier_proposals",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _send_order_confirmation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send order confirmation to selected supplier."""
        start_time = datetime.utcnow()
        
        if not self.validate_input(input_data, ['supplier_id', 'order_details']):
            return self.create_error_response("Missing required fields for order confirmation")
        
        supplier_id = input_data['supplier_id']
        order_details = input_data['order_details']
        
        db = SessionLocal()
        try:
            # Get supplier information
            supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
            if not supplier:
                return self.create_error_response("Supplier not found")
            
            # Send order confirmation email
            confirmation_result = await self._send_order_confirmation_email(
                supplier, order_details
            )
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = {
                'confirmation_sent': True,
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'order_details': order_details,
                'confirmation_result': confirmation_result,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            await self.log_action(
                action="send_order_confirmation",
                input_data=input_data,
                output_data=result,
                execution_time_ms=execution_time
            )
            
            return self.create_success_response(result)
            
        finally:
            db.close()
    
    async def _send_rfq_email(
        self, 
        supplier: Supplier, 
        product: Product, 
        quantity: int, 
        urgency: str,
        supplier_product: SupplierProduct
    ) -> Dict[str, Any]:
        """Send RFQ email to supplier."""
        try:
            # Create email content
            subject = f"RFQ - {product.name} (Qty: {quantity})"
            
            body = f"""
Dear {supplier.contact_person or supplier.name},

We are requesting a quotation for the following product:

Product: {product.name}
SKU: {product.sku}
Description: {product.description or 'N/A'}
Quantity: {quantity}
Unit of Measure: {product.unit_of_measure}
Urgency: {urgency.upper()}

Please provide:
1. Unit price
2. Total cost
3. Delivery lead time
4. Payment terms
5. Any applicable discounts

Please respond within 24 hours for urgent requests or 48 hours for normal requests.

Best regards,
MiniMart AI Inventory Management System
            """
            
            # Send email (simulated for MVP)
            email_sent = await self._simulate_email_send(supplier.email, subject, body)
            
            return {
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'supplier_email': supplier.email,
                'email_sent': email_sent,
                'rfq_id': f"RFQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{supplier.id}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send RFQ email to {supplier.email}: {e}")
            return {
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'supplier_email': supplier.email,
                'email_sent': False,
                'error': str(e)
            }
    
    async def _send_emergency_rfq_email(
        self, 
        supplier: Supplier, 
        product: Product, 
        quantity: int,
        supplier_product: SupplierProduct,
        shipment_id: Optional[int]
    ) -> Dict[str, Any]:
        """Send emergency RFQ email to supplier."""
        try:
            subject = f"URGENT RFQ - {product.name} (Emergency Reorder)"
            
            body = f"""
URGENT REQUEST - IMMEDIATE ATTENTION REQUIRED

Dear {supplier.contact_person or supplier.name},

This is an EMERGENCY reorder request for the following product:

Product: {product.name}
SKU: {product.sku}
Quantity: {quantity}
Current Stock Level: CRITICAL
Shipment ID: {shipment_id or 'TBD'}

We need immediate confirmation of:
1. Availability
2. Fastest possible delivery time
3. Confirmed pricing
4. Tracking information once shipped

Please respond within 2 hours to confirm availability and delivery timeline.

This is a critical situation requiring immediate attention.

Best regards,
MiniMart AI Inventory Management System
Emergency Response Team
            """
            
            email_sent = await self._simulate_email_send(supplier.email, subject, body)
            
            return {
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'supplier_email': supplier.email,
                'email_sent': email_sent,
                'emergency_rfq_id': f"EMERGENCY-RFQ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{supplier.id}",
                'shipment_id': shipment_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send emergency RFQ email to {supplier.email}: {e}")
            return {
                'supplier_id': supplier.id,
                'supplier_name': supplier.name,
                'supplier_email': supplier.email,
                'email_sent': False,
                'error': str(e)
            }
    
    async def _simulate_negotiation(
        self, 
        supplier: Supplier, 
        product: Product, 
        current_price: float, 
        target_price: float
    ) -> Dict[str, Any]:
        """Simulate price negotiation with supplier."""
        
        # Simulate negotiation rounds
        rounds = 0
        current_negotiation_price = current_price
        discount_achieved = 0
        
        # Simulate supplier's willingness to negotiate based on various factors
        supplier_flexibility = random.uniform(0.3, 0.8)  # 30-80% flexibility
        market_conditions = random.uniform(0.5, 1.0)  # Market conditions factor
        
        while rounds < 3 and current_negotiation_price > target_price:
            rounds += 1
            
            # Calculate potential discount for this round
            max_discount = (current_negotiation_price - target_price) * supplier_flexibility * market_conditions
            round_discount = random.uniform(0.1, max_discount)
            
            current_negotiation_price -= round_discount
            
            # Simulate supplier response
            if current_negotiation_price <= target_price:
                break
        
        final_price = max(current_negotiation_price, target_price)
        discount_percentage = ((current_price - final_price) / current_price) * 100
        
        # Generate supplier response
        if discount_percentage > 10:
            supplier_response = f"After careful consideration, we can offer a {discount_percentage:.1f}% discount. This is our best price given current market conditions."
        elif discount_percentage > 5:
            supplier_response = f"We can provide a {discount_percentage:.1f}% discount. This reflects our commitment to our partnership."
        else:
            supplier_response = f"Our best offer is a {discount_percentage:.1f}% discount. Our prices are already competitive in the market."
        
        return {
            'final_price': final_price,
            'discount_percentage': discount_percentage,
            'rounds': rounds,
            'supplier_response': supplier_response,
            'negotiation_successful': discount_percentage > 0
        }
    
    async def _evaluate_single_proposal(self, proposal: Dict[str, Any], product: Product) -> Dict[str, Any]:
        """Evaluate a single supplier proposal."""
        
        # Scoring criteria (0-100 scale)
        price_score = 0
        delivery_score = 0
        quality_score = 0
        reliability_score = 0
        
        # Price scoring (lower price = higher score)
        proposed_price = proposal.get('unit_price', 0)
        if proposed_price > 0:
            # Compare with product cost price
            price_ratio = proposed_price / product.cost_price
            if price_ratio <= 1.0:
                price_score = 100
            elif price_ratio <= 1.1:
                price_score = 80
            elif price_ratio <= 1.2:
                price_score = 60
            else:
                price_score = max(0, 100 - (price_ratio - 1.2) * 100)
        
        # Delivery scoring
        lead_time = proposal.get('lead_time_days', 7)
        if lead_time <= 3:
            delivery_score = 100
        elif lead_time <= 7:
            delivery_score = 80
        elif lead_time <= 14:
            delivery_score = 60
        else:
            delivery_score = max(0, 100 - (lead_time - 14) * 5)
        
        # Quality scoring (simulated based on supplier reputation)
        quality_score = random.uniform(70, 95)
        
        # Reliability scoring (simulated based on historical performance)
        reliability_score = random.uniform(75, 90)
        
        # Calculate overall score (weighted average)
        weights = {'price': 0.4, 'delivery': 0.3, 'quality': 0.2, 'reliability': 0.1}
        overall_score = (
            price_score * weights['price'] +
            delivery_score * weights['delivery'] +
            quality_score * weights['quality'] +
            reliability_score * weights['reliability']
        )
        
        return {
            'supplier_id': proposal.get('supplier_id'),
            'supplier_name': proposal.get('supplier_name'),
            'unit_price': proposed_price,
            'lead_time_days': lead_time,
            'scores': {
                'price': price_score,
                'delivery': delivery_score,
                'quality': quality_score,
                'reliability': reliability_score
            },
            'overall_score': overall_score,
            'recommendation': 'accept' if overall_score >= 80 else 'consider' if overall_score >= 60 else 'reject'
        }
    
    async def _send_order_confirmation_email(
        self, 
        supplier: Supplier, 
        order_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send order confirmation email to supplier."""
        try:
            subject = f"Order Confirmation - {order_details.get('product_name', 'Product')}"
            
            body = f"""
Dear {supplier.contact_person or supplier.name},

We are pleased to confirm the following order:

Order Details:
- Product: {order_details.get('product_name', 'N/A')}
- Quantity: {order_details.get('quantity', 'N/A')}
- Unit Price: ${order_details.get('unit_price', 'N/A')}
- Total Amount: ${order_details.get('total_amount', 'N/A')}
- Expected Delivery: {order_details.get('expected_delivery', 'N/A')}
- Shipment ID: {order_details.get('shipment_id', 'N/A')}

Please confirm receipt of this order and provide tracking information once shipped.

Thank you for your prompt service.

Best regards,
MiniMart AI Inventory Management System
            """
            
            email_sent = await self._simulate_email_send(supplier.email, subject, body)
            
            return {
                'email_sent': email_sent,
                'confirmation_id': f"CONF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{supplier.id}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to send order confirmation email to {supplier.email}: {e}")
            return {
                'email_sent': False,
                'error': str(e)
            }
    
    async def _simulate_email_send(self, to_email: str, subject: str, body: str) -> bool:
        """Simulate email sending (for MVP purposes)."""
        try:
            # In a real implementation, this would use SMTP
            # For MVP, we'll simulate the email sending
            
            self.logger.info(f"Simulated email sent to {to_email}")
            self.logger.info(f"Subject: {subject}")
            self.logger.info(f"Body: {body[:200]}...")
            
            # Simulate 95% success rate
            return random.random() < 0.95
            
        except Exception as e:
            self.logger.error(f"Email simulation failed: {e}")
            return False
