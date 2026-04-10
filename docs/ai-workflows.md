# AI 활용 워크플로우

이 프로젝트에서 GitHub Actions + Claude API로 운영하는 자동화 워크플로우입니다.

> 각 워크플로우는 `anthropic/claude-code-action` 또는 Claude API 직접 호출 방식을 사용합니다.
> 세부 구현은 `.github/workflows/` 하위 각 파일 주석 참고.

---

## 워크플로우 목록

| 워크플로우 | 트리거 | 설명 |
|---|---|---|
| `ai-code-review.yml` | PR 생성/업데이트 | 코드 리뷰 자동화 |
| `ai-refactor.yml` | 이슈에 `refactor` 라벨 추가 | 리팩토링 제안 |
| `ai-test-gen.yml` | 이슈에 `test-needed` 라벨 추가 | 테스트 코드 초안 생성 |
| `ai-doc-update.yml` | main 브랜치 머지 | 문서 자동 업데이트 PR 생성 |
| `ai-issue-analysis.yml` | 이슈에 `analyze` 라벨 추가 | 이슈 원인 분석 및 개선 제안 |

---

## 1. 코드 리뷰 자동화 (`ai-code-review.yml`)

PR 생성/업데이트 시 자동 트리거. 검토 항목:

- Python 구현 원칙 준수 여부 (타입 힌트, 계층 구조, 에러 처리)
- 보안 취약점 (하드코딩된 시크릿, SQL injection 가능성)
- 테스트 누락 여부
- 성능 이슈 (N+1 쿼리, 불필요한 동기 호출)

## 2. 리팩토링 제안 (`ai-refactor.yml`)

이슈에 `refactor` 라벨 추가 시 트리거. 해당 파일을 분석하고 리팩토링 전략 코멘트.

## 3. 테스트 코드 자동 생성 (`ai-test-gen.yml`)

이슈에 `test-needed` 라벨 추가 시 트리거. 지정한 파일의 테스트 코드 초안 생성 후 PR 코멘트.

## 4. 문서 자동화 (`ai-doc-update.yml`)

main 브랜치 머지 시 트리거. API 변경 감지 → `docs/` 업데이트 PR 자동 생성.

## 5. 이슈 분석 및 개선 제안 (`ai-issue-analysis.yml`)

이슈에 `analyze` 라벨 추가 시 트리거. 이슈 내용 + 관련 코드 분석 → 원인 및 해결 방향 코멘트.
