from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.customer import CustomerCreate, CustomerListResponse, CustomerResponse, CustomerUpdate
from app.services import customer_service

router = APIRouter()


@router.get("", response_model=CustomerListResponse, status_code=status.HTTP_200_OK)
async def list_customers(db: AsyncSession = Depends(get_db)) -> CustomerListResponse:
    customers = await customer_service.get_all_customers(db)
    return CustomerListResponse(data=customers, count=len(customers))


@router.get("/{customer_id}", response_model=CustomerResponse, status_code=status.HTTP_200_OK)
async def get_customer(
    customer_id: int, db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    customer = await customer_service.get_customer_by_id(db, customer_id)
    return CustomerResponse.model_validate(customer)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    data: CustomerCreate, db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    customer = await customer_service.create_customer(db, data)
    return CustomerResponse.model_validate(customer)


@router.put("/{customer_id}", response_model=CustomerResponse, status_code=status.HTTP_200_OK)
async def update_customer(
    customer_id: int, data: CustomerUpdate, db: AsyncSession = Depends(get_db)
) -> CustomerResponse:
    customer = await customer_service.update_customer(db, customer_id, data)
    return CustomerResponse.model_validate(customer)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await customer_service.delete_customer(db, customer_id)
