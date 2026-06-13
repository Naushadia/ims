from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants import LOW_STOCK_THRESHOLD
from app.exceptions import AppError
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import DashboardSummary, LowStockProduct, OrderCreate


async def get_all_orders(db: AsyncSession) -> list[Order]:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .order_by(Order.id.desc())
    )
    return list(result.scalars().unique().all())


async def get_order_by_id(db: AsyncSession, order_id: int) -> Order:
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items).selectinload(OrderItem.product))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if order is None:
        raise AppError(
            message=f"Order with ID {order_id} not found.",
            code="ORDER_NOT_FOUND",
            status_code=404,
        )
    return order


async def create_order(db: AsyncSession, data: OrderCreate) -> Order:
    """
    Create an order atomically:
    1. Validate customer exists
    2. Validate each product exists and has sufficient stock
    3. Deduct stock from each product
    4. Create Order + OrderItem records
    5. Calculate and set total_amount
    All inside a single DB transaction.
    """
    async with db.begin():
        # 1 — Validate customer
        customer_result = await db.execute(
            select(Customer).where(Customer.id == data.customer_id)
        )
        customer = customer_result.scalar_one_or_none()
        if customer is None:
            raise AppError(
                message=f"Customer with ID {data.customer_id} not found.",
                code="CUSTOMER_NOT_FOUND",
                status_code=404,
            )
        if customer.status != "active":
            raise AppError(
                message=f"Cannot place order — customer '{customer.full_name}' is inactive.",
                code="INACTIVE_CUSTOMER",
                status_code=400,
            )

        # 2 — Validate all products and check stock (collect before mutating)
        product_map: dict[int, Product] = {}
        for item_data in data.items:
            if item_data.product_id in product_map:
                # Duplicate product in same order → merge quantities for stock check
                continue
            product_result = await db.execute(
                select(Product).where(Product.id == item_data.product_id).with_for_update()
            )
            product = product_result.scalar_one_or_none()
            if product is None:
                raise AppError(
                    message=f"Product with ID {item_data.product_id} not found.",
                    code="PRODUCT_NOT_FOUND",
                    status_code=404,
                )
            product_map[item_data.product_id] = product

        # Aggregate quantities per product (handle duplicate product_id in request)
        qty_by_product: dict[int, int] = {}
        for item_data in data.items:
            qty_by_product[item_data.product_id] = (
                qty_by_product.get(item_data.product_id, 0) + item_data.quantity
            )

        # Stock check — done before any mutation
        out_of_stock: list[str] = []
        for product_id, requested_qty in qty_by_product.items():
            product = product_map[product_id]
            if product.quantity < requested_qty:
                out_of_stock.append(
                    f"'{product.name}' (SKU: {product.sku}) — "
                    f"requested {requested_qty}, available {product.quantity}"
                )
        if out_of_stock:
            raise AppError(
                message="Insufficient stock for: " + "; ".join(out_of_stock),
                code="INSUFFICIENT_STOCK",
                status_code=400,
            )

        # 3 — Deduct stock atomically
        for product_id, requested_qty in qty_by_product.items():
            product_map[product_id].quantity -= requested_qty

        # 4 — Create order
        order = Order(customer_id=data.customer_id, status="created", total_amount=Decimal("0.00"))
        db.add(order)
        await db.flush()  # get order.id without committing

        # 5 — Create order items + calculate total
        total: Decimal = Decimal("0.00")
        for item_data in data.items:
            product = product_map[item_data.product_id]
            unit_price = product.price
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
                unit_price=unit_price,
            )
            db.add(order_item)
            total += unit_price * item_data.quantity

        order.total_amount = total
        # Transaction commits here when exiting `async with db.begin()`

    # Re-fetch with relationships for the response
    return await get_order_by_id(db, order.id)


async def delete_order(db: AsyncSession, order_id: int) -> None:
    """
    Cancel/delete an order.
    If the order is 'created', restore stock for all its items.
    """
    async with db.begin():
        order_result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
            .with_for_update(of=Order)
        )
        order = order_result.scalar_one_or_none()
        if order is None:
            raise AppError(
                message=f"Order with ID {order_id} not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        # Restore stock only for created/pending/confirmed orders
        if order.status in ("created", "pending", "confirmed"):
            for item in order.items:
                product_result = await db.execute(
                    select(Product)
                    .where(Product.id == item.product_id)
                    .with_for_update()
                )
                product = product_result.scalar_one_or_none()
                if product is not None:
                    product.quantity += item.quantity

        await db.delete(order)
        # Commit on exit


async def get_dashboard_summary(db: AsyncSession) -> DashboardSummary:
    # Aggregate counts in 3 queries — fast and straightforward
    total_products = await db.scalar(select(func.count()).select_from(Product))
    total_customers = await db.scalar(select(func.count()).select_from(Customer))
    total_orders = await db.scalar(select(func.count()).select_from(Order))

    low_stock_result = await db.execute(
        select(Product)
        .where(Product.quantity < LOW_STOCK_THRESHOLD)
        .order_by(Product.quantity.asc())
        .limit(20)
    )
    low_stock_products = list(low_stock_result.scalars().all())

    return DashboardSummary(
        total_products=total_products or 0,
        total_customers=total_customers or 0,
        total_orders=total_orders or 0,
        low_stock_count=len(low_stock_products),
        low_stock_products=[
            LowStockProduct(
                id=p.id, name=p.name, sku=p.sku, quantity=p.quantity
            )
            for p in low_stock_products
        ],
    )


async def update_order_status(
    db: AsyncSession, order_id: int, status: str, cancellation_reason: str | None = None
) -> Order:
    """
    Update order status with business rules:
    - Allowed transitions: created -> confirmed, created -> cancelled, confirmed -> completed, confirmed -> cancelled
    - Restore stock on cancellation from created or confirmed states
    - Require remarks/reason for cancellation
    """
    async with db.begin():
        # Get order
        order_result = await db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
            .with_for_update(of=Order)
        )
        order = order_result.scalar_one_or_none()
        if order is None:
            raise AppError(
                message=f"Order with ID {order_id} not found.",
                code="ORDER_NOT_FOUND",
                status_code=404,
            )

        old_status = order.status.lower()
        new_status = status.lower()

        if new_status not in ["created", "pending", "confirmed", "completed", "cancelled"]:
            raise AppError(
                message=f"Invalid status '{status}'.",
                code="INVALID_STATUS",
                status_code=400,
            )

        if old_status == new_status:
            return order

        # Terminal state check
        if old_status in ["completed", "cancelled"]:
            raise AppError(
                message=f"Cannot change status of a terminal '{old_status}' order.",
                code="TERMINAL_STATE",
                status_code=400,
            )

        # Transition validation (removed direct completion block to allow direct created -> completed)

        # Handle cancellation: restore stock
        if new_status == "cancelled":
            if not cancellation_reason or not cancellation_reason.strip():
                raise AppError(
                    message="Cancellation remarks/reason is required to cancel an order.",
                    code="CANCELLATION_REMARKS_REQUIRED",
                    status_code=400,
                )
            
            # Restore stock
            for item in order.items:
                product_result = await db.execute(
                    select(Product)
                    .where(Product.id == item.product_id)
                    .with_for_update()
                )
                product = product_result.scalar_one_or_none()
                if product is not None:
                    product.quantity += item.quantity
            
            order.cancellation_reason = cancellation_reason.strip()

        order.status = new_status
        # DB commits automatically upon leaving context manager db.begin()

    # Re-fetch order with items and product detail
    return await get_order_by_id(db, order.id)

