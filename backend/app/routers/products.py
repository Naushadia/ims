from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.get("", response_model=ProductListResponse, status_code=status.HTTP_200_OK)
async def list_products(db: AsyncSession = Depends(get_db)) -> ProductListResponse:
    products = await product_service.get_all_products(db)
    return ProductListResponse(data=products, count=len(products))


@router.get("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def get_product(
    product_id: int, db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    product = await product_service.get_product_by_id(db, product_id)
    return ProductResponse.model_validate(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate, db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    product = await product_service.create_product(db, data)
    return ProductResponse.model_validate(product)


@router.put("/{product_id}", response_model=ProductResponse, status_code=status.HTTP_200_OK)
async def update_product(
    product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)
) -> ProductResponse:
    product = await product_service.update_product(db, product_id, data)
    return ProductResponse.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await product_service.delete_product(db, product_id)
