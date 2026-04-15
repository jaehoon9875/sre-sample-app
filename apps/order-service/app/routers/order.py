import uuid

import redis.asyncio as aioredis
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_redis
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.services.order import OrderService

# prefix="/orders": 이 라우터의 모든 경로 앞에 /orders 가 붙는다.
# tags=["orders"]: Swagger UI 에서 그룹으로 묶인다.
router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    body: OrderCreate,
    # Depends: FastAPI 가 요청마다 자동으로 DB 세션/Redis 클라이언트를 주입해준다.
    # Java 의 @Autowired + 요청 스코프 빈과 유사한 개념.
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> OrderResponse:
    order = await OrderService(db, redis).create_order(body)
    # response_model=OrderResponse 가 선언되어 있으면 FastAPI 가 자동으로 직렬화한다.
    # SQLAlchemy 모델 → OrderResponse (from_attributes=True 덕분에 가능)
    return order  # type: ignore[return-value]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,          # 경로 변수. FastAPI 가 UUID 타입으로 자동 파싱한다.
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> OrderResponse:
    result = await OrderService(db, redis).get_order(order_id)
    if result is None:
        # HTTPException: FastAPI 가 자동으로 {"detail": "Order not found"} JSON 응답을 만든다.
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return result  # type: ignore[return-value]


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: uuid.UUID,
    body: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
) -> OrderResponse:
    result = await OrderService(db, redis).update_status(order_id, body.status)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return result  # type: ignore[return-value]
