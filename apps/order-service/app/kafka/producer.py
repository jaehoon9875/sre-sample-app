import json

import structlog
from aiokafka import AIOKafkaProducer

from app.config import settings
from app.models.order import Order

logger = structlog.get_logger()

# 모듈 레벨 싱글톤 producer.
# 앱 시작 시 start(), 종료 시 stop() 을 호출해서 생명주기를 관리한다.
_producer: AIOKafkaProducer | None = None


async def start() -> None:
    """앱 시작 시 Kafka 커넥션을 맺는다 (main.py lifespan 에서 호출)."""
    global _producer
    _producer = AIOKafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
    await _producer.start()
    logger.info("kafka_producer_started")


async def stop() -> None:
    """앱 종료 시 Kafka 커넥션을 닫는다 (main.py lifespan 에서 호출)."""
    global _producer
    if _producer is not None:
        await _producer.stop()
        logger.info("kafka_producer_stopped")


async def publish_order_created(order: Order) -> None:
    """
    주문 생성 이벤트를 "order.created" 토픽으로 발행한다.
    inventory-service 와 notification-service 가 이 토픽을 구독한다.
    """
    if _producer is None:
        # 로컬 테스트 등 Kafka 없는 환경에서는 경고만 남기고 넘어간다
        logger.warning("kafka_producer_not_initialized", order_id=str(order.id))
        return

    payload = {
        "order_id": str(order.id),
        "user_id": order.user_id,
        "items": [
            {"product_id": item.product_id, "quantity": item.quantity}
            for item in order.items
        ],
    }

    # send_and_wait: 브로커가 메시지를 받았다고 확인(ack)할 때까지 기다린다.
    # 메시지는 bytes 로 직렬화해서 보낸다.
    await _producer.send_and_wait(
        "order.created",
        json.dumps(payload).encode("utf-8"),
    )
    logger.info("order_created_event_published", order_id=str(order.id))
