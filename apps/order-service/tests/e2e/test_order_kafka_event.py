import asyncio
import json
import uuid

import httpx
import pytest
from aiokafka import AIOKafkaConsumer


@pytest.mark.asyncio
@pytest.mark.kafka
async def test_order_created_event_published_to_kafka():
    """
    실제 order-service + Kafka 연동 환경에서 주문 생성 이벤트 발행을 검증한다.
    - 필요 조건:
      1) Kafka 브로커가 localhost:29092 에서 접근 가능
      2) order-service 가 localhost:8001 에서 실행 중
    """
    consumer = AIOKafkaConsumer(
        "order.created",
        bootstrap_servers="localhost:29092",
        group_id=f"order-e2e-{uuid.uuid4()}",
        auto_offset_reset="latest",
        enable_auto_commit=False,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )

    try:
        await consumer.start()
    except Exception as exc:  # pragma: no cover - e2e 환경 체크용
        pytest.skip(f"Kafka not reachable at localhost:29092: {exc}")

    try:
        async with httpx.AsyncClient(base_url="http://localhost:8001", timeout=10.0) as client:
            try:
                health = await client.get("/health")
            except Exception as exc:  # pragma: no cover - e2e 환경 체크용
                pytest.skip(f"order-service not reachable at localhost:8001: {exc}")

            if health.status_code != 200:
                pytest.skip(f"order-service /health returned {health.status_code}")

            response = await client.post(
                "/orders",
                json={
                    "user_id": 1,
                    "items": [
                        {"product_id": 101, "quantity": 2, "price": "15000.00"},
                    ],
                },
            )

        assert response.status_code == 201
        created_order = response.json()
        expected_order_id = created_order["id"]

        found_event = None
        for _ in range(15):
            try:
                record = await asyncio.wait_for(consumer.getone(), timeout=1.0)
            except TimeoutError:
                continue

            payload = record.value
            if payload.get("order_id") == expected_order_id:
                found_event = payload
                break

        assert found_event is not None, "order.created 이벤트를 Kafka에서 찾지 못했습니다."
        assert found_event["user_id"] == 1
        assert len(found_event["items"]) == 1
        assert found_event["items"][0]["product_id"] == 101
        assert found_event["items"][0]["quantity"] == 2
    finally:
        await consumer.stop()
