# k8s/CLAUDE.md

## 역할

ArgoCD가 감시하는 Kubernetes 매니페스트 디렉토리.
이 경로의 변경이 Git에 머지되면 ArgoCD가 자동으로 감지하여 GKE에 배포한다.

## ⚠️ 주의사항

- **`kubectl apply` 또는 `helm upgrade`로 직접 클러스터를 수정하지 않는다.**
- 모든 변경은 반드시 이 디렉토리 파일 수정 → Git push → ArgoCD sync 경로로만 반영한다.
- `k8s/` 변경이 포함된 PR은 머지 전 반드시 영향 범위를 확인한다.

## ArgoCD 연결

ArgoCD는 [cloud-sre-platform](https://github.com/jaehoon9875/cloud-sre-platform) repo에서 관리한다.
이 repo의 `k8s/` 경로를 Application source로 등록되어 있다.

인프라 자체(ArgoCD 설정, Kafka/Redis/PostgreSQL Helm chart 등)를 변경해야 한다면
**이 repo가 아닌 cloud-sre-platform repo에서 작업한다.**

## 디렉토리 구조

```
k8s/
├── nginx/                  # Nginx API Gateway
├── order-service/          # 주문 서비스
├── inventory-service/      # 재고 서비스
└── notification-service/   # 알림 서비스 (FastAPI + Celery worker)
```

각 서비스 디렉토리에 들어갈 매니페스트:

| 파일 | 설명 |
|------|------|
| `deployment.yaml` | Pod 스펙, 이미지 태그, 환경변수 |
| `service.yaml` | ClusterIP 서비스 |
| `configmap.yaml` | 비민감 환경변수 |
| `secret.yaml` | 민감 환경변수 (실제 값은 GKE Secret 또는 외부 시크릿으로 관리) |

## 이미지 태그 관리

CI에서 Docker 이미지를 빌드하고 Artifact Registry에 push한 후,
`deployment.yaml`의 이미지 태그를 commit SHA로 자동 업데이트한다.
이 업데이트가 Git push되면 ArgoCD가 자동으로 배포한다.
