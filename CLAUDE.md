# CLAUDE.md

AI가 이 프로젝트를 도울 때 반드시 읽어야 하는 컨텍스트 파일.

## 프로젝트 목적

- 클라우드 환경에서 실무 수준의 Python MSA 구축 및 운영 실습
- SRE 역량 강화: SLO 정의 → 장애 시뮬레이션 → 포스트모텀 사이클 경험
- 주력 언어는 Java, Python은 학습 중

## 레포지토리 관계

```
cloud-sre-platform     → 인프라 (GKE, ArgoCD, Kafka, Redis, PostgreSQL Helm)
observability-platform → 모니터링 스택 (Prometheus, Grafana, Loki, Tempo)
sre-sample-app         → 이 레포. 앱 코드 + k8s 매니페스트만 관리.
```

이 repo에서 인프라 Helm chart를 작성하지 않는다. `k8s/` 매니페스트만 관리하며 ArgoCD가 이를 바라본다.

## 디렉토리 구조

```
.github/workflows/   CI/CD + AI 자동화 워크플로우
docs/                설계 문서, 계획, 이슈, SLO, 런북, 포스트모텀
k8s/                 ArgoCD 배포 대상 Kubernetes 매니페스트
order-service/       주문 서비스 (FastAPI + PostgreSQL + Redis)
inventory-service/   재고 서비스 (FastAPI + PostgreSQL)
notification-service/ 알림 서비스 (FastAPI + Celery + Redis + Kafka)
```

### 진행 관리 문서

- 새 작업 단계 시작 전 `docs/PLAN.md`에 Stage와 체크리스트 먼저 작성
- 이슈 발생 시 즉시 `docs/ISSUES.md`에 기록 (심각도 분류 후 추가)
- Stage 완료 시 PLAN.md 상태 업데이트, 해결된 이슈는 ISSUES.md 해결 섹션으로 이동

## Git Convention

브랜치는 단순하게 운영한다. `main`에 직접 커밋하되, 기능 단위 작업은 `feature/` 브랜치를 활용한다.

### 커밋 메시지

```
<type>(<scope>): <subject>

type: feat | fix | docs | refactor | test | chore
scope: order | inventory | notification | k8s | docs | ci
```

예시: `feat(order): 주문 생성 API 구현`, `fix(inventory): connection pool 고갈 시 503 반환`

---

## Python 구현 원칙

### 기본 규칙

- 모든 함수에 타입 힌트 필수 (파라미터 + 반환값)
- DB / HTTP / 외부 IO는 전부 `async`
- 입출력 검증은 Pydantic v2 사용. `dict` 직접 사용 금지.
- 의존성 주입은 FastAPI `Depends` 사용
- 환경변수는 `pydantic-settings BaseSettings` 사용. 하드코딩 절대 금지.

### 계층 구조 (의존 방향 엄수)

```
router → service → repository → model
```

- `router`: HTTP 요청/응답만. 비즈니스 로직 없음.
- `service`: 비즈니스 로직 + 외부 서비스 호출.
- `repository`: DB 접근만. SQL/ORM 쿼리.
- `model`: SQLAlchemy 모델. 비즈니스 로직 없음.

router에서 repository를 직접 호출하지 않는다.

### 에러 처리

- 외부 호출은 반드시 예외 처리
- `400`: 클라이언트 오류 (재시도 불필요)
- `503`: 의존 서비스 불가 (재시도 가능)
- 서비스 간 HTTP 호출에는 retry + fallback을 명시적으로 정의한다 (`tenacity` 사용)

### 로깅

- `structlog` 사용. `print()` 절대 금지.
- 주요 이벤트마다 `trace_id` 포함하여 기록

### 테스트

- **모든 기능 작성 시 테스트 코드를 함께 작성한다.**
- 단위 테스트: 외부 의존성 mock 처리 (`pytest-asyncio`, `httpx.AsyncClient`)
- 통합 테스트: 실제 DB 사용, 트랜잭션 롤백으로 격리
- 커버리지 목표: service 레이어 80% 이상

---

## 현재 진행 상태

현재 **시작 전** 단계입니다.

단계별 체크리스트 → [docs/PLAN.md](docs/PLAN.md)
진행 중 이슈 → [docs/ISSUES.md](docs/ISSUES.md)

## 참고 문서

docs 디렉토리 전체 문서 목록 → [docs/CLAUDE.md](docs/CLAUDE.md)

---

## Important Rules

- 인프라 변경(Kafka topic, Redis 설정 등)은 cloud-sre-platform repo에서 작업한다. 이 repo에서 Helm chart를 작성하지 않는다.
- `k8s/` 변경은 ArgoCD 자동 배포를 트리거한다. 머지 전 반드시 확인한다.
- 기능 추가·수정·삭제 등 변경이 생기면 `docs/` 하위 문서를 확인하고, 업데이트가 필요한 문서가 있으면 함께 반영한다.
- 시크릿(DB 패스워드, API 키 등)은 코드나 설정 파일에 하드코딩하지 않는다. `.env` 파일은 `.gitignore`에 포함되어 있어야 한다.
- push 전에 민감 정보가 스테이징되어 있지 않은지 반드시 확인한다.
