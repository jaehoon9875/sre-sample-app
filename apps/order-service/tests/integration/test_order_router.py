import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


# ── 공통 페이로드 ────────────────────────────────────────────────────────────

ORDER_PAYLOAD = {
    "user_id": 1,
    "items": [
        {"product_id": 101, "quantity": 2, "price": "15000.00"}
    ],
}


# ── 테스트 ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_order(async_client: AsyncClient):
    """
    POST /orders 가 주문을 생성하고 201 을 반환하는지 확인.
    실제 DB(인메모리 SQLite) 에 INSERT 가 일어난다.
    """
    # Kafka 발행은 mock 처리 (테스트 환경에 Kafka 서버 없음)
    with patch("app.kafka.producer.publish_order_created"):
        response = await async_client.post("/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == 1
    assert data["status"] == "PENDING"
    assert "id" in data
    assert len(data["items"]) == 1


@pytest.mark.asyncio
async def test_get_order(async_client: AsyncClient):
    """
    GET /orders/{order_id} 가 생성된 주문을 올바르게 반환하는지 확인.
    """
    with patch("app.kafka.producer.publish_order_created"):
        create_response = await async_client.post("/orders", json=ORDER_PAYLOAD)

    order_id = create_response.json()["id"]

    response = await async_client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    assert response.json()["id"] == order_id


@pytest.mark.asyncio
async def test_get_order_not_found(async_client: AsyncClient):
    """
    존재하지 않는 order_id 로 조회 시 404 를 반환하는지 확인.
    """
    non_existent_id = str(uuid.uuid4())
    response = await async_client.get(f"/orders/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


@pytest.mark.asyncio
async def test_update_order_status(async_client: AsyncClient):
    """
    PATCH /orders/{order_id}/status 로 상태 변경이 정상 동작하는지 확인.
    """
    with patch("app.kafka.producer.publish_order_created"):
        create_response = await async_client.post("/orders", json=ORDER_PAYLOAD)

    order_id = create_response.json()["id"]

    response = await async_client.patch(
        f"/orders/{order_id}/status",
        json={"status": "CONFIRMED"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_health(async_client: AsyncClient):
    """헬스체크 엔드포인트가 200 을 반환하는지 확인."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
