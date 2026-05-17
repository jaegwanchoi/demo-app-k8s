# Phase 1 — K8s 기초 (실습 노트)

> 환경: Docker Desktop Kubernetes (context: `docker-desktop`)
> 앱: web (nginx) → api (Flask) → auth (Flask)
> Namespace: `app-dev`

## Sessions

- [x] Session 1 — Namespace, Pod, Service
- [x] Session 2 — Deployment, ReplicaSet
- [x] Session 3 — ConfigMap, Secret
- [ ] Session 4 — Volume, PV, PVC
- [ ] Session 5 — Job, CronJob, DaemonSet

---

## 명령어 cheatsheet (세션 진행하며 채워나가기)

### 조회
```powershell
kubectl get nodes
kubectl get pods -n app-dev
kubectl get all -n app-dev
kubectl describe pod <name> -n app-dev
kubectl logs <pod> -n app-dev
```

### 컨텍스트
```powershell
kubectl config current-context
kubectl config use-context docker-desktop
```

### 정리
```powershell
kubectl delete namespace app-dev   # 모든 리소스 한 방에 삭제
```

---

## Session 1 메모

### 배운 객체
- **Namespace**: 논리적 격리 (RBAC/Quota 단위). 시스템 NS(default/kube-system 등)는 삭제 X
- **Pod**: 컨테이너 묶음. Mortal — 죽으면 새 IP. Raw Pod은 자가치유 X
- **Service**:
  - ClusterIP — 가상 IP, 클러스터 내부 통신용
  - NodePort — 노드 30000~32767 포트 노출 (kind 기반 DD K8s에선 직접 안 됨)

### 핵심 메커니즘
- **라벨 셀렉터** → Endpoints/EndpointSlice 자동 생성 (Service-Pod 결합)
- **CoreDNS** → `<svc>.<ns>.svc.cluster.local` 풀어줌
- **IP 대역 분리**: Pod `10.244.x.x` (CNI), Service `10.96.x.x` (가상)
- **Service IP는 가상** → kube-proxy가 노드 iptables에 규칙 박음

### 트러블슈팅 패턴
1. `kubectl describe <object>` Events 섹션 (90% 답)
2. `kubectl logs <pod>` (앱 에러)
3. 가장 작은 외부 검증 (`docker pull` 등)

### 환경 함정 메모
- Git Bash가 `/bin/sh` → Windows 경로로 자동 변환 → `kubectl exec`는 PowerShell에서 실행
- DD Kubernetes는 kind 기반 → NodePort 직접 X → `kubectl port-forward` 사용
- `Endpoints v1`은 deprecated → `EndpointSlice` 사용 권장 (`kubectl get endpointslices`)

### 자주 쓴 명령
```powershell
kubectl exec -it -n app-dev <pod> -- /bin/sh
kubectl port-forward -n app-dev svc/<name> <local>:<svc-port>
kubectl get endpointslices -n app-dev
kubectl get all -n app-dev
```

## Session 2 메모

### 배운 객체
- **Deployment**: 사람이 작성하는 객체. 버전 관리(revision history) + 무중단 배포 전략
- **ReplicaSet**: Deployment가 자동 생성. "N개 Pod 유지" 보장. 직접 만들 일 거의 없음

### Controller 패턴 (reconciliation loop)
- 원하는 상태(spec) ↔ 현재 상태(status) 끊임없이 비교 → 차이 메꿈
- 자가치유는 이 루프의 결과 (사람이 시키는 게 아님)

### 객체 계층
```
Deployment auth
   └─ ReplicaSet auth-<해시>     ← Pod 템플릿의 해시
         └─ Pod auth-<해시>-<랜덤>
```

### Service와의 느슨한 결합
- Service는 Deployment를 모름. 라벨 selector로 Pod만 잡음
- Deployment를 새로 만들거나 교체해도 Service는 자동으로 새 Pod을 backend로 등록

