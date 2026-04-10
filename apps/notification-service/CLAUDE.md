# notification-service/CLAUDE.md

공통 개발 원칙 → [apps/CLAUDE.md](../CLAUDE.md)

---

## 서비스 역할

Kafka 이벤트를 수신하여 이메일/웹훅 알림을 비동기로 발송하는 서비스.
Celery + Redis를 Task Queue로 사용하며, FastAPI는 발송 상태 조회 API 역할만 담당.

## 컴포넌트 구성

```
[Kafka consumer] → order.created 이벤트 수신
       ↓
[Celery Task 발행] → Redis Queue
       ↓
[Celery Worker] → 알림 발송 처리
```

FastAPI 앱과 Celery Worker는 별도 프로세스로 실행된다 (docker-compose에서 별도 서비스).

## API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/notifications/send` | 알림 발송 요청 (즉시 Celery Task로 위임) |
| GET | `/notifications/{notification_id}` | 발송 결과 조회 |
| GET | `/health` | 헬스체크 |

## Kafka consumer

- **구독 topic**: `order.created`
- 이벤트 수신 시 Celery Task(`send_notification`) 발행
- consumer group id: `notification-service`

## 환경변수 (.env.example)

```
REDIS_URL=redis://localhost:6379/1
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CONSUMER_GROUP=notification-service
LOG_LEVEL=INFO
```

## Celery 설정

```python
# celery_app.py
from celery import Celery

celery_app = Celery(
    "notification",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.task_serializer = "json"
```

## 주의사항

- Celery Worker OOM 시 처리 중인 Task가 유실될 수 있음 (SRE 실습 시나리오 postmortem-004)
- Kafka consumer lag 증가 시 알림 지연 발생 (postmortem-003)
- Worker와 API 서버는 같은 이미지를 사용하되, 실행 커맨드로 분리 (`celery worker` vs `uvicorn`)
