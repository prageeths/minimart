"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
from app.models.models import ProductCategory, OrderStatus, ShipmentStatus, AgentType


# Product Schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: ProductCategory
    sku: str
    unit_price: float
    cost_price: float
    unit_of_measure: str
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    brand: Optional[str] = None
    barcode: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    unit_price: Optional[float] = None
    cost_price: Optional[float] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    brand: Optional[str] = None
    is_active: Optional[bool] = None


class Product(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Inventory Schemas
class InventoryBase(BaseModel):
    current_stock: int
    reorder_point: int
    reorder_quantity: int
    safety_stock: int
    maximum_stock: int


class InventoryUpdate(BaseModel):
    current_stock: Optional[int] = None
    reorder_point: Optional[int] = None
    reorder_quantity: Optional[int] = None
    safety_stock: Optional[int] = None
    maximum_stock: Optional[int] = None


class Inventory(InventoryBase):
    id: int
    product_id: int
    reserved_stock: int
    available_stock: int
    last_updated: datetime

    class Config:
        from_attributes = True


class InventoryWithProduct(Inventory):
    product: Product


# Customer Schemas
class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class Customer(CustomerBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Order Schemas
class OrderItemBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: float


class OrderItemCreate(OrderItemBase):
    pass


class OrderItem(OrderItemBase):
    id: int
    order_id: int
    total_price: float
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemWithProduct(OrderItem):
    product: Product


class OrderBase(BaseModel):
    customer_id: int
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    payment_status: Optional[str] = None
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    notes: Optional[str] = None


class Order(OrderBase):
    id: int
    order_number: str
    status: OrderStatus
    total_amount: float
    payment_status: str
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderWithDetails(Order):
    customer: Customer
    order_items: List[OrderItemWithProduct]


# Supplier Schemas
class SupplierBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_lead_time_days: int = 7
    minimum_order_value: float = 0.0


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    contact_person: Optional[str] = None
    payment_terms: Optional[str] = None
    delivery_lead_time_days: Optional[int] = None
    minimum_order_value: Optional[float] = None
    is_active: Optional[bool] = None


class Supplier(SupplierBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Supplier Product Schemas
class SupplierProductBase(BaseModel):
    supplier_id: int
    product_id: int
    supplier_sku: Optional[str] = None
    unit_cost: float
    minimum_order_quantity: int = 1
    lead_time_days: int = 7
    is_preferred: bool = False


class SupplierProductCreate(SupplierProductBase):
    pass


class SupplierProductUpdate(BaseModel):
    supplier_sku: Optional[str] = None
    unit_cost: Optional[float] = None
    minimum_order_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None
    is_preferred: Optional[bool] = None


class SupplierProduct(SupplierProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SupplierProductWithDetails(SupplierProduct):
    supplier: Supplier
    product: Product


# Shipment Schemas
class ShipmentBase(BaseModel):
    supplier_id: int
    shipment_number: str
    expected_delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class ShipmentCreate(ShipmentBase):
    pass


class ShipmentUpdate(BaseModel):
    status: Optional[ShipmentStatus] = None
    expected_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None


class Shipment(ShipmentBase):
    id: int
    status: ShipmentStatus
    actual_delivery_date: Optional[datetime] = None
    total_value: float
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ShipmentWithSupplier(Shipment):
    supplier: Supplier


# Sales Transaction Schemas
class SalesTransactionBase(BaseModel):
    product_id: int
    order_id: Optional[int] = None
    quantity: int
    unit_price: float
    total_amount: float


class SalesTransactionCreate(SalesTransactionBase):
    pass


class SalesTransaction(SalesTransactionBase):
    id: int
    transaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Procurement Transaction Schemas
class ProcurementTransactionBase(BaseModel):
    product_id: int
    supplier_id: int
    shipment_id: Optional[int] = None
    quantity: int
    unit_cost: float
    total_cost: float


class ProcurementTransactionCreate(ProcurementTransactionBase):
    pass


class ProcurementTransaction(ProcurementTransactionBase):
    id: int
    transaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# Agent Log Schemas
class AgentLogBase(BaseModel):
    agent_type: AgentType
    action: str
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    status: str = "success"
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None


class AgentLogCreate(AgentLogBase):
    pass


class AgentLog(AgentLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Agent Interaction Schemas
class AgentInteractionBase(BaseModel):
    from_agent: AgentType
    to_agent: AgentType
    interaction_type: str
    message: Optional[str] = None
    data: Optional[str] = None


class AgentInteractionCreate(AgentInteractionBase):
    log_id: Optional[int] = None


class AgentInteraction(AgentInteractionBase):
    id: int
    log_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Dashboard and Analytics Schemas
class InventoryAlert(BaseModel):
    product_id: int
    product_name: str
    current_stock: int
    reorder_point: int
    alert_type: str  # "low_stock", "out_of_stock", "overstock"


class SalesAnalytics(BaseModel):
    product_id: int
    product_name: str
    total_sales: int
    total_revenue: float
    average_daily_sales: float
    trend: str  # "increasing", "decreasing", "stable"


class SupplierPerformanceMetrics(BaseModel):
    supplier_id: int
    supplier_name: str
    on_time_delivery_rate: float
    average_delivery_time: float
    quality_score: float
    price_competitiveness: float
    overall_score: float


# API Response Schemas
class MessageResponse(BaseModel):
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


# Pagination Schemas
class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int
