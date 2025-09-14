"""Tests for API endpoints."""

import pytest
import json
from fastapi.testclient import TestClient
from app.main import app


class TestOrderAPI:
    """Test cases for Order API endpoints."""
    
    def test_create_order_success(self, client, sample_customers, sample_products):
        """Test successful order creation."""
        order_data = {
            "customer_id": sample_customers[0].id,
            "items": [
                {
                    "product_id": sample_products[0].id,
                    "quantity": 2,
                    "unit_price": 10.0
                }
            ],
            "notes": "Test order"
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["customer_id"] == sample_customers[0].id
        assert data["total_amount"] == 20.0
        assert data["status"] == "pending"
    
    def test_create_order_insufficient_stock(self, client, sample_customers, sample_products):
        """Test order creation with insufficient stock."""
        # Update inventory to have low stock
        inventory_response = client.put(
            f"/api/v1/inventory/{sample_products[0].id}",
            json={"current_stock": 1}
        )
        assert inventory_response.status_code == 200
        
        order_data = {
            "customer_id": sample_customers[0].id,
            "items": [
                {
                    "product_id": sample_products[0].id,
                    "quantity": 5,  # More than available stock
                    "unit_price": 10.0
                }
            ]
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 400
        assert "Insufficient stock" in response.json()["detail"]
    
    def test_get_orders(self, client, sample_orders):
        """Test getting all orders."""
        response = client.get("/api/v1/orders/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= len(sample_orders)
    
    def test_get_order_by_id(self, client, sample_orders):
        """Test getting order by ID."""
        order_id = sample_orders[0].id
        
        response = client.get(f"/api/v1/orders/{order_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert "customer" in data
        assert "order_items" in data
    
    def test_get_order_not_found(self, client):
        """Test getting non-existent order."""
        response = client.get("/api/v1/orders/99999")
        
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]
    
    def test_process_payment(self, client, sample_orders):
        """Test payment processing."""
        order_id = sample_orders[0].id
        payment_data = {
            "payment_method": "credit_card",
            "card_number": "4111111111111111",
            "expiry_date": "12/25",
            "cvv": "123"
        }
        
        response = client.post(
            f"/api/v1/orders/{order_id}/process-payment",
            json=payment_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "payment_reference" in data
        assert data["order_status"] == "confirmed"


class TestInventoryAPI:
    """Test cases for Inventory API endpoints."""
    
    def test_get_inventory(self, client, sample_inventory):
        """Test getting all inventory items."""
        response = client.get("/api/v1/inventory/")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= len(sample_inventory)
        
        # Check that each item has product information
        for item in data:
            assert "product" in item
            assert "current_stock" in item
            assert "available_stock" in item
    
    def test_get_inventory_by_product(self, client, sample_products, sample_inventory):
        """Test getting inventory by product ID."""
        product_id = sample_products[0].id
        
        response = client.get(f"/api/v1/inventory/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == product_id
        assert "product" in data
    
    def test_update_inventory(self, client, sample_products):
        """Test updating inventory."""
        product_id = sample_products[0].id
        update_data = {
            "current_stock": 150,
            "reorder_point": 25
        }
        
        response = client.put(f"/api/v1/inventory/{product_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_stock"] == 150
        assert data["reorder_point"] == 25
    
    def test_get_low_stock_alerts(self, client, sample_products):
        """Test getting low stock alerts."""
        # Set one product to low stock
        client.put(
            f"/api/v1/inventory/{sample_products[0].id}",
            json={"current_stock": 5}  # Below reorder point
        )
        
        response = client.get("/api/v1/inventory/alerts/low-stock")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have at least one alert
        if len(data) > 0:
            alert = data[0]
            assert "product_id" in alert
            assert "product_name" in alert
            assert "current_stock" in alert
            assert "alert_type" in alert
    
    def test_check_reorder_points(self, client):
        """Test reorder point check."""
        response = client.post("/api/v1/inventory/reorder-check")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow_result" in data
    
    def test_emergency_reorder(self, client, sample_products):
        """Test emergency reorder."""
        product_id = sample_products[0].id
        quantity = 50
        
        response = client.post(
            f"/api/v1/inventory/emergency-reorder/{product_id}",
            params={"quantity": quantity}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "workflow_result" in data


class TestAgentsAPI:
    """Test cases for Agents API endpoints."""
    
    def test_execute_inventory_management_workflow(self, client, sample_products):
        """Test inventory management workflow execution."""
        product_ids = [sample_products[0].id, sample_products[1].id]
        
        response = client.post(
            "/api/v1/agents/workflow/inventory-management",
            json={"product_ids": product_ids}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_execute_emergency_reorder_workflow(self, client, sample_products):
        """Test emergency reorder workflow execution."""
        product_id = sample_products[0].id
        quantity = 50
        
        response = client.post(
            "/api/v1/agents/workflow/emergency-reorder",
            json={"product_id": product_id, "quantity": quantity}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_execute_demand_forecast(self, client, sample_products):
        """Test demand forecasting."""
        request_data = {
            "product_ids": [sample_products[0].id],
            "forecast_period_days": 30
        }
        
        response = client.post(
            "/api/v1/agents/demand-forecast",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_execute_order_placement(self, client):
        """Test order placement logic."""
        request_data = {
            "action": "check_reorder_points"
        }
        
        response = client.post(
            "/api/v1/agents/order-placement",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_execute_supplier_negotiation(self, client, sample_products, sample_suppliers):
        """Test supplier negotiation."""
        request_data = {
            "action": "send_rfq",
            "product_id": sample_products[0].id,
            "quantity": 50
        }
        
        response = client.post(
            "/api/v1/agents/supplier-negotiation",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_execute_logistics_tracking(self, client):
        """Test logistics tracking."""
        request_data = {
            "action": "track_shipments"
        }
        
        response = client.post(
            "/api/v1/agents/logistics-tracking",
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_query_knowledge_base(self, client):
        """Test RAG knowledge base query."""
        response = client.post(
            "/api/v1/agents/rag/query",
            params={
                "query": "products with low stock",
                "collection": "all",
                "limit": 5
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_build_knowledge_base(self, client):
        """Test knowledge base building."""
        response = client.post("/api/v1/agents/rag/build-knowledge-base")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_get_product_insights(self, client, sample_products):
        """Test product insights generation."""
        product_id = sample_products[0].id
        
        response = client.get(f"/api/v1/agents/rag/product-insights/{product_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_get_inventory_recommendations(self, client):
        """Test inventory recommendations."""
        response = client.get("/api/v1/agents/rag/inventory-recommendations")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data
    
    def test_search_agent_decisions(self, client):
        """Test agent decision search."""
        response = client.get(
            "/api/v1/agents/rag/agent-decisions",
            params={"search_term": "demand forecast"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "result" in data


class TestHealthEndpoints:
    """Test cases for health and status endpoints."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data


class TestErrorHandling:
    """Test cases for error handling."""
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint."""
        response = client.get("/api/v1/invalid-endpoint")
        
        assert response.status_code == 404
    
    def test_invalid_json(self, client):
        """Test invalid JSON in request body."""
        response = client.post(
            "/api/v1/orders/",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test missing required fields."""
        order_data = {
            "customer_id": 1
            # Missing items field
        }
        
        response = client.post("/api/v1/orders/", json=order_data)
        
        assert response.status_code == 422
