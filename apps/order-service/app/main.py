from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI

from app.kafka import producer as kafka_producer
from app.routers import order

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    앱의 시작/종료 시점에 실행되는 코드를 정의한다.
    yield 이전: 앱 시작 시 실행 (리소스 초기화)
    yield 이후: 앱 종료 시 실행 (리소스 정리)
    Java 의 @PostConstruct / @PreDestroy 와 유사한 개념.
    """
    await kafka_producer.start()
    logger.info("order_service_started")
    yield
    await kafka_producer.stop()
    logger.info("order_service_stopped")


app = FastAPI(title="Order Service", lifespan=lifespan)

# 라우터 등록. order.router 안의 모든 엔드포인트가 app 에 추가된다.
app.include_router(order.router)


@app.get("/health")
async def health() -> dict:
    """헬스체크 엔드포인트. Kubernetes liveness/readiness probe 에서 호출한다."""
    return {"status": "ok"}
