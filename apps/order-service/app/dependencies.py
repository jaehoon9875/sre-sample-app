from collections.abc import AsyncGenerator

import redis.asyncio as aioredis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# 비동기 DB 엔진 생성.
# pool_pre_ping=True: 커넥션 풀에서 꺼낼 때 DB 연결이 살아있는지 먼저 확인한다.
# pool_size / max_overflow 는 기본값(5/10) 사용. 운영 시 튜닝 포인트.
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)

# 세션 팩토리. 실제 세션은 이 팩토리를 통해 만들어진다.
# expire_on_commit=False: commit 이후에도 모델 객체의 속성에 접근 가능하게 한다.
#   (True 이면 commit 후 다시 DB 에서 로딩하려 해서 async 환경에서 오류 발생 가능)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI Depends 용 DB 세션 제공 함수.
    요청마다 세션을 열고, 요청이 끝나면 자동으로 닫는다.
    Java 의 @Transactional 과 유사한 역할.
    """
    async with AsyncSessionLocal() as session:
        # yield: 이 지점에서 세션을 라우터/서비스에 넘겨준다.
        # 요청 처리가 끝나면 async with 블록이 종료되며 session.close() 가 자동 호출된다.
        yield session


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """
    FastAPI Depends 용 Redis 클라이언트 제공 함수.
    요청마다 커넥션을 열고, 요청이 끝나면 닫는다.
    """
    redis = aioredis.from_url(
        settings.REDIS_URL,
        encoding="utf-8",
        decode_responses=True,  # bytes 대신 str 로 자동 디코딩
    )
    try:
        yield redis
    finally:
        await redis.aclose()
