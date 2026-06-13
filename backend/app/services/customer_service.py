from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AppError
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate


async def get_all_customers(db: AsyncSession) -> list[Customer]:
    result = await db.execute(select(Customer).order_by(Customer.id))
    return list(result.scalars().all())


async def get_customer_by_id(db: AsyncSession, customer_id: int) -> Customer:
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if customer is None:
        raise AppError(
            message=f"Customer with ID {customer_id} not found.",
            code="CUSTOMER_NOT_FOUND",
            status_code=404,
        )
    return customer


async def create_customer(db: AsyncSession, data: CustomerCreate) -> Customer:
    # Pre-check email uniqueness for a clean error message
    existing = await db.execute(
        select(Customer).where(Customer.email == data.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise AppError(
            message=f"A customer with email '{data.email}' already exists.",
            code="DUPLICATE_EMAIL",
            status_code=409,
        )

    customer = Customer(
        full_name=data.full_name,
        email=data.email,
        phone=data.phone,
    )
    db.add(customer)
    try:
        await db.commit()
        await db.refresh(customer)
    except IntegrityError:
        await db.rollback()
        raise AppError(
            message=f"A customer with email '{data.email}' already exists.",
            code="DUPLICATE_EMAIL",
            status_code=409,
        )
    return customer


async def delete_customer(db: AsyncSession, customer_id: int) -> None:
    customer = await get_customer_by_id(db, customer_id)
    try:
        await db.delete(customer)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            message=(
                f"Cannot delete customer '{customer.full_name}' — they have existing orders."
            ),
            code="CUSTOMER_HAS_ORDERS",
            status_code=409,
        )
