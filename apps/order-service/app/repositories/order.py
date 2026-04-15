import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate


class OrderRepository:
    """
    DB 접근 전담 클래스. SQL/ORM 쿼리만 여기에 작성한다.
    비즈니스 로직(캐시, Kafka 등)은 작성하지 않는다.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: OrderCreate) -> Order:
        # 총 금액 계산: 각 아이템의 (단가 × 수량) 합계
        total_price = sum(item.price * item.quantity for item in data.items)

        # Order 객체 생성 (아직 DB 에 저장된 게 아님)
        order = Order(
            user_id=data.user_id,
            total_price=total_price,
            # items 에 OrderItem 리스트를 넘기면 SQLAlchemy 가 관계를 자동으로 처리한다
            items=[
                OrderItem(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price=item.price,
                )
                for item in data.items
            ],
        )

        self.db.add(order)        # 세션에 추가 (INSERT 예약)
        await self.db.commit()    # 실제 DB 에 INSERT 실행
        await self.db.refresh(order)  # DB 에서 생성된 값(id, created_at 등)을 다시 로딩
        return order

    async def get_by_id(self, order_id: uuid.UUID) -> Order | None:
        # selectinload: items 관계를 별도 SELECT 로 미리 로딩 (N+1 문제 방지)
        # N+1 문제: order 를 먼저 조회하고, 그 뒤 item 마다 SELECT 를 날리는 비효율 패턴
        result = await self.db.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(selectinload(Order.items))
        )
        # scalars().first(): 결과 행을 Order 객체로 변환하고 첫 번째 행 반환 (없으면 None)
        return result.scalars().first()

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> Order | None:
        order = await self.get_by_id(order_id)
        if order is None:
            return None

        order.status = status       # 속성 변경 (SQLAlchemy 가 변경 감지)
        await self.db.commit()      # UPDATE 실행
        await self.db.refresh(order)
        return order
