# sre-sample-app

클라우드 환경에서 실무 수준의 Python MSA를 직접 구축하고 운영해보는 SRE 실습 프로젝트입니다.

FastAPI 기반 마이크로서비스 3개를 Kubernetes(GKE) 위에 올리고, Kafka / Redis / PostgreSQL을 연동하여 실제 서비스와 유사한 환경을 구성합니다. SLO 정의 → 장애 시뮬레이션 → 포스트모텀으로 이어지는 SRE 사이클을 반복하며 역량을 키우는 것이 목표입니다.

## 빠른 시작 (로컬)

> **사전 조건**: Docker, Docker Compose 설치 필요.

```bash
# 1. 저장소 클론
git clone https://github.com/jaehoon9875/sre-sample-app
cd sre-sample-app

# 2. 환경변수 설정
cp apps/order-service/.env.example apps/order-service/.env
cp apps/inventory-service/.env.example apps/inventory-service/.env
cp apps/notification-service/.env.example apps/notification-service/.env

# 3. 전체 스택 실행
docker-compose up -d

# 4. DB 마이그레이션
docker-compose exec order-service alembic upgrade head
docker-compose exec inventory-service alembic upgrade head


# 5. 동작 확인
curl http://localhost/health
```

## 서비스 구성

```
[Client]
   ↓
[Nginx - API Gateway / Rate Limiting]
   ↓              ↓              ↓
[order-service] [inventory-service] [notification-service]
FastAPI          FastAPI             FastAPI + Celery
PostgreSQL       PostgreSQL          Redis (Queue)
Redis (Cache)
   ↓ (Kafka event)                      ↑
   └──────────────────────────────────►─┘
```

| 서비스 | 역할 | 포트 |
|---|---|---|
| nginx | API Gateway, Rate Limiting | 80 |
| order-service | 주문 생성/조회/상태 관리 | 8001 |
| inventory-service | 재고 확인/차감 | 8002 |
| notification-service | 이메일/웹훅 알림 비동기 발송 | 8003 |

## 기술 스택

| 분류 | 기술 |
|---|---|
| Framework | FastAPI, Pydantic v2 |
| ORM | SQLAlchemy (async) + Alembic |
| Task Queue | Celery + Redis |
| Messaging | Kafka (Strimzi) |
| Cache | Redis |
| DB | PostgreSQL |
| Observability | OpenTelemetry, Prometheus, structlog |
| Test | pytest, httpx |
| Container | Docker, Kubernetes (GKE) |
| GitOps | ArgoCD |

## GKE 배포 (ArgoCD)

```bash
kubectl apply -f https://github.com/jaehoon9875/cloud-sre-platform/k8s/argocd/apps/sre-sample-app.yaml
```

이후 `k8s/` 경로 변경 시 ArgoCD가 자동 감지하여 배포합니다.

## SRE 실습 시나리오

장애 시나리오별 대응 절차 및 포스트모텀은 아래 문서를 참고하세요.

- [docs/runbooks/](docs/runbooks/) — 장애 대응 절차서
- [docs/postmortems/](docs/postmortems/) — 장애 포스트모텀 기록

## 문서

| 문서 | 설명 |
|------|------|
| [docs/PLAN.md](docs/PLAN.md) | 단계별 구현 계획 및 진행 현황 |
| [docs/ISSUES.md](docs/ISSUES.md) | 진행 중 이슈 및 미해결 항목 추적 |
| [docs/architecture.md](docs/architecture.md) | 아키텍처 결정 근거 (ADR) |
| [docs/slo.md](docs/slo.md) | SLO 정의 및 Error Budget 계산 기준 |
| [docs/runbooks/](docs/runbooks/) | 장애 대응 절차서 |
| [docs/postmortems/](docs/postmortems/) | 장애 포스트모텀 기록 |
| [docs/ai-workflows.md](docs/ai-workflows.md) | GitHub Actions + Claude AI 자동화 워크플로우 |
| [docs/observability-guide.md](docs/observability-guide.md) | OpenTelemetry + Prometheus 연동 가이드 |

## 관련 프로젝트

- [observability-platform](https://github.com/jaehoon9875/observability-platform) — 모니터링 스택 (Prometheus, Grafana, Loki, Tempo)
- [cloud-sre-platform](https://github.com/jaehoon9875/cloud-sre-platform) — 인프라 관리 (GKE, ArgoCD, Kafka, Redis, PostgreSQL)
# test
