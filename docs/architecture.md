# Architecture

> **상태**: 설계 단계 — 실제 구현 및 배포로 검증되지 않았습니다. 구현 과정에서 변경될 수 있으며, 변경 시 이 문서를 함께 업데이트합니다.
>
> <!-- TODO: Stage 2 완료 후 Kafka 이벤트 흐름(order.created 발행/소비) 실제 동작 검증 결과 반영 -->
> <!-- TODO: Stage 3 완료 후 OpenSearch 인덱싱 파이프라인 검증 결과 반영 -->

이 문서는 sre-sample-app의 전체 아키텍처와 주요 설계 결정 근거를 설명합니다.
인프라(GKE, Kafka, OpenSearch 등)의 실제 구성은 [cloud-sre-platform](https://github.com/jaehoon9875/cloud-sre-platform)에서 관리합니다.

---

## 서비스 흐름

```text
[Client]
   ↓
[Nginx — API Gateway / Rate Limiting]
   ↓
[order-service]  ──── PostgreSQL (주문 저장)
   │              └─── Redis (캐시)
   │
   └─ Kafka (order.created 이벤트 발행)
         │
         ├─ [inventory-service]
         │       ├── PostgreSQL (재고 차감)
         │       └── OpenSearch (재고 이벤트 인덱싱)
         │
         └─ [notification-service]
                 └── Celery Task 발행
                         ↓
                 [Celery worker] — 알림 발송 (이메일/웹훅)
```

---

## 컴포넌트 설명

### order-service

- 주문 생성/조회/상태 변경 API (FastAPI)
- 주문 생성 시 `order.created` Kafka 이벤트 발행
- Redis를 통한 주문 캐싱 (캐시 우선 조회, 상태 변경 시 무효화)
- SRE 시나리오: DB connection pool 고갈 → 503 반환

### inventory-service

- 재고 확인/차감 API (FastAPI)
- `order.created` 이벤트 소비 → 재고 차감 처리
- 재고 이벤트를 OpenSearch에 인덱싱 (재고 이력 검색 목적)
- SRE 시나리오: Kafka consumer lag 증가 → 알림 지연

### notification-service

- `order.created` 이벤트 소비 → Celery Task 발행
- Celery worker가 실제 알림 발송 처리 (이메일/웹훅)
- SRE 시나리오: Celery worker OOM → 작업 유실

### Celery worker

- notification-service와 코드베이스를 공유하되, GKE 배포 시 별도 Deployment로 분리
- batch-pool(spot 노드)에 배치 — 이유: CPU/메모리 단기 집중 사용 패턴으로 app-pool과 혼용 시 FastAPI 응답 시간 영향

---

## 인프라 구성

### Kafka (3-broker 클러스터, KRaft 모드)

- Replication factor 3으로 운영하여 브로커 1대 장애 시에도 가용성 유지
- GKE data-pool(고정 노드)에 배치 — spot 노드 사용 시 replication 중 노드 종료로 데이터 유실 위험 있음
- topic: `order.created`

### OpenSearch (3-node 클러스터)

- inventory-service가 재고 이벤트 인덱싱
- GKE data-pool(고정 노드)에 배치 — shard 복구 중 노드 종료 시 인덱스 손상 위험 있음
- 과거 Watchtek에서 Flink → OpenSearch 파이프라인을 운영한 경험을 클라우드 환경으로 이식

### GKE Node Pool

| pool | 머신 타입 | spot | 배치 대상 |
|------|----------|------|---------|
| system-pool | e2-small × 1 | 고정 | 시스템 pod |
| app-pool | e2-standard-2 × 0~3 | spot | FastAPI 3개, Redis, Nginx |
| data-pool | e2-standard-4 × 3 | 고정 | Kafka 3 브로커, OpenSearch 3노드, PostgreSQL |
| batch-pool | e2-standard-2 × 0~N | spot | Celery worker |

---

## 서비스 간 통신

| 방향 | 방식 | 비고 |
|------|------|------|
| order → inventory | HTTP (동기) | tenacity retry, circuit breaker |
| order → Kafka | 비동기 이벤트 발행 | order.created topic |
| Kafka → inventory | 비동기 이벤트 소비 | consumer group 기반 |
| Kafka → notification | 비동기 이벤트 소비 | consumer group 기반 |
| notification → Celery | Task 발행 | Redis broker |

### Circuit Breaker

inventory-service 다운 시 order-service의 동기 호출이 실패합니다.
Circuit Breaker 패턴을 적용하여 연쇄 장애(cascading failure)를 방지합니다.

---

## SRE 실습 시나리오

| 시나리오 | 서비스 | 현상 | 대응 |
|---------|-------|------|------|
| DB connection pool 고갈 | order | 503 다량 발생 | pool 크기 조정, 지연 모니터링 |
| Kafka consumer lag 증가 | inventory | 재고 처리 지연 | lag 알람, consumer 스케일 아웃 |
| Celery worker OOM | notification | 작업 유실 | worker 리소스 제한 조정, DLQ 구성 |
| inventory-service 다운 | order → inventory | Circuit Breaker 동작 | fallback 처리 확인 |
| Redis 다운 | order | 캐시 fallback → DB 직접 조회 | DB 부하 증가 모니터링 |
