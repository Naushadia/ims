from decimal import Decimal
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
        order = Order(
            customer_id=data.customer_id,
            status="created",
            total_amount=Decimal("0.00"),
            email_note=data.email_note
        )
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


def send_order_confirmation_email_sync(order: Order):
    """
    Sends a beautifully designed order confirmation email using Gmail SMTP.
    Runs inside a thread pool (via background_tasks) to prevent blocking async.
    """
    smtp_user = os.environ.get("SMTP_USER", "sadabia854318@gmail.com")
    smtp_password = os.environ.get("SMTP_PASSWORD", "hwsayenivquiutnt")
    
    if not smtp_user or not smtp_password:
        print("WARNING: SMTP credentials not set. Skipping email.")
        return
        
    customer = order.customer
    if not customer or not customer.email:
        print(f"WARNING: Order #{order.id} has no customer email. Skipping email.")
        return

    to_email = customer.email
    subject = f"Order Confirmation — #{order.id:04d}"

    # Build items HTML table
    items_rows_html = ""
    for item in order.items:
        product_name = item.product.name if item.product else f"Product ID {item.product_id}"
        sku = item.product.sku if item.product else "—"
        price = float(item.unit_price)
        qty = item.quantity
        subtotal = price * qty
        items_rows_html += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: sans-serif; font-size: 14px; color: #2d3748;">{product_name} ({sku})</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: sans-serif; font-size: 14px; color: #2d3748; text-align: right;">₹{price:.2f}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: sans-serif; font-size: 14px; color: #2d3748; text-align: center;">{qty}</td>
            <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-family: sans-serif; font-size: 14px; color: #2d3748; text-align: right; font-weight: bold;">₹{subtotal:.2f}</td>
        </tr>
        """

    # Build note HTML if present
    note_html = ""
    if order.email_note and order.email_note.strip():
        note_html = f"""
        <div style="background-color: #fef3c7; border-left: 4px solid #d97706; padding: 15px; margin: 20px 0; border-radius: 4px;">
            <p style="margin: 0 0 4px 0; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #b45309; text-transform: uppercase;">Note from sender:</p>
            <p style="margin: 0; font-family: sans-serif; font-size: 14px; color: #78350f; font-style: italic;">"{order.email_note.strip()}"</p>
        </div>
        """

    body_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{subject}</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f7fafc;">
        <table width="100%" border="0" cellspacing="0" cellpadding="0" style="background-color: #f7fafc; padding: 30px 15px;">
            <tr>
                <td align="center">
                    <table width="600" border="0" cellspacing="0" cellpadding="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06); overflow: hidden; border: 1px solid #e2e8f0;">
                        <!-- Header banner -->
                        <tr>
                            <td style="background-color: #d97706; padding: 30px 40px; text-align: left;">
                                <h1 style="margin: 0; font-family: sans-serif; font-size: 24px; color: #ffffff; font-weight: 700;">IMS — Order Confirmed</h1>
                                <p style="margin: 4px 0 0 0; font-family: sans-serif; font-size: 14px; color: #ffedd5; opacity: 0.9;">Thank you for your order!</p>
                            </td>
                        </tr>
                        
                        <!-- Content area -->
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 16px 0; font-family: sans-serif; font-size: 16px; color: #2d3748; line-height: 1.5;">
                                    Hello <strong>{customer.full_name}</strong>,
                                </p>
                                <p style="margin: 0 0 24px 0; font-family: sans-serif; font-size: 15px; color: #4a5568; line-height: 1.6;">
                                    Your order <strong>#{order.id:04d}</strong> has been successfully placed. We are preparing it for processing. Below is your order summary:
                                </p>

                                {note_html}

                                <!-- Items Table -->
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" style="border-collapse: collapse; margin-bottom: 24px;">
                                    <thead>
                                        <tr style="background-color: #f7fafc;">
                                            <th align="left" style="padding: 10px; border-bottom: 2px solid #e2e8f0; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #718096; text-transform: uppercase;">Product</th>
                                            <th align="right" style="padding: 10px; border-bottom: 2px solid #e2e8f0; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #718096; text-transform: uppercase;">Price</th>
                                            <th align="center" style="padding: 10px; border-bottom: 2px solid #e2e8f0; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #718096; text-transform: uppercase;">Qty</th>
                                            <th align="right" style="padding: 10px; border-bottom: 2px solid #e2e8f0; font-family: sans-serif; font-size: 12px; font-weight: bold; color: #718096; text-transform: uppercase;">Subtotal</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {items_rows_html}
                                        <!-- Total row -->
                                        <tr>
                                            <td colspan="2" style="padding: 15px 10px; border-top: 2px solid #e2e8f0;"></td>
                                            <td align="right" style="padding: 15px 10px; border-top: 2px solid #e2e8f0; font-family: sans-serif; font-size: 14px; font-weight: bold; color: #4a5568;">Total</td>
                                            <td align="right" style="padding: 15px 10px; border-top: 2px solid #e2e8f0; font-family: sans-serif; font-size: 16px; font-weight: bold; color: #d97706;">₹{float(order.total_amount):.2f}</td>
                                        </tr>
                                    </tbody>
                                </table>

                                <div style="border-top: 1px solid #e2e8f0; padding-top: 24px; font-family: sans-serif; font-size: 12px; color: #a0aec0; text-align: center;">
                                    If you have any questions regarding your order, please contact warehouse support.
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f7fafc; padding: 20px 40px; text-align: center; border-top: 1px solid #e2e8f0;">
                                <p style="margin: 0; font-family: sans-serif; font-size: 12px; color: #718096;">
                                    © 2026 IMS Warehouse Operations Inc. All Rights Reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        print(f"SMTP: Connecting to {smtp_server}:{smtp_port}...")
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            print(f"SMTP: Logging in as {smtp_user}...")
            server.login(smtp_user, smtp_password)
            print(f"SMTP: Sending order email to {to_email}...")
            server.sendmail(smtp_user, to_email, msg.as_string())
            print(f"SMTP: Confirmation email sent for Order #{order.id:04d}!")
    except Exception as e:
        print(f"SMTP ERROR: Failed to send confirmation email: {e}")

