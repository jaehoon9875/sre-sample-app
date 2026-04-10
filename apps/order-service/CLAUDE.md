# order-service/CLAUDE.md

공통 개발 원칙 → [apps/CLAUDE.md](../CLAUDE.md)

---

## 서비스 역할

주문의 생성, 조회, 상태 관리를 담당하는 핵심 서비스.
재고 확인(inventory-service 호출)과 주문 이벤트 발행(Kafka)의 오케스트레이터 역할.

## DB 스키마

**orders**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| user_id | int | 주문자 ID |
| status | enum | PENDING / CONFIRMED / CANCELLED |
| total_price | decimal | 총 금액 |
| created_at | timestamp | |

**order_items**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | UUID | PK |
| order_id | UUID | FK → orders.id |
| product_id | int | 상품 ID |
| quantity | int | 수량 |
| price | decimal | 단가 |

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/orders` | 주문 생성 (재고 차감 → Kafka 이벤트 발행) |
| GET | `/orders/{order_id}` | 주문 조회 (Redis 캐시 우선) |
| PATCH | `/orders/{order_id}/status` | 주문 상태 변경 |
| GET | `/health` | 헬스체크 |

## 환경변수 (.env.example)

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/orders
REDIS_URL=redis://localhost:6379/0
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
INVENTORY_SERVICE_URL=http://inventory-service:8002
LOG_LEVEL=INFO
```

## 의존 서비스

- **inventory-service**: 주문 생성 시 `POST /inventory/reserve` 호출하여 재고 차감
  - 실패 시 주문 생성 롤백, 503 반환
  - retry 3회, exponential backoff 적용

## Kafka 이벤트

- **발행**: 주문 확정 시 `order.created` topic으로 이벤트 발행
  ```json
  { "order_id": "...", "user_id": 1, "items": [...] }
  ```

## Redis 캐시 전략

- 주문 조회 시 `order:{order_id}` 키로 캐시 우선 조회 (TTL: 300초)
- 주문 상태 변경 시 해당 캐시 무효화
