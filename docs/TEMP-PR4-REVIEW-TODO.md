# TEMP-PR4-REVIEW-TODO.md

PR: https://github.com/jaehoon9875/sre-sample-app/pull/4
작성일: 2026-04-16
목적: CodeRabbit 리뷰 코멘트 임시 정리 및 다음 작업 우선순위 관리

---

## 현재 상황 요약

- CodeRabbit 코멘트 다수(약 24개) 발생.
- 코멘트 성격이 혼합됨:
  - 즉시 반영 가치가 큰 항목
  - 스타일/권장사항
  - Stage 3+ 범위 확장 항목(이번 PR 범위 밖)
- 일부는 이미 반영되었거나 현재 코드 기준 재검증이 필요한 항목.

---

## 다음 작업 (복귀 시 가장 먼저 할 일)

아래 순서대로 처리한다. 다른 작업보다 이 문서 항목을 우선한다.

1. [x] PR #4의 최신 코멘트 다시 로드 후, 항목별로 `유효/무효/보류` 분류
2. [x] 우선순위 높음 4개를 먼저 수정
3. [x] 테스트/체크 재실행 후 푸시
4. [x] 보류 항목은 Stage 3+ 백로그로 분리 기록

---

## 우선순위 높음 (이번 PR에서 우선 검토/수정)

1) [x] Alembic async migration 패턴 정리 (`apps/order-service/alembic/env.py`)
- `context.configure`와 `run_migrations`를 같은 `run_sync` 흐름으로 묶는 방식 검토.

1) [x] Migration downgrade enum 정리 (`apps/order-service/alembic/versions/9314af2d1ea2_create_orders_table.py`)
- `orderstatus` enum type 제거 누락 여부 점검 및 필요 시 `downgrade()`에 정리 로직 추가.

1) [x] 서비스 반환 타입 일관성 (`apps/order-service/app/services/order.py`)
- 캐시 히트 시 `dict` 반환 vs 시그니처 `Order | None` 불일치 해결.

1) [x] Redis 의존성 수명주기 (`apps/order-service/app/dependencies.py`)
- 요청마다 클라이언트 생성/종료 방식 개선 검토(앱 수명주기 단위 재사용).

---

## 코멘트 분류 결과 (2026-04-17)

- `유효(반영 완료)`: 고우선 4건(`alembic/env.py`, `migration downgrade enum`, `service 반환 타입`, `redis 수명주기`) 및 `apps/order-service/app/repositories/order.py`의 `create()` `type: ignore` 제거까지 코드 반영/검증 완료.
- `유효(추가 확인 필요)`: 없음.
- `보류`: Stage 3+ 범위 항목(inventory 연동/리트라이/통합 테스트 확장, Postgres 테스트 트랜잭션 전환, 런타임/개발 의존성 분리 등)은 이번 PR에서 분리 유지.
- `무효`: 없음 (최신 코멘트 원문 조회 완료 기준).

---

## 중간 우선순위 (시간 여유 시)

- [ ] `apps/order-service/README.md` 오타 수정 (`실브로커` 표현)
  <!-- TODO: README에서 '실브로커' 표현을 일관된 용어로 수정 -->
- [ ] Markdown fence 공백 규칙(MD031) 정리
  <!-- TODO: apps/CLAUDE.md, docs/PLAN.md의 코드펜스 전후 공백 규칙 적용 -->
  - `apps/CLAUDE.md`
  - `docs/PLAN.md`
- [ ] 테스트 함수/fixture 타입 힌트 보강
  <!-- TODO: tests/conftest.py, tests/unit/test_order_service.py에 반환 타입 힌트 추가 -->
- [ ] e2e timeout 예외를 `asyncio.TimeoutError`로 명시
  <!-- TODO: e2e Kafka 테스트에서 TimeoutError를 asyncio.TimeoutError로 통일 -->

---

## 이번 PR 범위 밖 (분리 권장: Stage 3+)

- inventory-service reserve 호출 + retry + 실패 시 503 흐름
- reserve 실패 경로 단위/통합 테스트 확장
- 테스트 DB를 Postgres 트랜잭션 롤백 구조로 전환
- requirements 런타임/개발 의존성 분리
- Dockerfile non-root/healthcheck 강화

---

## 작업 메모

- 커밋 메시지 규칙(사용자 요청):
  - 키워드(type/scope)는 영어 유지
  - 제목/본문 내용은 한글로 작성
  - 예: `fix(order): 설정 로딩 실패 수정`
