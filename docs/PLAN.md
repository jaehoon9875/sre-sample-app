# PLAN.md

## Stage 진행 현황


| Stage   | 내용                              | 상태    |
| ------- | ------------------------------- | ----- |
| Stage 1 | 개발 환경 + CI/AI 자동화 설정            | ✅ 완료   |
| Stage 2 | order-service 구현                | ⬜ 미시작 |
| Stage 3 | inventory-service 구현 + 서비스 간 통신 | ⬜ 미시작 |
| Stage 4 | notification-service 구현         | ⬜ 미시작 |
| Stage 5 | Nginx + Kubernetes + GKE 배포     | ⬜ 미시작 |
| Stage 6 | Observability 연동                | ⬜ 미시작 |
| Stage 7 | SRE 실습 (장애 시뮬레이션 + 포스트모텀)       | ⬜ 미시작 |


---

## Stage 1 - 개발 환경 + CI/AI 자동화 설정

**목표**: 코드를 작성하기 전에 리뷰 환경과 로컬 인프라를 먼저 구성한다. Python에 익숙하지 않은 만큼, 모든 PR에 AI 코드 리뷰가 자동으로 달리는 환경을 갖추는 것이 핵심.

### 체크리스트

**로컬 개발 환경**

- `docker-compose.yml` 작성 — PostgreSQL, Redis, Kafka, Zookeeper, Nginx, 각 서비스 포함
- 각 서비스 `.env.example` 작성 (DATABASE_URL, REDIS_URL, KAFKA_BOOTSTRAP_SERVERS 등)
- `docker-compose up -d` 후 전체 스택 정상 기동 확인

**GitHub Actions CI**

- `.github/workflows/ci.yml` 작성 — PR 시 자동 실행
  - lint: `ruff` 또는 `flake8`
  - type check: `mypy`
  - test: `pytest` (각 서비스별)
- `.github/PULL_REQUEST_TEMPLATE.md` 작성

**AI 코드 리뷰 자동화**

- CodeRabbit GitHub App 설치 및 레포 연동
- `.coderabbit.yml` 작성 — 프로젝트 규칙 기반 리뷰 설정
- 테스트 PR 생성 후 AI 리뷰 동작 확인

---

## Stage 2 - order-service 구현

**목표**: 가장 핵심 서비스인 order-service를 먼저 완성한다. 이후 서비스들의 구조 기준이 된다.

### 체크리스트

**프로젝트 기반 설정**

- `requirements.txt` 작성 (fastapi, sqlalchemy, alembic, pydantic-settings, redis, structlog 등)
- `Dockerfile` 작성 (multi-stage)
- `app/config.py` — pydantic-settings 기반 환경변수 관리

**DB 스키마 + 마이그레이션**

- `apps/order-service/app/models/order.py` — Order, OrderItem SQLAlchemy 모델 정의
- Alembic 초기화 및 첫 마이그레이션 생성
- `docker-compose exec order-service alembic upgrade head` 동작 확인

**API 구현** (router → service → repository 계층 준수)

- `POST /orders` — 주문 생성
- `GET /orders/{order_id}` — 주문 조회
- `PATCH /orders/{order_id}/status` — 주문 상태 변경
- `GET /health` — 헬스체크

**Redis 캐시 연동**

- 주문 조회 시 Redis 캐시 우선 조회, 없으면 DB 조회 후 캐시 저장
- 주문 상태 변경 시 캐시 무효화

**테스트**

- `tests/unit/` — service 레이어 단위 테스트 (외부 의존성 mock)
- `tests/integration/` — 실제 DB 사용 통합 테스트 (트랜잭션 롤백 격리)
- service 레이어 커버리지 80% 이상 확인

---

## Stage 3 - inventory-service 구현 + 서비스 간 통신

**목표**: 재고 서비스를 구현하고, order-service에서 inventory-service를 호출하는 서비스 간 통신과 Circuit Breaker를 적용한다.

### 체크리스트

**inventory-service 구현**

- `apps/inventory-service/app/models/inventory.py` — Product, Stock SQLAlchemy 모델 정의
- Alembic 마이그레이션
- `POST /inventory/reserve` — 재고 차감 (요청 수량 확인 후 차감)
- `GET /inventory/{product_id}` — 재고 조회
- 단위/통합 테스트

**order-service → inventory-service 통신**

- order 생성 시 inventory-service 재고 차감 호출
- `tenacity` 기반 retry 로직 적용 (최대 3회, exponential backoff)
- inventory-service 응답 실패 시 명시적 fallback 처리 (503 반환)
- 통합 테스트 — inventory-service mock 기반 시나리오 테스트

---

