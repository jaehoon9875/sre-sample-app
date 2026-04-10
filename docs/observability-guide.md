# Observability 연동 가이드

모든 서비스에 공통 적용되는 Observability 설정입니다.

## OpenTelemetry + Prometheus 초기화 (main.py)

```python
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

FastAPIInstrumentor.instrument_app(app)
SQLAlchemyInstrumentor().instrument()
Instrumentator().instrument(app).expose(app)
```

## 수집 경로

| 신호 | 수집 도구 | 저장소 |
|------|-----------|--------|
| Metrics | Prometheus | Prometheus |
| Traces | OpenTelemetry SDK | Tempo |
| Logs | Alloy | Loki |

## trace_id 주입

trace_id는 미들웨어에서 자동으로 모든 로그에 주입됩니다. 로그 작성 시 별도로 추출할 필요 없습니다.

```python
# structlog는 미들웨어가 주입한 trace_id를 자동으로 포함
logger.info("order_created", order_id=order_id, user_id=user_id)
```

## 로그 레벨 기준

| 레벨 | 기준 |
|------|------|
| DEBUG | 개발 중 상세 디버깅 정보 |
| INFO | 정상적인 주요 흐름 (주문 생성, 상태 변경 등) |
| WARNING | 예상된 예외 (재시도, fallback 동작) |
| ERROR | 처리 실패 (응답 불가 상태) |
