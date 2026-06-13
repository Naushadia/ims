from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import AppError
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


async def get_all_products(db: AsyncSession) -> list[Product]:
    result = await db.execute(select(Product).order_by(Product.id))
    return list(result.scalars().all())


async def get_product_by_id(db: AsyncSession, product_id: int) -> Product:
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if product is None:
        raise AppError(
            message=f"Product with ID {product_id} not found.",
            code="PRODUCT_NOT_FOUND",
            status_code=404,
        )
    return product


async def create_product(db: AsyncSession, data: ProductCreate) -> Product:
    # Check SKU uniqueness before hitting the DB constraint for a clean error message
    existing = await db.execute(
        select(Product).where(Product.sku == data.sku)
    )
    if existing.scalar_one_or_none() is not None:
        raise AppError(
            message=f"A product with SKU '{data.sku}' already exists.",
            code="DUPLICATE_SKU",
            status_code=409,
        )

    product = Product(
        name=data.name,
        sku=data.sku,
        price=data.price,
        quantity=data.quantity,
    )
    db.add(product)
    try:
        await db.commit()
        await db.refresh(product)
    except IntegrityError:
        await db.rollback()
        raise AppError(
            message=f"A product with SKU '{data.sku}' already exists.",
            code="DUPLICATE_SKU",
            status_code=409,
        )
    return product


async def update_product(
    db: AsyncSession, product_id: int, data: ProductUpdate
) -> Product:
    product = await get_product_by_id(db, product_id)

    if data.name is not None:
        product.name = data.name
    if data.price is not None:
        product.price = data.price
    if data.quantity is not None:
        if data.quantity < 0:
            raise AppError(
                message="Product quantity cannot be negative.",
                code="NEGATIVE_QUANTITY",
                status_code=422,
            )
        product.quantity = data.quantity

    await db.commit()
    await db.refresh(product)
    return product


async def delete_product(db: AsyncSession, product_id: int) -> None:
    product = await get_product_by_id(db, product_id)
    try:
        await db.delete(product)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppError(
            message=(
                f"Cannot delete product '{product.name}' — it is referenced by existing order items."
            ),
            code="PRODUCT_IN_USE",
            status_code=409,
        )
