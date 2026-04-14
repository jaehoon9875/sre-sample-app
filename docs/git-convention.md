# Git Convention

이 프로젝트의 브랜치 전략 및 커밋 메시지 규칙을 정의합니다.
CodeRabbit 코드 리뷰와 GitHub PR 워크플로우를 전제로 합니다.

---

## 브랜치 전략

### 기본 원칙

- **`main` 브랜치는 항상 배포 가능한 상태를 유지합니다.** `main`에 직접 push는 금지합니다.
- 모든 작업은 별도 브랜치에서 진행하고, PR을 통해 `main`에 머지합니다.
- PR 머지 전 CodeRabbit 자동 리뷰가 실행됩니다. 리뷰 내용을 반드시 확인합니다.

### 브랜치 네이밍

```
feat/<설명>      새 기능 추가        예: feat/order-create-api
fix/<설명>       버그 수정           예: fix/inventory-connection-pool
refactor/<설명>  리팩토링            예: refactor/notification-celery-task
docs/<설명>      문서 작업           예: docs/architecture-update
chore/<설명>     설정, 빌드 등       예: chore/ci-ruff-lint
```

### PR 작성 규칙

- PR 제목은 커밋 메시지 형식과 동일하게 작성합니다.
- PR 본문에는 변경 내용 요약, 테스트 방법, 관련 이슈를 포함합니다.
- `.github/PULL_REQUEST_TEMPLATE.md` 템플릿을 사용합니다.
- CodeRabbit 리뷰 결과는 무시하지 않습니다. 동의하지 않는 경우 코멘트로 근거를 남깁니다.

---

## 커밋 메시지

### 형식

```
<type>(<scope>): <subject>
```

### type

| type | 설명 |
|------|------|
| `feat` | 새 기능 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `refactor` | 기능 변경 없는 코드 구조 개선 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드, 패키지, CI 설정 등 |

### scope

| scope | 대상 |
|-------|------|
| `order` | order-service |
| `inventory` | inventory-service |
| `notification` | notification-service |
| `k8s` | Kubernetes 매니페스트 |
| `docs` | 문서 |
| `ci` | GitHub Actions 워크플로우 |

### 예시

```
feat(order): 주문 생성 API 구현
fix(inventory): connection pool 고갈 시 503 반환
docs(docs): architecture.md OpenSearch 추가 반영
chore(ci): ruff lint 워크플로우 추가
```

---

## AI 코드 리뷰 (CodeRabbit)

PR 생성 시 CodeRabbit이 자동으로 리뷰를 달아줍니다.

- PR 본문에 변경 맥락을 충분히 작성하면 리뷰 품질이 올라갑니다.
- SRE/Platform 관점의 코드(K8s 매니페스트, 모니터링 설정)는 Observability와 안정성을 우선으로 고려합니다.
- `.coderabbit.yml`에 프로젝트 규칙이 설정되어 있습니다.
