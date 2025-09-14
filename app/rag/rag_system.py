"""RAG (Retrieval-Augmented Generation) system for internal data retrieval."""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import pandas as pd
from sqlalchemy import text
from app.database.database import SessionLocal
from app.models.models import (
    Product, Inventory, Supplier, SalesTransaction, 
    ProcurementTransaction, Shipment, AgentLog
)
from app.core.config import settings


class RAGSystem:
    """RAG system for retrieving and analyzing internal business data."""
    
    def __init__(self):
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db"
        ))
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = "minimart_knowledge"
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize ChromaDB collections."""
        try:
            # Create or get the main knowledge collection
            self.knowledge_collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "MiniMart internal knowledge base"}
            )
            
            # Create specialized collections
            self.product_collection = self.chroma_client.get_or_create_collection(
                name="products",
                metadata={"description": "Product information and specifications"}
            )
            
            self.sales_collection = self.chroma_client.get_or_create_collection(
                name="sales_data",
                metadata={"description": "Historical sales transactions and patterns"}
            )
            
            self.supplier_collection = self.chroma_client.get_or_create_collection(
                name="suppliers",
                metadata={"description": "Supplier information and performance data"}
            )
            
            self.agent_collection = self.chroma_client.get_or_create_collection(
                name="agent_logs",
                metadata={"description": "Agent decision logs and interactions"}
            )
            
        except Exception as e:
            print(f"Error initializing collections: {e}")
    
    async def build_knowledge_base(self) -> Dict[str, Any]:
        """Build the knowledge base from database data."""
        try:
            # Build different knowledge collections
            product_data = await self._build_product_knowledge()
            sales_data = await self._build_sales_knowledge()
            supplier_data = await self._build_supplier_knowledge()
            agent_data = await self._build_agent_knowledge()
            
            return {
                'success': True,
                'collections_built': {
                    'products': len(product_data),
                    'sales': len(sales_data),
                    'suppliers': len(supplier_data),
                    'agents': len(agent_data)
                },
                'built_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'built_at': datetime.utcnow().isoformat()
            }
    
    async def _build_product_knowledge(self) -> List[Dict[str, Any]]:
        """Build product knowledge base."""
        db = SessionLocal()
        try:
            # Get all products with inventory information
            products = db.query(Product, Inventory).join(
                Inventory, Product.id == Inventory.product_id
            ).all()
            
            product_docs = []
            for product, inventory in products:
                # Create comprehensive product document
                doc = {
                    'product_id': product.id,
                    'name': product.name,
                    'description': product.description or '',
                    'category': product.category.value,
                    'sku': product.sku,
                    'brand': product.brand or '',
                    'current_stock': inventory.current_stock,
                    'reorder_point': inventory.reorder_point,
                    'safety_stock': inventory.safety_stock,
                    'unit_price': product.unit_price,
                    'cost_price': product.cost_price,
                    'unit_of_measure': product.unit_of_measure
                }
                
                # Create searchable text
                searchable_text = f"""
                Product: {product.name}
                Category: {product.category.value}
                Description: {product.description or 'No description'}
                Brand: {product.brand or 'No brand'}
                SKU: {product.sku}
                Current Stock: {inventory.current_stock}
                Reorder Point: {inventory.reorder_point}
                Safety Stock: {inventory.safety_stock}
                Unit Price: ${product.unit_price}
                Cost Price: ${product.cost_price}
                Unit of Measure: {product.unit_of_measure}
                """
                
                # Add to collection
                self.product_collection.add(
                    documents=[searchable_text],
                    metadatas=[doc],
                    ids=[f"product_{product.id}"]
                )
                
                product_docs.append(doc)
            
            return product_docs
            
        finally:
            db.close()
    
    async def _build_sales_knowledge(self) -> List[Dict[str, Any]]:
        """Build sales knowledge base."""
        db = SessionLocal()
        try:
            # Get sales data for the last 2 years
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=2*365)
            
            sales_data = db.query(SalesTransaction, Product).join(
                Product, SalesTransaction.product_id == Product.id
            ).filter(
                SalesTransaction.transaction_date >= start_date
            ).all()
            
            # Group sales by product and time periods
            sales_summary = {}
            for transaction, product in sales_data:
                product_id = product.id
                if product_id not in sales_summary:
                    sales_summary[product_id] = {
                        'product_name': product.name,
                        'total_quantity': 0,
                        'total_revenue': 0,
                        'transaction_count': 0,
                        'avg_daily_sales': 0,
                        'recent_trend': 'stable'
                    }
                
                sales_summary[product_id]['total_quantity'] += transaction.quantity
                sales_summary[product_id]['total_revenue'] += transaction.total_amount
                sales_summary[product_id]['transaction_count'] += 1
            
            # Calculate trends and add to collection
            sales_docs = []
            for product_id, summary in sales_summary.items():
                # Calculate average daily sales
                days_in_period = (end_date - start_date).days
                summary['avg_daily_sales'] = summary['total_quantity'] / days_in_period
                
                # Create searchable text
                searchable_text = f"""
                Product: {summary['product_name']}
                Total Sales Quantity: {summary['total_quantity']}
                Total Revenue: ${summary['total_revenue']:.2f}
                Transaction Count: {summary['transaction_count']}
                Average Daily Sales: {summary['avg_daily_sales']:.2f}
                Sales Period: {start_date.date()} to {end_date.date()}
                """
                
                # Add to collection
                self.sales_collection.add(
                    documents=[searchable_text],
                    metadatas=[summary],
                    ids=[f"sales_{product_id}"]
                )
                
                sales_docs.append(summary)
            
            return sales_docs
            
        finally:
            db.close()
    
    async def _build_supplier_knowledge(self) -> List[Dict[str, Any]]:
        """Build supplier knowledge base."""
        db = SessionLocal()
        try:
            # Get suppliers with their products and performance data
            suppliers = db.query(Supplier).filter(Supplier.is_active == True).all()
            
            supplier_docs = []
            for supplier in suppliers:
                # Get supplier's products
                supplier_products = db.query(SupplierProduct, Product).join(
                    Product, SupplierProduct.product_id == Product.id
                ).filter(SupplierProduct.supplier_id == supplier.id).all()
                
                # Get recent shipments
                recent_shipments = db.query(Shipment).filter(
                    Shipment.supplier_id == supplier.id,
                    Shipment.created_at >= datetime.utcnow() - timedelta(days=90)
                ).all()
                
                # Calculate performance metrics
                total_shipments = len(recent_shipments)
                on_time_deliveries = sum(1 for s in recent_shipments 
                                       if s.actual_delivery_date and s.expected_delivery_date 
                                       and s.actual_delivery_date <= s.expected_delivery_date)
                
                on_time_rate = (on_time_deliveries / total_shipments * 100) if total_shipments > 0 else 0
                
                supplier_doc = {
                    'supplier_id': supplier.id,
                    'name': supplier.name,
                    'email': supplier.email,
                    'contact_person': supplier.contact_person or '',
                    'payment_terms': supplier.payment_terms or '',
                    'lead_time_days': supplier.delivery_lead_time_days,
                    'minimum_order_value': supplier.minimum_order_value,
                    'product_count': len(supplier_products),
                    'recent_shipments': total_shipments,
                    'on_time_delivery_rate': on_time_rate,
                    'products_supplied': [p.name for _, p in supplier_products]
                }
                
                # Create searchable text
                searchable_text = f"""
                Supplier: {supplier.name}
                Contact: {supplier.contact_person or 'N/A'}
                Email: {supplier.email}
                Payment Terms: {supplier.payment_terms or 'N/A'}
                Lead Time: {supplier.delivery_lead_time_days} days
                Minimum Order: ${supplier.minimum_order_value}
                Products Supplied: {', '.join(supplier_doc['products_supplied'])}
                Recent Shipments: {total_shipments}
                On-Time Delivery Rate: {on_time_rate:.1f}%
                """
                
                # Add to collection
                self.supplier_collection.add(
                    documents=[searchable_text],
                    metadatas=[supplier_doc],
                    ids=[f"supplier_{supplier.id}"]
                )
                
                supplier_docs.append(supplier_doc)
            
            return supplier_docs
            
        finally:
            db.close()
    
    async def _build_agent_knowledge(self) -> List[Dict[str, Any]]:
        """Build agent knowledge base from logs."""
        db = SessionLocal()
        try:
            # Get recent agent logs
            recent_logs = db.query(AgentLog).filter(
                AgentLog.created_at >= datetime.utcnow() - timedelta(days=30)
            ).order_by(AgentLog.created_at.desc()).limit(1000).all()
            
            agent_docs = []
            for log in recent_logs:
                agent_doc = {
                    'log_id': log.id,
                    'agent_type': log.agent_type.value,
                    'action': log.action,
                    'status': log.status,
                    'execution_time_ms': log.execution_time_ms,
                    'created_at': log.created_at.isoformat(),
                    'error_message': log.error_message or ''
                }
                
                # Create searchable text
                searchable_text = f"""
                Agent: {log.agent_type.value}
                Action: {log.action}
                Status: {log.status}
                Execution Time: {log.execution_time_ms}ms
                Date: {log.created_at}
                Error: {log.error_message or 'None'}
                """
                
                # Add to collection
                self.agent_collection.add(
                    documents=[searchable_text],
                    metadatas=[agent_doc],
                    ids=[f"agent_log_{log.id}"]
                )
                
                agent_docs.append(agent_doc)
            
            return agent_docs
            
        finally:
            db.close()
    
    async def query_knowledge_base(
        self, 
        query: str, 
        collection: str = "all",
        limit: int = 5
    ) -> Dict[str, Any]:
        """Query the knowledge base for relevant information."""
        try:
            results = {}
            
            if collection == "all" or collection == "products":
                product_results = self.product_collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                results['products'] = self._format_query_results(product_results)
            
            if collection == "all" or collection == "sales":
                sales_results = self.sales_collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                results['sales'] = self._format_query_results(sales_results)
            
            if collection == "all" or collection == "suppliers":
                supplier_results = self.supplier_collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                results['suppliers'] = self._format_query_results(supplier_results)
            
            if collection == "all" or collection == "agents":
                agent_results = self.agent_collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                results['agents'] = self._format_query_results(agent_results)
            
            return {
                'success': True,
                'query': query,
                'results': results,
                'queried_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'queried_at': datetime.utcnow().isoformat()
            }
    
    def _format_query_results(self, query_results) -> List[Dict[str, Any]]:
        """Format query results for better readability."""
        if not query_results or not query_results.get('documents'):
            return []
        
        formatted_results = []
        for i, doc in enumerate(query_results['documents'][0]):
            metadata = query_results['metadatas'][0][i] if query_results.get('metadatas') else {}
            distance = query_results['distances'][0][i] if query_results.get('distances') else 0
            
            formatted_results.append({
                'document': doc,
                'metadata': metadata,
                'relevance_score': 1 - distance,  # Convert distance to relevance score
                'id': query_results['ids'][0][i] if query_results.get('ids') else None
            })
        
        return formatted_results
    
    async def get_product_insights(self, product_id: int) -> Dict[str, Any]:
        """Get comprehensive insights for a specific product."""
        try:
            # Query product information
            product_query = f"product ID {product_id}"
            product_results = await self.query_knowledge_base(product_query, "products", 1)
            
            # Query sales data for this product
            sales_query = f"product sales performance trends"
            sales_results = await self.query_knowledge_base(sales_query, "sales", 5)
            
            # Query supplier information
            supplier_query = f"suppliers for product"
            supplier_results = await self.query_knowledge_base(supplier_query, "suppliers", 3)
            
            # Query agent decisions related to this product
            agent_query = f"agent decisions product inventory"
            agent_results = await self.query_knowledge_base(agent_query, "agents", 5)
            
            return {
                'success': True,
                'product_id': product_id,
                'insights': {
                    'product_info': product_results.get('results', {}).get('products', []),
                    'sales_performance': sales_results.get('results', {}).get('sales', []),
                    'supplier_info': supplier_results.get('results', {}).get('suppliers', []),
                    'agent_decisions': agent_results.get('results', {}).get('agents', [])
                },
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'product_id': product_id,
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def get_inventory_recommendations(self) -> Dict[str, Any]:
        """Get inventory management recommendations based on knowledge base."""
        try:
            # Query for low stock products
            low_stock_query = "products with low stock reorder point safety stock"
            low_stock_results = await self.query_knowledge_base(low_stock_query, "products", 10)
            
            # Query for high-performing products
            high_performance_query = "products with high sales performance revenue"
            high_performance_results = await self.query_knowledge_base(high_performance_query, "sales", 5)
            
            # Query for supplier performance
            supplier_performance_query = "suppliers with good performance on-time delivery"
            supplier_performance_results = await self.query_knowledge_base(supplier_performance_query, "suppliers", 5)
            
            # Generate recommendations
            recommendations = []
            
            # Low stock recommendations
            for product in low_stock_results.get('results', {}).get('products', []):
                if product['metadata'].get('current_stock', 0) <= product['metadata'].get('reorder_point', 0):
                    recommendations.append({
                        'type': 'reorder_urgent',
                        'product_id': product['metadata'].get('product_id'),
                        'product_name': product['metadata'].get('name'),
                        'current_stock': product['metadata'].get('current_stock'),
                        'reorder_point': product['metadata'].get('reorder_point'),
                        'recommendation': f"Urgent reorder needed for {product['metadata'].get('name')}"
                    })
            
            # High performance recommendations
            for sales in high_performance_results.get('results', {}).get('sales', []):
                if sales['metadata'].get('avg_daily_sales', 0) > 10:  # High daily sales
                    recommendations.append({
                        'type': 'increase_stock',
                        'product_name': sales['metadata'].get('product_name'),
                        'avg_daily_sales': sales['metadata'].get('avg_daily_sales'),
                        'recommendation': f"Consider increasing stock for high-performing product {sales['metadata'].get('product_name')}"
                    })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'total_recommendations': len(recommendations),
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'generated_at': datetime.utcnow().isoformat()
            }
    
    async def search_agent_decisions(self, search_term: str) -> Dict[str, Any]:
        """Search through agent decision logs."""
        try:
            results = await self.query_knowledge_base(search_term, "agents", 10)
            
            # Analyze patterns in agent decisions
            agent_decisions = results.get('results', {}).get('agents', [])
            
            decision_patterns = {
                'successful_actions': [],
                'failed_actions': [],
                'common_errors': [],
                'performance_metrics': {}
            }
            
            for decision in agent_decisions:
                metadata = decision.get('metadata', {})
                status = metadata.get('status', '')
                action = metadata.get('action', '')
                
                if status == 'success':
                    decision_patterns['successful_actions'].append(action)
                elif status == 'error':
                    decision_patterns['failed_actions'].append(action)
                    if metadata.get('error_message'):
                        decision_patterns['common_errors'].append(metadata['error_message'])
                
                # Track performance metrics
                agent_type = metadata.get('agent_type', '')
                if agent_type not in decision_patterns['performance_metrics']:
                    decision_patterns['performance_metrics'][agent_type] = {
                        'total_actions': 0,
                        'successful_actions': 0,
                        'avg_execution_time': 0
                    }
                
                metrics = decision_patterns['performance_metrics'][agent_type]
                metrics['total_actions'] += 1
                if status == 'success':
                    metrics['successful_actions'] += 1
                
                if metadata.get('execution_time_ms'):
                    metrics['avg_execution_time'] = (
                        (metrics['avg_execution_time'] * (metrics['total_actions'] - 1) + 
                         metadata['execution_time_ms']) / metrics['total_actions']
                    )
            
            return {
                'success': True,
                'search_term': search_term,
                'agent_decisions': agent_decisions,
                'decision_patterns': decision_patterns,
                'searched_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'search_term': search_term,
                'searched_at': datetime.utcnow().isoformat()
            }
