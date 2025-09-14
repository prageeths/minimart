"""Database models for the MiniMart inventory management system."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.database import Base
import enum


class ProductCategory(enum.Enum):
    """Product categories for mini mart items."""
    BEVERAGES = "beverages"
    SNACKS = "snacks"
    HOUSEHOLD = "household"
    PERSONAL_CARE = "personal_care"
    FOOD_ITEMS = "food_items"
    ELECTRONICS = "electronics"
    STATIONERY = "stationery"
    TOYS = "toys"


class OrderStatus(enum.Enum):
    """Order status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class ShipmentStatus(enum.Enum):
    """Shipment status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    DELAYED = "delayed"
    CANCELLED = "cancelled"


class AgentType(enum.Enum):
    """Agent types in the system."""
    ORDER_PLACEMENT = "order_placement"
    DEMAND_FORECAST = "demand_forecast"
    SUPPLIER = "supplier"
    LOGISTICS = "logistics"
    SUPERVISOR = "supervisor"


class Product(Base):
    """Product model for mini mart items."""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    category = Column(Enum(ProductCategory), nullable=False)
    sku = Column(String(100), unique=True, nullable=False, index=True)
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    unit_of_measure = Column(String(50), nullable=False)  # e.g., "piece", "kg", "liter"
    weight = Column(Float)  # in grams
    dimensions = Column(String(100))  # e.g., "10x5x3 cm"
    brand = Column(String(100))
    barcode = Column(String(50), unique=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    inventory = relationship("Inventory", back_populates="product", uselist=False)
    order_items = relationship("OrderItem", back_populates="product")
    supplier_products = relationship("SupplierProduct", back_populates="product")
    sales_transactions = relationship("SalesTransaction", back_populates="product")
    procurement_transactions = relationship("ProcurementTransaction", back_populates="product")


class Supplier(Base):
    """Supplier model."""
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(50))
    address = Column(Text)
    contact_person = Column(String(255))
    payment_terms = Column(String(100))  # e.g., "Net 30"
    delivery_lead_time_days = Column(Integer, default=7)
    minimum_order_value = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier_products = relationship("SupplierProduct", back_populates="supplier")
    shipments = relationship("Shipment", back_populates="supplier")
    supplier_performance = relationship("SupplierPerformance", back_populates="supplier")


class SupplierProduct(Base):
    """Many-to-many relationship between suppliers and products."""
    __tablename__ = "supplier_products"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_sku = Column(String(100))
    unit_cost = Column(Float, nullable=False)
    minimum_order_quantity = Column(Integer, default=1)
    lead_time_days = Column(Integer, default=7)
    is_preferred = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_products")
    product = relationship("Product", back_populates="supplier_products")


class Inventory(Base):
    """Inventory model for tracking stock levels."""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, unique=True)
    current_stock = Column(Integer, nullable=False, default=0)
    reserved_stock = Column(Integer, default=0)  # Stock reserved for pending orders
    available_stock = Column(Integer, nullable=False, default=0)  # current_stock - reserved_stock
    reorder_point = Column(Integer, nullable=False, default=10)
    reorder_quantity = Column(Integer, nullable=False, default=50)
    safety_stock = Column(Integer, default=5)
    maximum_stock = Column(Integer, default=200)
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="inventory")


class Customer(Base):
    """Customer model."""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True)
    phone = Column(String(50))
    address = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="customer")


class Order(Base):
    """Customer order model."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_number = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total_amount = Column(Float, nullable=False)
    payment_status = Column(String(50), default="pending")
    payment_method = Column(String(50))
    payment_reference = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Order items model."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class SalesTransaction(Base):
    """Historical sales transactions."""
    __tablename__ = "sales_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="sales_transactions")
    order = relationship("Order")


class ProcurementTransaction(Base):
    """Historical procurement transactions."""
    __tablename__ = "procurement_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    shipment_id = Column(Integer, ForeignKey("shipments.id"))
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    transaction_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="procurement_transactions")
    supplier = relationship("Supplier")
    shipment = relationship("Shipment")


class Shipment(Base):
    """Shipment model for tracking deliveries."""
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    shipment_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(Enum(ShipmentStatus), default=ShipmentStatus.PENDING)
    expected_delivery_date = Column(DateTime(timezone=True))
    actual_delivery_date = Column(DateTime(timezone=True))
    total_value = Column(Float, default=0.0)
    tracking_number = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="shipments")
    procurement_transactions = relationship("ProcurementTransaction", back_populates="shipment")


class SupplierPerformance(Base):
    """Supplier performance tracking."""
    __tablename__ = "supplier_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    total_orders = Column(Integer, default=0)
    on_time_deliveries = Column(Integer, default=0)
    delayed_deliveries = Column(Integer, default=0)
    quality_issues = Column(Integer, default=0)
    average_delivery_time_days = Column(Float, default=0.0)
    average_price = Column(Float, default=0.0)
    performance_score = Column(Float, default=0.0)  # 0-100 scale
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    supplier = relationship("Supplier", back_populates="supplier_performance")


class AgentLog(Base):
    """Agent communication and decision logs."""
    __tablename__ = "agent_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_type = Column(Enum(AgentType), nullable=False)
    action = Column(String(255), nullable=False)
    input_data = Column(Text)  # JSON string
    output_data = Column(Text)  # JSON string
    status = Column(String(50), default="success")  # success, error, warning
    error_message = Column(Text)
    execution_time_ms = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent_interactions = relationship("AgentInteraction", back_populates="log")


class AgentInteraction(Base):
    """Agent-to-agent communication logs."""
    __tablename__ = "agent_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    from_agent = Column(Enum(AgentType), nullable=False)
    to_agent = Column(Enum(AgentType), nullable=False)
    interaction_type = Column(String(100), nullable=False)  # request, response, notification
    message = Column(Text)
    data = Column(Text)  # JSON string
    log_id = Column(Integer, ForeignKey("agent_logs.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    log = relationship("AgentLog", back_populates="agent_interactions")