## Stage 4 - notification-service 구현

**목표**: Kafka 이벤트를 수신하여 비동기 알림을 발송하는 서비스를 구현한다. Celery + Redis Task Queue 구조를 직접 경험한다.

### 체크리스트

**Celery + Redis 설정**

- `apps/notification-service/celery_app.py` — Celery 인스턴스 설정 (broker: Redis)
- Celery worker Dockerfile 작성
- `docker-compose`에 celery worker 서비스 추가

**Kafka consumer**

- order-service에서 주문 생성 시 Kafka 이벤트 발행 (`order.created` topic)
- notification-service에서 `order.created` 이벤트 수신
- 이벤트 수신 시 Celery Task로 알림 발송 처리

**알림 발송 API**

- `POST /notifications/send` — 알림 발송 요청 (이메일/웹훅)
- `GET /notifications/{notification_id}` — 발송 결과 조회

**테스트**

- Celery Task 단위 테스트 (eager mode)
- Kafka consumer 단위 테스트 (mock consumer)

---

## Stage 5 - Nginx + Kubernetes + GKE 배포

**목표**: 전체 서비스를 Kubernetes 위에 올리고 ArgoCD로 GitOps 배포 파이프라인을 구성한다.

### 체크리스트

**Nginx 설정**

- `nginx/nginx.conf` — API Gateway 라우팅 (서비스별 upstream 설정)
- Rate Limiting 설정 (`limit_req_zone`)

**Kubernetes 매니페스트**

- `k8s/order-service/` — Deployment, Service, ConfigMap, Secret
- `k8s/inventory-service/` — 동일 구조
- `k8s/notification-service/` — 동일 구조 + Celery worker Deployment
- `k8s/nginx/` — Deployment, Service (LoadBalancer 또는 Ingress)

**GitHub Actions CI 확장**

- `ci.yml`에 Docker 이미지 빌드 + Artifact Registry push 추가
- 이미지 태그 자동 업데이트 (commit SHA 기반)

**GKE 배포**

- cloud-sre-platform에서 ArgoCD Application 등록
- `k8s/` 변경 시 ArgoCD 자동 감지 및 배포 확인
- `curl http://<GKE_EXTERNAL_IP>/health` 동작 확인

---

## Stage 6 - Observability 연동

**목표**: 모든 서비스에 메트릭, 트레이싱, 로깅을 연동하여 Grafana에서 전체 흐름을 관찰할 수 있게 한다.

### 체크리스트

**OpenTelemetry + Prometheus**

- 각 서비스 `main.py`에 FastAPIInstrumentor, SQLAlchemyInstrumentor 적용
- Prometheus metrics 엔드포인트 (`/metrics`) 노출
- Grafana에서 각 서비스 메트릭 확인

**structlog + trace_id 미들웨어**

- 각 서비스에 trace_id 주입 미들웨어 추가
- 요청 단위로 trace_id가 모든 로그에 포함되는지 확인
- Loki에서 trace_id로 로그 검색 확인

**분산 트레이싱**

- order → inventory → notification 요청 흐름이 Tempo에서 단일 trace로 연결 확인

---

## Stage 7 - SRE 실습 (장애 시뮬레이션 + 포스트모텀)

**목표**: 실제 장애를 재현하고 대응 절차를 경험한다. SLO 기반으로 영향도를 측정하고 포스트모텀을 작성한다.

### 체크리스트

**SLO 정의**

- `docs/slo.md` 작성 — 가용성/지연 SLO 및 Error Budget 계산 기준

**장애 시나리오 (순서대로 진행)**

- `postmortem-001`: inventory-service 다운 → Circuit Breaker 동작 확인
- `postmortem-002`: DB connection pool 고갈 → 503 반환 확인
- `postmortem-003`: Kafka consumer lag 증가 → 알림 지연 확인
- `postmortem-004`: Celery worker OOM → 작업 유실 확인
- `postmortem-005`: Redis 다운 → 캐시 fallback → DB 직접 조회 확인

**각 시나리오 진행 방식**

1. `docs/runbooks/` 에 장애 대응 절차서 먼저 작성
2. 장애 시뮬레이션 실행 (docker-compose stop 또는 리소스 제한)
3. Grafana 메트릭 / Loki 로그로 현상 확인
4. 복구 및 `docs/postmortems/` 에 포스트모텀 작성

---

## 이슈 및 메모

진행 중 발생한 이슈 및 미해결 항목은 **[ISSUES.md](ISSUES.md)** 에서 관리합니다.


| #   | 단계  | 요약      | 상태  |
| --- | --- | ------- | --- |
| -   | -   | (아직 없음) | -   |


