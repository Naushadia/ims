from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


# ── Input schemas ─────────────────────────────────────────────────────────────

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)


class OrderCreate(BaseModel):
    customer_id: int = Field(..., gt=0)
    items: list[OrderItemCreate] = Field(..., min_length=1)
    email_note: str | None = Field(default=None, max_length=1000)


# ── Response schemas ──────────────────────────────────────────────────────────

class OrderItemProductSnap(BaseModel):
    """Minimal product snapshot embedded in order item response."""
    id: int
    name: str
    sku: str

    model_config = {"from_attributes": True}


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product: OrderItemProductSnap
    quantity: int
    unit_price: Decimal
    subtotal: Decimal

    model_config = {"from_attributes": True}


class OrderCustomerSnap(BaseModel):
    """Minimal customer snapshot embedded in order response."""
    id: int
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    customer: OrderCustomerSnap
    status: str
    total_amount: Decimal
    items: list[OrderItemResponse]
    cancellation_reason: str | None
    email_note: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    data: list[OrderResponse]
    count: int


class OrderStatusUpdate(BaseModel):
    status: str
    cancellation_reason: str | None = None



# ── Dashboard schema ──────────────────────────────────────────────────────────

class LowStockProduct(BaseModel):
    id: int
    name: str
    sku: str
    quantity: int

    model_config = {"from_attributes": True}


class DashboardSummary(BaseModel):
    total_products: int
    total_customers: int
    total_orders: int
    low_stock_count: int
    low_stock_products: list[LowStockProduct]
