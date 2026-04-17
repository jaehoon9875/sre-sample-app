import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.order import OrderStatus


# ── 요청 스키마 ──────────────────────────────────────────────────────────────
# 클라이언트가 API 에 보내는 데이터 구조를 정의한다.
# Pydantic 이 자동으로 타입 검증 + 에러 메시지를 처리해준다.

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)       # gt=0: 0보다 커야 함 (greater than)
    price: Decimal = Field(gt=0)      # 단가도 0보다 커야 함


class OrderCreate(BaseModel):
    user_id: int
    items: list[OrderItemCreate] = Field(min_length=1)  # 최소 1개 이상의 아이템


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


# ── 응답 스키마 ──────────────────────────────────────────────────────────────
# 서버가 클라이언트에게 돌려주는 데이터 구조를 정의한다.

class OrderItemResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    product_id: int
    quantity: int
    price: Decimal

    # from_attributes=True: SQLAlchemy 모델 객체를 Pydantic 모델로 변환할 수 있게 한다.
    # router 에서 return order 하면 Pydantic 이 order.id, order.status 등을 자동으로 읽는다.
    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: int
    status: OrderStatus
    total_price: Decimal
    created_at: datetime
    items: list[OrderItemResponse]

    model_config = {"from_attributes": True}
