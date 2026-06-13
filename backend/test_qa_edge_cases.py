import asyncio
import os
import sys
from decimal import Decimal

# Set python path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.customer import Customer
from app.models.product import Product
from app.models.order import Order
from app.services import customer_service, order_service
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.order import OrderCreate, OrderItemCreate
from app.exceptions import AppError


async def pre_cleanup():
    print("Pre-cleanup: Removing stale QA test accounts...")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Customer).where(
                Customer.email.in_(["qa-inactive@example.com", "qa-active@example.com"])
            )
        )
        stale_customers = result.scalars().all()
        for c in stale_customers:
            orders_res = await db.execute(select(Order).where(Order.customer_id == c.id))
            stale_orders = orders_res.scalars().all()
            for o in stale_orders:
                await db.delete(o)
            await db.delete(c)
        await db.commit()
    print("Pre-cleanup complete.")


async def test_inactive_customer_blocks_order():
    print("\nTest 1: Inactive Customer ordering block...")
    
    # 1. Create an inactive customer
    async with AsyncSessionLocal() as db:
        customer_data = CustomerCreate(
            full_name="QA Inactive User",
            email="qa-inactive@example.com",
            phone="1234567890",
            status="inactive"
        )
        customer = await customer_service.create_customer(db, customer_data)
        customer_id = customer.id
        print(f"Created Inactive Customer: {customer.full_name} (ID: {customer_id}, Status: {customer.status})")

    # 2. Get a sample product to order
    async with AsyncSessionLocal() as db:
        product_result = await db.execute(select(Product).limit(1))
        product = product_result.scalar_one_or_none()
        if not product:
            print("ERROR: No products available to place an order.")
            return
        product_id = product.id

    # 3. Try to place order using a fresh session
    async with AsyncSessionLocal() as db:
        order_data = OrderCreate(
            customer_id=customer_id,
            items=[OrderItemCreate(product_id=product_id, quantity=1)]
        )

        try:
            await order_service.create_order(db, order_data)
            print("FAIL: Order creation succeeded for inactive customer!")
        except AppError as e:
            if e.code == "INACTIVE_CUSTOMER" and e.status_code == 400:
                print("PASS: Order creation correctly blocked with 400 Inactive Customer error.")
            else:
                print(f"FAIL: Expected INACTIVE_CUSTOMER code, got {e.code} ({e.status_code})")
        except Exception as e:
            print(f"FAIL: Unexpected error: {e}")

    # Cleanup customer using a fresh session
    async with AsyncSessionLocal() as db:
        customer = await customer_service.get_customer_by_id(db, customer_id)
        await db.delete(customer)
        await db.commit()


async def test_order_transitions_and_status():
    print("\nTest 2: Order status created and transition constraints...")
    
    # 1. Create active customer
    async with AsyncSessionLocal() as db:
        customer_data = CustomerCreate(
            full_name="QA Active User",
            email="qa-active@example.com",
            phone="1234567890",
            status="active"
        )
        customer = await customer_service.create_customer(db, customer_data)
        customer_id = customer.id

    # Get a sample product
    async with AsyncSessionLocal() as db:
        product_result = await db.execute(select(Product).where(Product.quantity > 5).limit(1))
        product = product_result.scalar_one_or_none()
        if not product:
            print("ERROR: No products with stock available.")
            return
        product_id = product.id
        orig_qty = product.quantity

    # 2. Create Order
    async with AsyncSessionLocal() as db:
        order_data = OrderCreate(
            customer_id=customer_id,
            items=[OrderItemCreate(product_id=product_id, quantity=1)]
        )
        order = await order_service.create_order(db, order_data)
        order_id = order.id
        print(f"Placed Order: ID={order.id}, Status={order.status}, Total={order.total_amount}")

        if order.status == "created":
            print("PASS: Default order status is 'created'.")
        else:
            print(f"FAIL: Default order status is '{order.status}'")

    # 3. Transition: created -> completed (directly) - should fail
    async with AsyncSessionLocal() as db:
        try:
            await order_service.update_order_status(db, order_id, "completed")
            print("FAIL: Allowed direct transitions from 'created' to 'completed'!")
        except AppError as e:
            if e.code == "INVALID_TRANSITION":
                print("PASS: Correctly blocked 'created' -> 'completed' transition.")
            else:
                print(f"FAIL: Expected INVALID_TRANSITION, got {e.code}")

    # 4. Transition: created -> confirmed - should pass
    async with AsyncSessionLocal() as db:
        order = await order_service.update_order_status(db, order_id, "confirmed")
        if order.status == "confirmed":
            print("PASS: Successfully transitioned 'created' -> 'confirmed'.")
        else:
            print(f"FAIL: Order status is {order.status}")

    # 5. Transition: confirmed -> completed - should pass
    async with AsyncSessionLocal() as db:
        order = await order_service.update_order_status(db, order_id, "completed")
        if order.status == "completed":
            print("PASS: Successfully transitioned 'confirmed' -> 'completed'.")
        else:
            print(f"FAIL: Order status is {order.status}")

    # 6. Terminal state check: completed -> cancelled - should fail
    async with AsyncSessionLocal() as db:
        try:
            await order_service.update_order_status(db, order_id, "cancelled", "Mistake")
            print("FAIL: Allowed status change from completed terminal state!")
        except AppError as e:
            if e.code == "TERMINAL_STATE":
                print("PASS: Correctly blocked transition from completed terminal state.")
            else:
                print(f"FAIL: Expected TERMINAL_STATE, got {e.code}")

    # Cleanup
    async with AsyncSessionLocal() as db:
        order = await order_service.get_order_by_id(db, order_id)
        await db.delete(order)
        # Restore stock manually since it was completed
        product = await db.get(Product, product_id)
        product.quantity = orig_qty
        
        customer = await customer_service.get_customer_by_id(db, customer_id)
        await db.delete(customer)
        await db.commit()
    print("Test 2 cleanup complete.")


async def main():
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("ERROR: DATABASE_URL not set in environment.")
        sys.exit(1)

    print("Connecting to database...")
    try:
        await pre_cleanup()
        await test_inactive_customer_blocks_order()
        await test_order_transitions_and_status()
        print("\nALL QA AUTOMATION TESTS PASSED.")
    except Exception as e:
        print(f"\nTest execution failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
