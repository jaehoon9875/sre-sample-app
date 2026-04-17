import uuid
from datetime import datetime, UTC
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderItemCreate
from app.services.order import OrderService


# ── 픽스처 ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db() -> AsyncMock:
    """실제 DB 없이 테스트하기 위한 mock AsyncSession."""
    return AsyncMock()


@pytest.fixture
def mock_redis() -> AsyncMock:
    """실제 Redis 없이 테스트하기 위한 mock Redis 클라이언트."""
    redis = AsyncMock()
    redis.get.return_value = None   # 기본값: 캐시 미스
    return redis


@pytest.fixture
def fake_order() -> Order:
    """테스트용 Order 객체. DB 에 실제로 저장되지 않는다."""
    order = Order(
        id=uuid.uuid4(),
        user_id=1,
        status=OrderStatus.PENDING,
        total_price=Decimal("30000"),
        created_at=datetime.now(UTC),
    )
    order.items = [
        OrderItem(
            id=uuid.uuid4(),
            order_id=order.id,
            product_id=101,
            quantity=2,
            price=Decimal("15000"),
        )
    ]
    return order


# ── 테스트 ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_order_success(
    mock_db: AsyncMock,
    mock_redis: AsyncMock,
    fake_order: Order,
) -> None:
    """
    주문 생성 성공 케이스.
    - OrderRepository.create 가 호출되고 order 가 반환되는지 확인
    - Kafka 이벤트 발행이 시도되는지 확인
    """
    # patch: 특정 모듈 경로의 객체를 테스트 중에만 가짜로 교체한다.
    # "app.services.order.OrderRepository" 를 mock 으로 교체해서 DB 호출을 막는다.
    with patch("app.services.order.OrderRepository") as MockRepo, \
         patch("app.services.order.kafka_producer.publish_order_created") as mock_publish:

        # create 메서드가 fake_order 를 반환하도록 설정
        MockRepo.return_value.create = AsyncMock(return_value=fake_order)
        mock_publish.return_value = None  # Kafka 발행은 아무것도 하지 않음

        service = OrderService(db=mock_db, redis=mock_redis)
        data = OrderCreate(user_id=1, items=[OrderItemCreate(product_id=101, quantity=2, price=Decimal("15000"))])

        result = await service.create_order(data)

        # 결과 검증
        assert result.user_id == 1
        assert result.status == OrderStatus.PENDING
        MockRepo.return_value.create.assert_called_once_with(data)
        mock_publish.assert_called_once_with(fake_order)


@pytest.mark.asyncio
async def test_create_order_kafka_failure_does_not_raise(
    mock_db: AsyncMock,
    mock_redis: AsyncMock,
    fake_order: Order,
) -> None:
    """
    Kafka 발행 실패 시 주문 생성이 롤백되지 않고 정상 반환되는지 확인.
    이벤트 유실은 허용하지만 주문 자체는 유지해야 한다.
    """
    with patch("app.services.order.OrderRepository") as MockRepo, \
         patch("app.services.order.kafka_producer.publish_order_created") as mock_publish:

        MockRepo.return_value.create = AsyncMock(return_value=fake_order)
        # Kafka 발행에서 예외 발생하도록 설정
        mock_publish.side_effect = Exception("Kafka connection refused")

        service = OrderService(db=mock_db, redis=mock_redis)
        data = OrderCreate(user_id=1, items=[OrderItemCreate(product_id=101, quantity=2, price=Decimal("15000"))])

        # 예외가 전파되지 않고 order 가 정상 반환되어야 한다
        result = await service.create_order(data)
        assert result is fake_order


@pytest.mark.asyncio
async def test_get_order_cache_hit(
    mock_db: AsyncMock,
    mock_redis: AsyncMock,
    fake_order: Order,
) -> None:
    """
    Redis 캐시에 데이터가 있으면 DB 를 조회하지 않는지 확인.
    """
    import json
    from app.services.order import _order_to_dict

    # 캐시에 데이터가 있는 상태로 설정
    mock_redis.get.return_value = json.dumps(_order_to_dict(fake_order))

    with patch("app.services.order.OrderRepository") as MockRepo:
        service = OrderService(db=mock_db, redis=mock_redis)
        result = await service.get_order(fake_order.id)

        # 캐시 히트 → DB 조회 없음
        MockRepo.return_value.get_by_id.assert_not_called()
        assert result is not None


@pytest.mark.asyncio
async def test_get_order_cache_miss_sets_cache(
    mock_db: AsyncMock,
    mock_redis: AsyncMock,
    fake_order: Order,
) -> None:
    """
    캐시 미스 시 DB 에서 조회 후 Redis 에 저장하는지 확인.
    """
    import json
    from app.services.order import CACHE_TTL, _order_to_dict

    mock_redis.get.return_value = None  # 캐시 미스

    with patch("app.services.order.OrderRepository") as MockRepo:
        MockRepo.return_value.get_by_id = AsyncMock(return_value=fake_order)

        service = OrderService(db=mock_db, redis=mock_redis)
        result = await service.get_order(fake_order.id)

        # DB 조회 후 캐시 저장 확인
        assert result is not None
        MockRepo.return_value.get_by_id.assert_called_once_with(fake_order.id)
        mock_redis.set.assert_called_once_with(
            f"order:{fake_order.id}",
            json.dumps(_order_to_dict(fake_order)),
            ex=CACHE_TTL,
        )


@pytest.mark.asyncio
async def test_update_status_invalidates_cache(
    mock_db: AsyncMock,
    mock_redis: AsyncMock,
    fake_order: Order,
) -> None:
    """
    상태 변경 후 Redis 캐시가 삭제되는지 확인.
    캐시가 남아있으면 이전 상태가 계속 반환되는 버그가 발생할 수 있다.
    """
    with patch("app.services.order.OrderRepository") as MockRepo:
        MockRepo.return_value.update_status = AsyncMock(return_value=fake_order)

        service = OrderService(db=mock_db, redis=mock_redis)
        await service.update_status(fake_order.id, OrderStatus.CONFIRMED)

        # 캐시 삭제 확인
        mock_redis.delete.assert_called_once_with(f"order:{fake_order.id}")
