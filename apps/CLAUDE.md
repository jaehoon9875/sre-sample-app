# apps/CLAUDE.md

3개 서비스(order, inventory, notification)에 공통으로 적용되는 Python/FastAPI 개발 원칙.
서비스별 도메인 상세는 각 서비스 하위 `CLAUDE.md` 참고.

---

## Python 버전

**Python 3.12** 사용. 모든 서비스 공통.

- `X | None` union 문법, `match` 등 3.10+ 문법 사용 가능
- 각 서비스 디렉토리에 `.python-version` 파일로 pyenv 버전 고정
- Dockerfile 베이스 이미지도 `python:3.12-slim` 사용

로컬 환경 세팅:
```bash
brew install python@3.12  # 아직 없으면 설치
cd apps/order-service
python3.12 -m venv .venv  # 반드시 python3.12 로 venv 생성
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 기본 규칙

- 모든 함수에 타입 힌트 필수 (파라미터 + 반환값)
- DB / HTTP / 외부 IO는 전부 `async`
- 입출력 검증은 Pydantic v2 사용. `dict` 직접 사용 금지.
- 의존성 주입은 FastAPI `Depends` 사용
- 환경변수는 `pydantic-settings BaseSettings` 사용. 하드코딩 절대 금지.

## 계층 구조 (의존 방향 엄수)

```
router → service → repository → model
```

- `router`: HTTP 요청/응답만. 비즈니스 로직 없음.
- `service`: 비즈니스 로직 + 외부 서비스 호출.
- `repository`: DB 접근만. SQL/ORM 쿼리.
- `model`: SQLAlchemy 모델. 비즈니스 로직 없음.

router에서 repository를 직접 호출하지 않는다.

## 디렉토리 구조 (서비스 공통)

```
{service}/
├── app/
│   ├── main.py          # FastAPI 앱 초기화, 미들웨어, 라우터 등록
│   ├── config.py        # pydantic-settings 환경변수
│   ├── dependencies.py  # FastAPI Depends 함수 모음
│   ├── models/          # SQLAlchemy 모델
│   ├── schemas/         # Pydantic 입출력 스키마
│   ├── routers/         # FastAPI 라우터
│   ├── services/        # 비즈니스 로직
│   └── repositories/    # DB 접근
├── tests/
│   ├── unit/            # service 레이어 단위 테스트 (mock 사용)
│   └── integration/     # 실제 DB 사용 통합 테스트 (트랜잭션 롤백)
├── alembic/             # DB 마이그레이션
├── Dockerfile
├── requirements.txt
└── .env.example
```

## 환경변수 관리

```python
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(env_file=".env")

settings = Settings()
```

## 에러 처리

- 외부 호출은 반드시 예외 처리
- `400`: 클라이언트 오류 (재시도 불필요)
- `404`: 리소스 없음
- `503`: 의존 서비스 불가 (재시도 가능)
- 서비스 간 HTTP 호출에는 retry + fallback 명시적으로 정의 (`tenacity` 사용)

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import httpx

@retry(
    retry=retry_if_exception_type(httpx.HTTPError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
)
async def call_external_service(...):
    ...
```

## 로깅

- `structlog` 사용. `print()` 절대 금지.
- 주요 이벤트마다 관련 ID(order_id, user_id 등) 포함하여 기록
- trace_id는 미들웨어에서 자동 주입되므로 별도 추출 불필요

```python
import structlog
logger = structlog.get_logger()

logger.info("order_created", order_id=order_id, user_id=user_id)
logger.error("inventory_call_failed", order_id=order_id, error=str(e))
```

## 테스트

- **모든 기능 작성 시 테스트 코드를 함께 작성한다.**
- 단위 테스트: `pytest-asyncio` + `httpx.AsyncClient`, 외부 의존성 mock
- 통합 테스트: 실제 DB 사용, 트랜잭션 롤백으로 격리
- 커버리지 목표: service 레이어 80% 이상

```python
@pytest.mark.asyncio
async def test_create_order_success(async_client: AsyncClient, mock_inventory):
    mock_inventory.return_value = True
    response = await async_client.post("/orders", json={...})
    assert response.status_code == 201
```
