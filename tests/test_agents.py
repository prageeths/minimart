"""Tests for AI agents."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.agents.demand_forecast_agent import DemandForecastAgent
from app.agents.order_placement_agent import OrderPlacementAgent
from app.agents.supplier_agent import SupplierAgent
from app.agents.logistics_agent import LogisticsAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.models.models import AgentType


class TestDemandForecastAgent:
    """Test cases for Demand Forecast Agent."""
    
    @pytest.fixture
    def agent(self):
        return DemandForecastAgent()
    
    @pytest.mark.asyncio
    async def test_execute_success(self, agent):
        """Test successful demand forecasting execution."""
        input_data = {
            'product_ids': [1, 2],
            'forecast_period_days': 30
        }
        
        with patch.object(agent, '_get_historical_sales_data') as mock_get_data, \
             patch.object(agent, '_forecast_product_demand') as mock_forecast, \
             patch.object(agent, '_get_market_insights') as mock_insights, \
             patch.object(agent, 'log_action') as mock_log:
            
            # Mock return values
            mock_get_data.return_value = {1: Mock(), 2: Mock()}
            mock_forecast.return_value = {'forecast': 'test'}
            mock_insights.return_value = {'analysis': 'test'}
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert 'forecasts' in result['data']
            assert 'market_insights' in result['data']
    
    @pytest.mark.asyncio
    async def test_execute_invalid_input(self, agent):
        """Test demand forecasting with invalid input."""
        input_data = {
            'invalid_field': 'test'
        }
        
        result = await agent.execute(input_data)
        
        assert result['success'] is False
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_forecast_product_demand_limited_data(self, agent):
        """Test forecasting with limited historical data."""
        import pandas as pd
        
        # Create empty DataFrame to simulate limited data
        empty_df = pd.DataFrame(columns=['quantity', 'revenue'])
        
        result = await agent._forecast_product_demand(1, empty_df, 30)
        
        assert result['product_id'] == 1
        assert 'simple_average' in result['forecast_methods']
        assert result['data_quality'] == 'limited'


class TestOrderPlacementAgent:
    """Test cases for Order Placement Agent."""
    
    @pytest.fixture
    def agent(self):
        return OrderPlacementAgent()
    
    @pytest.mark.asyncio
    async def test_check_reorder_points(self, agent, db_session, sample_products, sample_inventory):
        """Test reorder point checking."""
        input_data = {
            'action': 'check_reorder_points'
        }
        
        with patch.object(agent, 'send_request') as mock_send_request, \
             patch.object(agent, 'log_action') as mock_log:
            
            mock_send_request.return_value = 1
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert 'reorder_candidates' in result['data']
            assert 'emergency_reorders' in result['data']
    
    @pytest.mark.asyncio
    async def test_place_emergency_order(self, agent, db_session, sample_products, sample_suppliers):
        """Test emergency order placement."""
        # Create supplier-product relationship
        from app.models.models import SupplierProduct
        supplier_product = SupplierProduct(
            supplier_id=sample_suppliers[0].id,
            product_id=sample_products[0].id,
            unit_cost=7.0,
            minimum_order_quantity=10,
            lead_time_days=5
        )
        db_session.add(supplier_product)
        db_session.commit()
        
        input_data = {
            'action': 'place_emergency_order',
            'product_id': sample_products[0].id,
            'quantity': 50
        }
        
        with patch.object(agent, 'send_request') as mock_send_request, \
             patch.object(agent, 'log_action') as mock_log:
            
            mock_send_request.return_value = 1
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert result['data']['order_placed'] is True
            assert result['data']['product_id'] == sample_products[0].id


class TestSupplierAgent:
    """Test cases for Supplier Agent."""
    
    @pytest.fixture
    def agent(self):
        return SupplierAgent()
    
    @pytest.mark.asyncio
    async def test_send_rfq(self, agent, db_session, sample_products, sample_suppliers):
        """Test RFQ sending."""
        # Create supplier-product relationship
        from app.models.models import SupplierProduct
        supplier_product = SupplierProduct(
            supplier_id=sample_suppliers[0].id,
            product_id=sample_products[0].id,
            unit_cost=7.0,
            minimum_order_quantity=10,
            lead_time_days=5
        )
        db_session.add(supplier_product)
        db_session.commit()
        
        input_data = {
            'action': 'send_rfq',
            'product_id': sample_products[0].id,
            'quantity': 50
        }
        
        with patch.object(agent, '_simulate_email_send') as mock_email, \
             patch.object(agent, 'log_action') as mock_log:
            
            mock_email.return_value = True
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert result['data']['rfq_sent'] is True
            assert result['data']['suppliers_contacted'] > 0
    
    @pytest.mark.asyncio
    async def test_negotiate_pricing(self, agent):
        """Test price negotiation."""
        input_data = {
            'action': 'negotiate_pricing',
            'product_id': 1,
            'supplier_id': 1,
            'current_price': 10.0,
            'target_price': 9.0
        }
        
        with patch.object(agent, 'log_action') as mock_log:
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert 'negotiated_price' in result['data']
            assert 'discount_achieved' in result['data']


class TestLogisticsAgent:
    """Test cases for Logistics Agent."""
    
    @pytest.fixture
    def agent(self):
        return LogisticsAgent()
    
    @pytest.mark.asyncio
    async def test_track_shipments(self, agent, db_session, sample_suppliers):
        """Test shipment tracking."""
        # Create sample shipments
        from app.models.models import Shipment, ShipmentStatus
        shipment = Shipment(
            supplier_id=sample_suppliers[0].id,
            shipment_number="TEST-SHIP-001",
            status=ShipmentStatus.IN_TRANSIT,
            expected_delivery_date=None,
            total_value=500.0
        )
        db_session.add(shipment)
        db_session.commit()
        
        input_data = {
            'action': 'track_shipments'
        }
        
        with patch.object(agent, 'log_action') as mock_log:
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert 'total_active_shipments' in result['data']
            assert 'shipment_status' in result['data']
    
    @pytest.mark.asyncio
    async def test_evaluate_supplier_performance(self, agent, db_session, sample_suppliers):
        """Test supplier performance evaluation."""
        input_data = {
            'action': 'evaluate_supplier_performance'
        }
        
        with patch.object(agent, 'log_action') as mock_log:
            mock_log.return_value = 1
            
            result = await agent.execute(input_data)
            
            assert result['success'] is True
            assert 'performance_results' in result['data']
            assert 'total_suppliers_evaluated' in result['data']


class TestSupervisorAgent:
    """Test cases for Supervisor Agent."""
    
    @pytest.fixture
    def agent(self):
        return SupervisorAgent()
    
    @pytest.mark.asyncio
    async def test_execute_inventory_management_workflow(self, agent):
        """Test inventory management workflow execution."""
        product_ids = [1, 2, 3]
        
        with patch.object(agent, 'execute') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'data': {'workflow_completed': True}
            }
            
            result = await agent.execute_inventory_management_workflow(product_ids)
            
            assert result['success'] is True
            assert 'workflow_completed' in result['data']
    
    @pytest.mark.asyncio
    async def test_execute_emergency_reorder_workflow(self, agent):
        """Test emergency reorder workflow execution."""
        product_id = 1
        quantity = 50
        
        with patch.object(agent, 'execute') as mock_execute:
            mock_execute.return_value = {
                'success': True,
                'data': {'emergency_reorder_completed': True}
            }
            
            result = await agent.execute_emergency_reorder_workflow(product_id, quantity)
            
            assert result['success'] is True
            assert 'emergency_reorder_completed' in result['data']


class TestAgentIntegration:
    """Integration tests for agent interactions."""
    
    @pytest.mark.asyncio
    async def test_agent_communication(self, db_session):
        """Test agent-to-agent communication."""
        from app.models.models import AgentInteraction, AgentType
        
        # Create test agent interaction
        interaction = AgentInteraction(
            from_agent=AgentType.ORDER_PLACEMENT,
            to_agent=AgentType.DEMAND_FORECAST,
            interaction_type="request",
            message="Request demand forecast for products [1, 2, 3]",
            data='{"product_ids": [1, 2, 3]}'
        )
        
        db_session.add(interaction)
        db_session.commit()
        db_session.refresh(interaction)
        
        assert interaction.id is not None
        assert interaction.from_agent == AgentType.ORDER_PLACEMENT
        assert interaction.to_agent == AgentType.DEMAND_FORECAST
    
    @pytest.mark.asyncio
    async def test_agent_logging(self, db_session):
        """Test agent action logging."""
        from app.models.models import AgentLog, AgentType
        
        # Create test agent log
        log = AgentLog(
            agent_type=AgentType.DEMAND_FORECAST,
            action="demand_forecast",
            input_data='{"product_ids": [1, 2, 3]}',
            output_data='{"forecasts": {}}',
            status="success",
            execution_time_ms=1500
        )
        
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)
        
        assert log.id is not None
        assert log.agent_type == AgentType.DEMAND_FORECAST
        assert log.status == "success"
        assert log.execution_time_ms == 1500
