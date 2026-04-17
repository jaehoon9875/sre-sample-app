import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import UUID, Enum, ForeignKey, Integer, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# SQLAlchemy 모델의 공통 베이스 클래스.
# 모든 테이블 모델은 이 Base 를 상속한다.
class Base(DeclarativeBase):
    pass


# 주문 상태를 나타내는 Enum.
# str 을 함께 상속하면 JSON 직렬화 시 "PENDING" 같은 문자열로 자동 변환된다.
class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"       # 결제 대기
    CONFIRMED = "CONFIRMED"   # 주문 확정
    CANCELLED = "CANCELLED"   # 취소


class Order(Base):
    __tablename__ = "orders"  # 실제 DB 테이블명

    # Mapped[타입] 은 Python 타입 힌트와 SQLAlchemy 컬럼을 동시에 선언하는 방식 (SQLAlchemy 2.0+)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),   # DB에 UUID 타입으로 저장
        primary_key=True,
        default=uuid.uuid4,   # INSERT 시 자동으로 uuid4 생성
    )
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),    # DB에 Enum 타입으로 저장
        default=OrderStatus.PENDING,
        nullable=False,
    )
    # Numeric(10, 2): 소수점 2자리까지 저장하는 고정소수점 타입 (금액에 적합)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # server_default=func.now(): INSERT 시 DB 서버 시각을 자동으로 기록
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    # 1:N 관계 선언. Order 하나에 여러 OrderItem 이 속한다.
    # cascade="all, delete-orphan": Order 삭제 시 연결된 OrderItem 도 함께 삭제
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ForeignKey: orders.id 를 참조하는 외래키
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)  # 단가

    # N:1 관계 선언. OrderItem 여러 개가 Order 하나에 속한다.
    order: Mapped["Order"] = relationship("Order", back_populates="items")
