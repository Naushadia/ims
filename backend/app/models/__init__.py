# backend/app/models/__init__.py
from app.models.product import Product
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem

__all__ = ["Product", "Customer", "Order", "OrderItem"]
