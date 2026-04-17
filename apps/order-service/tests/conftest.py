from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.dependencies import get_db, get_redis
from app.main import app
from app.models.order import Base

# 테스트용 인메모리 SQLite.
# 실제 PostgreSQL 대신 사용하므로 별도 DB 서버 없이 테스트 실행 가능.
# aiosqlite 패키지 필요 (requirements.txt 에 추가 필요)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    테스트마다 새 인메모리 DB 를 만들고 테스트 후 삭제한다.
    각 테스트가 독립적인 DB 상태에서 실행되므로 서로 간섭하지 않는다.
    """
    engine = create_async_engine(TEST_DATABASE_URL)

    # 테이블 생성 (실제 마이그레이션 없이 모델 기반으로 바로 생성)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    # 테스트 후 테이블 삭제 (다음 테스트를 위한 클린업)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    테스트용 HTTP 클라이언트.
    실제 서버를 띄우지 않고 ASGI 앱에 직접 요청을 보낸다.
    의존성 오버라이드로 테스트용 DB 세션과 mock Redis 를 주입한다.
    """
    from unittest.mock import AsyncMock

    # get_db 의존성을 테스트용 db_session 으로 교체
    app.dependency_overrides[get_db] = lambda: db_session

    # get_redis 의존성을 AsyncMock 으로 교체 (실제 Redis 서버 불필요)
    mock_redis = AsyncMock()
    mock_redis.get.return_value = None   # 기본적으로 캐시 미스 상태
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    app.dependency_overrides[get_redis] = lambda: mock_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    # 테스트 후 오버라이드 초기화
    app.dependency_overrides.clear()
