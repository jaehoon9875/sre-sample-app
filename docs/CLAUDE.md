# docs/CLAUDE.md

이 디렉토리는 프로젝트의 설계 문서, 의사결정 기록, 운영 가이드, 진행 계획을 관리합니다.

---

## 문서 구조

| 파일/디렉토리 | 용도 |
|---------------|------|
| [PLAN.md](PLAN.md) | Stage별 구현 계획 및 체크리스트. 현재 진행 단계 파악 시 참조 |
| [ISSUES.md](ISSUES.md) | 진행 중 이슈, 미해결 항목, 보류 결정 사항 추적 |
| [architecture.md](architecture.md) | 전체 아키텍처 설명, 서비스 간 관계, 주요 설계 결정 |
| [slo.md](slo.md) | SLO 정의 및 Error Budget 계산 기준 |
| [observability-guide.md](observability-guide.md) | OpenTelemetry + Prometheus 연동 가이드 (모든 서비스 공통) |
| [ai-workflows.md](ai-workflows.md) | GitHub Actions + Claude AI 자동화 워크플로우 목록 및 설명 |
| [runbooks/](runbooks/) | 장애 유형별 대응 절차서 |
| [postmortems/](postmortems/) | 장애 포스트모텀 기록 |

서비스 공통 개발 원칙 및 각 서비스 도메인 상세 → [apps/CLAUDE.md](../apps/CLAUDE.md)
Kubernetes 매니페스트 및 ArgoCD 배포 → [k8s/CLAUDE.md](../k8s/CLAUDE.md)

---

## 문서 작성 규칙

- 진행하면서 채워야 할 항목은 `<!-- TODO: ... -->` 주석으로 표시한다.
- `architecture.md`는 서비스/인프라 구조에 변경이 생기면 반드시 업데이트한다.
- `runbooks/`는 실제 장애를 경험한 후 추가하거나 보완한다.
- `ISSUES.md`의 이슈가 해결되면 해결 날짜와 방법을 기록한 뒤 해결 이슈 섹션으로 이동한다.
