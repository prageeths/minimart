"""Test configuration and fixtures."""

import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import get_db, Base
from app.models.models import *
from app.core.config import settings

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# Create test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)

# Create test session
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_products(db_session):
    """Create sample products for testing."""
    products = [
        Product(
            name="Test Product 1",
            description="Test description 1",
            category=ProductCategory.BEVERAGES,
            sku="TEST001",
            unit_price=10.0,
            cost_price=7.0,
            unit_of_measure="piece",
            brand="Test Brand"
        ),
        Product(
            name="Test Product 2",
            description="Test description 2",
            category=ProductCategory.SNACKS,
            sku="TEST002",
            unit_price=15.0,
            cost_price=10.0,
            unit_of_measure="pack",
            brand="Test Brand"
        )
    ]
    
    for product in products:
        db_session.add(product)
    
    db_session.commit()
    
    for product in products:
        db_session.refresh(product)
    
    return products


@pytest.fixture
def sample_inventory(db_session, sample_products):
    """Create sample inventory for testing."""
    inventory_items = []
    
    for product in sample_products:
        inventory = Inventory(
            product_id=product.id,
            current_stock=100,
            reserved_stock=0,
            available_stock=100,
            reorder_point=20,
            reorder_quantity=50,
            safety_stock=10,
            maximum_stock=200
        )
        db_session.add(inventory)
        inventory_items.append(inventory)
    
    db_session.commit()
    
    for inventory in inventory_items:
        db_session.refresh(inventory)
    
    return inventory_items


@pytest.fixture
def sample_suppliers(db_session):
    """Create sample suppliers for testing."""
    suppliers = [
        Supplier(
            name="Test Supplier 1",
            email="supplier1@test.com",
            contact_person="John Doe",
            payment_terms="Net 30",
            delivery_lead_time_days=5,
            minimum_order_value=100.0
        ),
        Supplier(
            name="Test Supplier 2",
            email="supplier2@test.com",
            contact_person="Jane Smith",
            payment_terms="Net 15",
            delivery_lead_time_days=3,
            minimum_order_value=150.0
        )
    ]
    
    for supplier in suppliers:
        db_session.add(supplier)
    
    db_session.commit()
    
    for supplier in suppliers:
        db_session.refresh(supplier)
    
    return suppliers


@pytest.fixture
def sample_customers(db_session):
    """Create sample customers for testing."""
    customers = [
        Customer(
            name="Test Customer 1",
            email="customer1@test.com",
            phone="+1-555-0101"
        ),
        Customer(
            name="Test Customer 2",
            email="customer2@test.com",
            phone="+1-555-0102"
        )
    ]
    
    for customer in customers:
        db_session.add(customer)
    
    db_session.commit()
    
    for customer in customers:
        db_session.refresh(customer)
    
    return customers


@pytest.fixture
def sample_orders(db_session, sample_customers, sample_products):
    """Create sample orders for testing."""
    orders = []
    
    for i, customer in enumerate(sample_customers):
        order = Order(
            customer_id=customer.id,
            order_number=f"TEST-ORD-{i+1:03d}",
            total_amount=25.0,
            status=OrderStatus.PENDING
        )
        db_session.add(order)
        orders.append(order)
    
    db_session.commit()
    
    for order in orders:
        db_session.refresh(order)
    
    return orders


@pytest.fixture
def sample_sales_transactions(db_session, sample_products, sample_customers):
    """Create sample sales transactions for testing."""
    transactions = []
    
    for i in range(10):
        transaction = SalesTransaction(
            product_id=sample_products[0].id,
            customer_id=sample_customers[0].id,
            quantity=2,
            unit_price=10.0,
            total_amount=20.0
        )
        db_session.add(transaction)
        transactions.append(transaction)
    
    db_session.commit()
    
    for transaction in transactions:
        db_session.refresh(transaction)
    
    return transactions
