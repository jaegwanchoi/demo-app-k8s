# note-app 사전 준비 가이드

Sessions 1~5 실습 전에 한 번만 진행하면 됩니다.

---

## 전제 조건

- Docker Desktop (Kubernetes 활성화)
- kubectl

```powershell
$ kubectl config current-context
# docker-desktop 이어야 함
```

---

## 1. 리포지토리 클론

```powershell
$ git clone <repo-url>
$ cd eks-study
```

---

## 2. 이미지 빌드

Docker Desktop K8s는 로컬 이미지를 직접 사용합니다. 레지스트리 푸시 불필요.

```powershell
$ docker build -t note-api:v1 ./note-app/api
$ docker build --build-arg VERSION=v2 -t note-api:v2 ./note-app/api
```

확인:

```powershell
$ docker images note-api
```

---

## 3. 기존 환경 초기화 (재시작 시)

```powershell
$ kubectl delete namespace note-app
```

Namespace 삭제 시 하위 모든 리소스(Pod, Service, ConfigMap, PVC 등)가 함께 삭제됩니다.

---

## 4. 세션별 적용 명령 요약

| Session | 주제 | 명령 |
|---|---|---|
| 1 | Namespace, Pod, Service | `kubectl apply -f note-app/manifests/01-basics/` |
| 2 | Deployment, ReplicaSet | `kubectl apply -f note-app/manifests/02-deployment/` |
| 3 | ConfigMap, Secret | `kubectl apply -f note-app/manifests/03-config/` |
| 4 | PV, PVC | `kubectl apply -f note-app/manifests/04-storage/` |
| 5 | Job, CronJob, DaemonSet | 파일별 순서대로 적용 (05-jobs/ 참고) |

각 Session은 이전 Session 위에 덮어씁니다. Namespace를 초기화할 필요 없이 순서대로 진행합니다.

---

## 5. 상태 확인 명령

```powershell
$ kubectl get all -n note-app
```

---

## 6. API 테스트 방법

```powershell
# 포트 포워딩 (별도 터미널 유지)
$ kubectl port-forward -n note-app svc/web 8080:80

# 노트 생성
$ curl -X POST http://localhost:8080/api/notes \
  -H "Content-Type: application/json" \
  -d '{"text":"첫 번째 노트"}'

# 노트 조회
$ curl http://localhost:8080/api/notes

# 헬스체크 (버전 확인)
$ curl http://localhost:8080/api/health
```
