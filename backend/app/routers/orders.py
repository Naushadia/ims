from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.order import DashboardSummary, OrderCreate, OrderListResponse, OrderResponse, OrderStatusUpdate
from app.services import order_service

router = APIRouter()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get(
    "/dashboard/summary",
    response_model=DashboardSummary,
    status_code=status.HTTP_200_OK,
    tags=["Dashboard"],
)
async def dashboard_summary(db: AsyncSession = Depends(get_db)) -> DashboardSummary:
    return await order_service.get_dashboard_summary(db)


# ── Orders ────────────────────────────────────────────────────────────────────

@router.get(
    "/orders",
    response_model=OrderListResponse,
    status_code=status.HTTP_200_OK,
)
async def list_orders(db: AsyncSession = Depends(get_db)) -> OrderListResponse:
    orders = await order_service.get_all_orders(db)
    return OrderListResponse(data=orders, count=len(orders))


@router.get(
    "/orders/{order_id}",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def get_order(
    order_id: int, db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    order = await order_service.get_order_by_id(db, order_id)
    return OrderResponse.model_validate(order)


@router.post(
    "/orders",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_order(
    data: OrderCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    order = await order_service.create_order(db, data)
    background_tasks.add_task(order_service.send_order_confirmation_email_background, order.id)
    return OrderResponse.model_validate(order)


@router.put(
    "/orders/{order_id}/status",
    response_model=OrderResponse,
    status_code=status.HTTP_200_OK,
)
async def update_order_status(
    order_id: int, data: OrderStatusUpdate, db: AsyncSession = Depends(get_db)
) -> OrderResponse:
    order = await order_service.update_order_status(
        db, order_id, data.status, data.cancellation_reason
    )
    return OrderResponse.model_validate(order)


@router.delete(
    "/orders/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_order(
    order_id: int, db: AsyncSession = Depends(get_db)
) -> None:
    await order_service.delete_order(db, order_id)
