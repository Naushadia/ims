import asyncio
import os
import sys
from decimal import Decimal
from datetime import datetime, timedelta

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal, engine
from app.models.product import Product
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem

async def seed_data():
    print("Starting database seeding...")
    async with AsyncSessionLocal() as session:
        async with session.begin():
            # 1. Check if we already have data
            product_check = await session.execute(select(Product))
            if product_check.scalars().first():
                print("Database already has data. Skipping seeding.")
                return

            print("Creating sample products...")
            now = datetime.utcnow()
            products = [
                Product(name="Ergonomic Office Chair", sku="CHR-001", price=Decimal("12999.00"), quantity=45, created_at=now, updated_at=now),
                Product(name="Mechanical Keyboard", sku="KEY-002", price=Decimal("4599.00"), quantity=12, created_at=now, updated_at=now),
                Product(name="UltraWide Gaming Monitor", sku="MON-003", price=Decimal("28499.00"), quantity=4, created_at=now, updated_at=now), # Low stock!
                Product(name="USB-C Multiport Adapter", sku="ADP-004", price=Decimal("1899.00"), quantity=120, created_at=now, updated_at=now),
                Product(name="Wireless Noise-Cancelling Headphones", sku="HDP-005", price=Decimal("14999.00"), quantity=0, created_at=now, updated_at=now), # Out of stock!
                Product(name="Dual-Monitor Mounting Arm", sku="ARM-006", price=Decimal("5499.00"), quantity=18, created_at=now, updated_at=now),
            ]
            session.add_all(products)

            print("Creating sample customers...")
            customers = [
                Customer(full_name="Rajesh Kumar", email="rajesh.kumar@example.com", phone="+919876543210", created_at=now - timedelta(days=10)),
                Customer(full_name="Priya Sharma", email="priya.sharma@example.com", phone="+918765432109", created_at=now - timedelta(days=8)),
                Customer(full_name="Amit Patel", email="amit.patel@example.com", phone="+917654321098", created_at=now - timedelta(days=6)),
                Customer(full_name="Ananya Iyer", email="ananya.iyer@example.com", phone="+916543210987", created_at=now - timedelta(days=4)),
            ]
            session.add_all(customers)

            # Flush to get IDs
            await session.flush()

            print("Creating sample orders...")
            # Order 1: Confirmed order for Rajesh
            order1 = Order(
                customer_id=customers[0].id,
                status="confirmed",
                total_amount=Decimal("17598.00"),
                created_at=now - timedelta(days=5),
                updated_at=now - timedelta(days=5),
            )
            session.add(order1)
            await session.flush()
            
            item1_1 = OrderItem(order_id=order1.id, product_id=products[0].id, quantity=1, unit_price=products[0].price)
            item1_2 = OrderItem(order_id=order1.id, product_id=products[1].id, quantity=1, unit_price=products[1].price)
            session.add_all([item1_1, item1_2])

            # Order 2: Created order for Priya
            order2 = Order(
                customer_id=customers[1].id,
                status="created",
                total_amount=Decimal("30398.00"),
                created_at=now - timedelta(days=2),
                updated_at=now - timedelta(days=2),
            )
            session.add(order2)
            await session.flush()

            item2_1 = OrderItem(order_id=order2.id, product_id=products[2].id, quantity=1, unit_price=products[2].price)
            item2_2 = OrderItem(order_id=order2.id, product_id=products[3].id, quantity=1, unit_price=products[3].price)
            session.add_all([item2_1, item2_2])

            # Order 3: Cancelled order for Amit
            order3 = Order(
                customer_id=customers[2].id,
                status="cancelled",
                total_amount=Decimal("4599.00"),
                created_at=now - timedelta(days=1),
                updated_at=now - timedelta(days=1),
            )
            session.add(order3)
            await session.flush()

            item3_1 = OrderItem(order_id=order3.id, product_id=products[1].id, quantity=1, unit_price=products[1].price)
            session.add(item3_1)

        await session.commit()
    print("Database seeding completed successfully!")

if __name__ == "__main__":
    asyncio.run(seed_data())