### 스케일링
- 명령형: `kubectl scale deployment/<name> --replicas=N` (학습/실험용)
- 선언형: yaml의 replicas 수정 후 apply (실무 표준, GitOps 호환)

### Rolling Update / Rollback
- `kubectl rollout status` — 진행 상황 watch
- `kubectl rollout history` — revision 목록
- `kubectl rollout undo --to-revision=N` — 특정 revision으로 복귀
- 동일한 Pod 템플릿은 revision 번호에 중복 보관 X → 번호에 구멍 생기는 게 정상
- 변경 이유는 `kubernetes.io/change-cause` annotation
  - `--record` 플래그는 1.22 deprecated, 1.27 제거됨
  - 권장: yaml의 metadata.annotations에 함께 두고 같이 apply (GitOps 친화적)

### Annotation vs Label
- **Label**: selector에 잡힘 → 객체 결합 (Service ↔ Pod, Deployment ↔ Pod)
- **Annotation**: selector에 안 잡힘 → 순수 메타데이터 (change-cause, ArgoCD sync-wave 등)

### 자주 쓴 명령
```powershell
kubectl scale deployment/<name> -n app-dev --replicas=N
kubectl rollout status deployment/<name> -n app-dev
kubectl rollout history deployment/<name> -n app-dev [--revision=N]
kubectl rollout undo deployment/<name> -n app-dev [--to-revision=N]
kubectl logs -n app-dev -l app=<label> --prefix --tail=20
kubectl exec -n app-dev deploy/<name> -- <cmd>
```

## Session 3 메모

### 배운 객체
- **ConfigMap**: 평문 설정 저장. 환경변수 or 파일로 Pod에 주입
- **Secret**: 민감 정보 저장. base64 인코딩 (암호화 아님). 실무엔 Secrets Manager/Vault

### 주입 패턴 3가지

**패턴 1 — 파일 마운트** (ConfigMap 키 → 컨테이너 내부 파일)
```yaml
volumes:
  - name: code
    configMap:
      name: auth-code
volumeMounts:
  - name: code
    mountPath: /app        # ConfigMap 키=파일명, 값=파일내용
```

**패턴 2 — 개별 env var** (Secret/ConfigMap 특정 키 하나만)
```yaml
env:
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: auth-secret
        key: jwt-secret
```

**패턴 3 — 일괄 env var** (ConfigMap 전체를 한 번에)
```yaml
envFrom:
  - configMapRef:
      name: api-config     # 모든 키-값이 env var로
```

### 이번 실습 구성
| 서비스 | ConfigMap | Secret |
|---|---|---|
| auth | 패턴1 (auth.py 코드 마운트) | 패턴2 (JWT_SECRET) |
| api | 패턴1 (api.py 코드 마운트) + 패턴3 (AUTH_URL, LOG_LEVEL) | 없음 |
| web | 패턴1 (nginx.conf 마운트) | 없음 |

### 핵심 메커니즘
- Secret base64는 편의성 분리, 암호화 아님 → 실무: AWS Secrets Manager, Vault, External Secrets Operator
- ConfigMap 파일 마운트: ConfigMap 키 = 파일명, 값 = 파일 내용
- `envFrom`은 ConfigMap 전체 주입 → 키 이름이 그대로 env var 이름이 됨
- 설정 변경 시 ConfigMap만 수정 후 Pod 재시작 → 이미지 재빌드 불필요

### 전체 흐름 테스트
```bash
$ TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
  -H "Content-Type: application/json" \
  -d '{"user":"alice"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")
$ curl -s "http://localhost:8080/api/data?token=$TOKEN"
# → {"data":"secret-data","for_user":"alice","log_level":"DEBUG"}
```

### 자주 쓴 명령
```powershell
kubectl get configmap -n app-dev
kubectl get secret -n app-dev
kubectl describe configmap <name> -n app-dev
kubectl exec -n app-dev deploy/<name> -- env | grep LOG_LEVEL
```

## Session 4 메모

## Session 5 메모
