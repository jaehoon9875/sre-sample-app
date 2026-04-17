# order-service 테스트 가이드

order-service 테스트는 목적에 따라 두 가지로 나뉜다.

- 기본 테스트: 빠르고 안정적인 회귀 검증 (Kafka 실브로커 의존 없음)
- Kafka e2e 테스트: 실제 Kafka 이벤트 발행/소비까지 포함한 통합 검증

## 1) 기본 테스트 (권장 기본 루틴)

```bash
cd apps/order-service
source .venv/bin/activate
pytest tests/ -m "not kafka" -v
```

- unit/integration 테스트를 실행한다.
- Kafka 실브로커 연동 테스트는 제외한다.
- 로컬 개발 및 PR 전 기본 확인으로 사용한다.

## 2) Kafka e2e 테스트 (실발행 검증)

```bash
cd apps/order-service
source .venv/bin/activate
pytest tests/e2e/test_order_kafka_event.py -m kafka -v -rs
```

- 주문 생성 후 `order.created` 이벤트가 Kafka에 실제 발행되는지 검증한다.
- `-rs` 옵션을 사용하면 skip 사유를 바로 확인할 수 있다.

## e2e 전제조건

Kafka e2e 테스트는 아래 조건이 맞아야 실행된다.

- Kafka 브로커 접근 가능: `localhost:29092`
- order-service 실행 중: `http://localhost:8001` (`/health` 응답 200)

예시:

```bash
# 프로젝트 루트
docker compose up -d postgres redis kafka

# 새 터미널
cd apps/order-service
source .venv/bin/activate
uvicorn app.main:app --reload --port 8001
```

## 결과 해석

- `PASSED`: 이벤트 실발행/소비 검증 성공
- `SKIPPED`: 환경 미충족(예: Kafka 또는 order-service 미기동)으로 실패가 아님
- `FAILED`: 코드/환경 문제로 실제 검증 실패. 로그와 skip 사유를 우선 확인
