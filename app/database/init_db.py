"""Database initialization with sample data."""

import asyncio
from datetime import datetime, timedelta
import random
from sqlalchemy.orm import Session
from app.database.database import SessionLocal, engine
from app.models.models import *
from app.core.config import settings


def init_database():
    """Initialize database with sample data."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if data already exists
        if db.query(Product).count() > 0:
            print("Database already initialized with data")
            return
        
        print("Initializing database with sample data...")
        
        # Create sample products
        products = create_sample_products(db)
        
        # Create sample suppliers
        suppliers = create_sample_suppliers(db)
        
        # Create supplier-product relationships
        create_supplier_products(db, products, suppliers)
        
        # Create sample inventory
        create_sample_inventory(db, products)
        
        # Create sample customers
        customers = create_sample_customers(db)
        
        # Create sample sales transactions (10 years of data)
        create_sample_sales_transactions(db, products, customers)
        
        # Create sample procurement transactions
        create_sample_procurement_transactions(db, products, suppliers)
        
        # Create sample shipments
        create_sample_shipments(db, suppliers)
        
        # Create sample agent logs
        create_sample_agent_logs(db)
        
        db.commit()
        print("Database initialized successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
        raise
    finally:
        db.close()


def create_sample_products(db: Session) -> list:
    """Create sample products."""
    products_data = [
        # Beverages
        {"name": "Coca Cola 330ml", "category": ProductCategory.BEVERAGES, "sku": "BEV001", "unit_price": 2.50, "cost_price": 1.80, "unit_of_measure": "can", "brand": "Coca Cola"},
        {"name": "Pepsi 330ml", "category": ProductCategory.BEVERAGES, "sku": "BEV002", "unit_price": 2.50, "cost_price": 1.80, "unit_of_measure": "can", "brand": "Pepsi"},
        {"name": "Orange Juice 1L", "category": ProductCategory.BEVERAGES, "sku": "BEV003", "unit_price": 4.50, "cost_price": 3.20, "unit_of_measure": "bottle", "brand": "Tropicana"},
        {"name": "Water Bottle 500ml", "category": ProductCategory.BEVERAGES, "sku": "BEV004", "unit_price": 1.50, "cost_price": 0.80, "unit_of_measure": "bottle", "brand": "Aquafina"},
        
        # Snacks
        {"name": "Potato Chips", "category": ProductCategory.SNACKS, "sku": "SNK001", "unit_price": 3.00, "cost_price": 2.00, "unit_of_measure": "bag", "brand": "Lays"},
        {"name": "Chocolate Bar", "category": ProductCategory.SNACKS, "sku": "SNK002", "unit_price": 2.50, "cost_price": 1.50, "unit_of_measure": "bar", "brand": "KitKat"},
        {"name": "Cookies Pack", "category": ProductCategory.SNACKS, "sku": "SNK003", "unit_price": 4.00, "cost_price": 2.50, "unit_of_measure": "pack", "brand": "Oreo"},
        {"name": "Nuts Mix", "category": ProductCategory.SNACKS, "sku": "SNK004", "unit_price": 5.50, "cost_price": 3.50, "unit_of_measure": "bag", "brand": "Planters"},
        
        # Household
        {"name": "Toilet Paper 4-pack", "category": ProductCategory.HOUSEHOLD, "sku": "HOU001", "unit_price": 8.00, "cost_price": 5.00, "unit_of_measure": "pack", "brand": "Charmin"},
        {"name": "Dish Soap", "category": ProductCategory.HOUSEHOLD, "sku": "HOU002", "unit_price": 3.50, "cost_price": 2.00, "unit_of_measure": "bottle", "brand": "Dawn"},
        {"name": "Laundry Detergent", "category": ProductCategory.HOUSEHOLD, "sku": "HOU003", "unit_price": 12.00, "cost_price": 8.00, "unit_of_measure": "bottle", "brand": "Tide"},
        {"name": "Trash Bags", "category": ProductCategory.HOUSEHOLD, "sku": "HOU004", "unit_price": 6.00, "cost_price": 3.50, "unit_of_measure": "roll", "brand": "Glad"},
        
        # Personal Care
        {"name": "Shampoo", "category": ProductCategory.PERSONAL_CARE, "sku": "PER001", "unit_price": 7.50, "cost_price": 4.50, "unit_of_measure": "bottle", "brand": "Head & Shoulders"},
        {"name": "Toothpaste", "category": ProductCategory.PERSONAL_CARE, "sku": "PER002", "unit_price": 4.00, "cost_price": 2.50, "unit_of_measure": "tube", "brand": "Colgate"},
        {"name": "Soap Bar", "category": ProductCategory.PERSONAL_CARE, "sku": "PER003", "unit_price": 2.00, "cost_price": 1.00, "unit_of_measure": "bar", "brand": "Dove"},
        {"name": "Deodorant", "category": ProductCategory.PERSONAL_CARE, "sku": "PER004", "unit_price": 5.50, "cost_price": 3.00, "unit_of_measure": "stick", "brand": "Old Spice"},
        
        # Food Items
        {"name": "Bread Loaf", "category": ProductCategory.FOOD_ITEMS, "sku": "FOO001", "unit_price": 3.50, "cost_price": 2.00, "unit_of_measure": "loaf", "brand": "Wonder"},
        {"name": "Milk 1L", "category": ProductCategory.FOOD_ITEMS, "sku": "FOO002", "unit_price": 4.00, "cost_price": 2.50, "unit_of_measure": "carton", "brand": "Dairy Fresh"},
        {"name": "Eggs 12-pack", "category": ProductCategory.FOOD_ITEMS, "sku": "FOO003", "unit_price": 5.00, "cost_price": 3.00, "unit_of_measure": "dozen", "brand": "Farm Fresh"},
        {"name": "Cereal Box", "category": ProductCategory.FOOD_ITEMS, "sku": "FOO004", "unit_price": 6.50, "cost_price": 4.00, "unit_of_measure": "box", "brand": "Kellogg's"},
    ]
    
    products = []
    for product_data in products_data:
        product = Product(**product_data)
        db.add(product)
        products.append(product)
    
    db.flush()  # Get the IDs
    return products


def create_sample_suppliers(db: Session) -> list:
    """Create sample suppliers."""
    suppliers_data = [
        {"name": "Beverage Distributors Inc", "email": "prageethsandakalum@gmail.com", "contact_person": "John Smith", "payment_terms": "Net 30", "delivery_lead_time_days": 3, "minimum_order_value": 100.0},
        {"name": "Snack Supply Co", "email": "prageeths@outlook.com", "contact_person": "Sarah Johnson", "payment_terms": "Net 15", "delivery_lead_time_days": 5, "minimum_order_value": 150.0},
        {"name": "Household Goods Ltd", "email": "malshasf@outlook.com", "contact_person": "Mike Wilson", "payment_terms": "Net 30", "delivery_lead_time_days": 7, "minimum_order_value": 200.0},
        {"name": "Personal Care Solutions", "email": "malshasf603@gmail.com", "contact_person": "Lisa Brown", "payment_terms": "Net 20", "delivery_lead_time_days": 4, "minimum_order_value": 120.0},
    ]
    
    suppliers = []
    for supplier_data in suppliers_data:
        supplier = Supplier(**supplier_data)
        db.add(supplier)
        suppliers.append(supplier)
    
    db.flush()
    return suppliers


def create_supplier_products(db: Session, products: list, suppliers: list):
    """Create supplier-product relationships."""
    for product in products:
        # Each product has 4 suppliers with different pricing
        for i, supplier in enumerate(suppliers):
            # Vary pricing slightly between suppliers
            base_cost = product.cost_price
            variation = random.uniform(0.9, 1.1)  # ±10% variation
            unit_cost = base_cost * variation
            
            supplier_product = SupplierProduct(
                supplier_id=supplier.id,
                product_id=product.id,
                unit_cost=round(unit_cost, 2),
                minimum_order_quantity=random.randint(10, 50),
                lead_time_days=random.randint(3, 10),
                is_preferred=(i == 0)  # First supplier is preferred
            )
            db.add(supplier_product)


def create_sample_inventory(db: Session, products: list):
    """Create sample inventory."""
    for product in products:
        # Random inventory levels
        current_stock = random.randint(20, 100)
        reorder_point = random.randint(10, 30)
        safety_stock = random.randint(5, 15)
        reorder_quantity = random.randint(50, 100)
        maximum_stock = random.randint(150, 300)
        
        inventory = Inventory(
            product_id=product.id,
            current_stock=current_stock,
            reserved_stock=0,
            available_stock=current_stock,
            reorder_point=reorder_point,
            reorder_quantity=reorder_quantity,
            safety_stock=safety_stock,
            maximum_stock=maximum_stock
        )
        db.add(inventory)


def create_sample_customers(db: Session) -> list:
    """Create sample customers."""
    customers_data = [
        {"name": "Alice Johnson", "email": "alice.johnson@email.com", "phone": "+1-555-0101"},
        {"name": "Bob Smith", "email": "bob.smith@email.com", "phone": "+1-555-0102"},
        {"name": "Carol Davis", "email": "carol.davis@email.com", "phone": "+1-555-0103"},
        {"name": "David Wilson", "email": "david.wilson@email.com", "phone": "+1-555-0104"},
        {"name": "Eva Brown", "email": "eva.brown@email.com", "phone": "+1-555-0105"},
    ]
    
    customers = []
    for customer_data in customers_data:
        customer = Customer(**customer_data)
        db.add(customer)
        customers.append(customer)
    
    db.flush()
    return customers


def create_sample_sales_transactions(db: Session, products: list, customers: list):
    """Create 10 years of sample sales transactions."""
    start_date = datetime.utcnow() - timedelta(days=10*365)
    end_date = datetime.utcnow()
    
    # Generate transactions for each day
    current_date = start_date
    while current_date <= end_date:
        # Random number of transactions per day (0-20)
        daily_transactions = random.randint(0, 20)
        
        for _ in range(daily_transactions):
            product = random.choice(products)
            customer = random.choice(customers)
            
            # Random quantity (1-5)
            quantity = random.randint(1, 5)
            
            # Add some seasonal variation
            seasonal_multiplier = 1.0
            if current_date.month in [11, 12]:  # Holiday season
                seasonal_multiplier = 1.5
            elif current_date.month in [6, 7, 8]:  # Summer
                if product.category == ProductCategory.BEVERAGES:
                    seasonal_multiplier = 1.3
            
            # Random time during the day
            transaction_time = current_date.replace(
                hour=random.randint(8, 20),
                minute=random.randint(0, 59),
                second=random.randint(0, 59)
            )
            
            transaction = SalesTransaction(
                product_id=product.id,
                customer_id=customer.id,
                quantity=int(quantity * seasonal_multiplier),
                unit_price=product.unit_price,
                total_amount=product.unit_price * int(quantity * seasonal_multiplier),
                transaction_date=transaction_time
            )
            db.add(transaction)
        
        current_date += timedelta(days=1)
    
    print(f"Created sales transactions from {start_date.date()} to {end_date.date()}")


def create_sample_procurement_transactions(db: Session, products: list, suppliers: list):
    """Create sample procurement transactions."""
    # Create procurement transactions for the last 2 years
    start_date = datetime.utcnow() - timedelta(days=2*365)
    end_date = datetime.utcnow()
    
    current_date = start_date
    while current_date <= end_date:
        # Random procurement events (0-5 per day)
        daily_procurements = random.randint(0, 5)
        
        for _ in range(daily_procurements):
            product = random.choice(products)
            supplier = random.choice(suppliers)
            
            # Get supplier product relationship
            supplier_product = db.query(SupplierProduct).filter(
                SupplierProduct.product_id == product.id,
                SupplierProduct.supplier_id == supplier.id
            ).first()
            
            if supplier_product:
                quantity = random.randint(50, 200)
                
                transaction = ProcurementTransaction(
                    product_id=product.id,
                    supplier_id=supplier.id,
                    quantity=quantity,
                    unit_cost=supplier_product.unit_cost,
                    total_cost=quantity * supplier_product.unit_cost,
                    transaction_date=current_date
                )
                db.add(transaction)
        
        current_date += timedelta(days=1)


def create_sample_shipments(db: Session, suppliers: list):
    """Create sample shipments."""
    # Create shipments for the last year
    start_date = datetime.utcnow() - timedelta(days=365)
    end_date = datetime.utcnow()
    
    current_date = start_date
    while current_date <= end_date:
        # Random shipments (0-3 per day)
        daily_shipments = random.randint(0, 3)
        
        for _ in range(daily_shipments):
            supplier = random.choice(suppliers)
            
            shipment_number = f"SHIP-{current_date.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
            expected_delivery = current_date + timedelta(days=random.randint(1, 10))
            
            # 80% chance of actual delivery
            actual_delivery = None
            status = ShipmentStatus.PENDING
            if random.random() < 0.8:
                actual_delivery = expected_delivery + timedelta(days=random.randint(-2, 3))
                status = ShipmentStatus.DELIVERED
            
            shipment = Shipment(
                supplier_id=supplier.id,
                shipment_number=shipment_number,
                status=status,
                expected_delivery_date=expected_delivery,
                actual_delivery_date=actual_delivery,
                total_value=random.uniform(100, 1000),
                tracking_number=f"TRK{random.randint(100000, 999999)}"
            )
            db.add(shipment)
        
        current_date += timedelta(days=1)


def create_sample_agent_logs(db: Session):
    """Create sample agent logs."""
    agent_types = [AgentType.ORDER_PLACEMENT, AgentType.DEMAND_FORECAST, AgentType.SUPPLIER, AgentType.LOGISTICS]
    actions = ["check_reorder_points", "demand_forecast", "send_rfq", "track_shipments", "negotiate_pricing"]
    
    # Create logs for the last 30 days
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()
    
    current_date = start_date
    while current_date <= end_date:
        # Random agent activities (5-20 per day)
        daily_activities = random.randint(5, 20)
        
        for _ in range(daily_activities):
            agent_type = random.choice(agent_types)
            action = random.choice(actions)
            status = random.choice(["success", "success", "success", "error"])  # 75% success rate
            
            log = AgentLog(
                agent_type=agent_type,
                action=action,
                input_data='{"test": "data"}',
                output_data='{"result": "success"}' if status == "success" else '{"error": "test error"}',
                status=status,
                error_message="Test error message" if status == "error" else None,
                execution_time_ms=random.randint(100, 2000)
            )
            db.add(log)
        
        current_date += timedelta(days=1)


if __name__ == "__main__":
    init_database()
