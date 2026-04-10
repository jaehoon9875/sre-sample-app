# inventory-service/CLAUDE.md

공통 개발 원칙 → [apps/CLAUDE.md](../CLAUDE.md)

---

## 서비스 역할

상품별 재고 수량을 관리하는 서비스.
order-service로부터 재고 차감 요청을 받아 처리한다.

## DB 스키마

**products**

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | int | PK |
| name | str | 상품명 |
| stock | int | 현재 재고 수량 |
| updated_at | timestamp | |

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/inventory/reserve` | 재고 차감 (수량 확인 후 차감) |
| GET | `/inventory/{product_id}` | 재고 조회 |
| GET | `/health` | 헬스체크 |

**재고 차감 요청/응답**

```json
// 요청
{ "order_id": "...", "product_id": 1, "quantity": 3 }

// 성공 응답
{ "success": true, "remaining_stock": 7 }

// 재고 부족 응답 (400)
{ "success": false, "detail": "Insufficient stock" }
```

## 환경변수 (.env.example)

```
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/inventory
LOG_LEVEL=INFO
```

## 주의사항

- 재고 차감은 동시 요청 시 race condition 방지를 위해 DB 수준 락 또는 optimistic locking 사용
- 재고 부족 시 `400` 반환 (클라이언트 오류, 재시도 불필요)
- 서비스 다운 시 order-service의 Circuit Breaker가 동작하여 `503` 반환
