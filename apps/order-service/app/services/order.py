import json
import uuid

import redis.asyncio as aioredis
import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.kafka import producer as kafka_producer
from app.models.order import Order, OrderStatus
from app.repositories.order import OrderRepository
from app.schemas.order import OrderCreate
from app.schemas.order import OrderResponse

logger = structlog.get_logger()

# Redis 캐시 키 패턴. order_id 를 포맷해서 사용한다.
# 예: "order:550e8400-e29b-41d4-a716-446655440000"
CACHE_KEY = "order:{order_id}"
CACHE_TTL = 300  # 초 단위 (5분)


def _order_to_dict(order: Order) -> dict:
    """
    Order 모델 객체를 JSON 직렬화 가능한 dict 로 변환하는 헬퍼.
    Redis 에 저장할 때 사용한다.
    """
    return {
        "id": str(order.id),
        "user_id": order.user_id,
        "status": order.status.value,
        "total_price": str(order.total_price),  # Decimal 은 str 로 변환
        "created_at": order.created_at.isoformat(),
        "items": [
            {
                "id": str(item.id),
                "order_id": str(item.order_id),
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price": str(item.price),
            }
            for item in order.items
        ],
    }


class OrderService:
    """
    비즈니스 로직 담당 클래스.
    DB 접근은 OrderRepository 에 위임하고,
    캐시·Kafka 등 외부 서비스 조율은 이 클래스에서 처리한다.
    """

    def __init__(self, db: AsyncSession, redis: aioredis.Redis) -> None:
        self.repo = OrderRepository(db)
        self.redis = redis

    async def create_order(self, data: OrderCreate) -> Order:
        # 1. DB 에 주문 저장
        order = await self.repo.create(data)
        logger.info("order_created", order_id=str(order.id), user_id=order.user_id)

        # 2. Kafka 이벤트 발행.
        #    실패해도 주문 자체는 유지한다 (이벤트 유실은 별도로 처리할 운영 이슈).
        try:
            await kafka_producer.publish_order_created(order)
        except Exception as e:
            logger.error("kafka_publish_failed", order_id=str(order.id), error=str(e))

        return order

    async def get_order(self, order_id: uuid.UUID) -> OrderResponse | None:
        cache_key = CACHE_KEY.format(order_id=order_id)

        # 1. Redis 캐시 먼저 조회
        try:
            cached = await self.redis.get(cache_key)
        except Exception as exc:
            logger.warning("order_cache_get_failed", order_id=str(order_id), error=str(exc))
            cached = None
        if cached:
            try:
                logger.info("order_cache_hit", order_id=str(order_id))
                return OrderResponse.model_validate_json(cached)
            except Exception as exc:
                logger.warning("order_cache_deserialize_failed", order_id=str(order_id), error=str(exc))

        # 2. 캐시 미스: DB 조회
        order = await self.repo.get_by_id(order_id)
        if order is None:
            return None

        # 3. 조회 결과를 캐시에 저장 (TTL 300초)
        try:
            await self.redis.set(cache_key, json.dumps(_order_to_dict(order)), ex=CACHE_TTL)
            logger.info("order_cache_set", order_id=str(order_id))
        except Exception as exc:
            logger.warning("order_cache_set_failed", order_id=str(order_id), error=str(exc))
        return OrderResponse.model_validate(order, from_attributes=True)

    async def update_status(self, order_id: uuid.UUID, status: OrderStatus) -> Order | None:
        # 1. DB 업데이트
        order = await self.repo.update_status(order_id, status)
        if order is None:
            return None

        # 2. 캐시 무효화: 상태가 바뀌었으므로 캐시를 지워서 다음 조회 때 DB 에서 새로 읽게 한다
        cache_key = CACHE_KEY.format(order_id=order_id)
        try:
            await self.redis.delete(cache_key)
            logger.info("order_cache_invalidated", order_id=str(order_id), new_status=status)
        except Exception as exc:
            logger.warning(
                "order_cache_invalidate_failed",
                order_id=str(order_id),
                new_status=status,
                error=str(exc),
            )

        return order
