# note-app — K8s 학습용 데모 앱

메모(note)를 생성·조회·삭제하는 REST API.
Sessions 1~5에 걸쳐 점진적으로 K8s 기능이 추가됨.

## 아키텍처

```
web (nginx:alpine)   ← NodePort :30080
  │  /api/ → proxy_pass
  ▼
api (note-api:v1)    ← ClusterIP :80→8080
  │  notes.json
  ▼
/tmp (Sessions 1~3)  →  PVC api-data (Session 4~)
```

## API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET | /notes | 전체 노트 조회 |
| POST | /notes | 노트 생성 `{"text": "..."}` |
| DELETE | /notes/{id} | 노트 삭제 |
| GET | /health | 헬스체크 (버전 포함) |

## 이미지 빌드 (최초 1회)

```powershell
$ docker build -t note-api:v1 ./api
$ docker build --build-arg VERSION=v2 -t note-api:v2 ./api
```

Docker Desktop K8s는 로컬 이미지를 직접 사용함 (`imagePullPolicy: Never`).

## 세션별 적용 순서

### Session 1 — Namespace, Pod, Service
```powershell
$ kubectl apply -f manifests/01-basics/
$ kubectl get all -n note-app
$ kubectl port-forward -n note-app svc/api 8080:80
# 새 터미널:
$ curl http://localhost:8080/notes
$ curl -X POST http://localhost:8080/notes -H "Content-Type: application/json" -d '{"text":"첫 번째 노트"}'
```

### Session 2 — Deployment, ReplicaSet
```powershell
$ kubectl apply -f manifests/02-deployment/
# Rolling update: image v1 → v2
# 01-deploy-api.yaml 의 image 를 note-api:v2 로 수정 후:
$ kubectl apply -f manifests/02-deployment/01-deploy-api.yaml
$ kubectl rollout status deployment/api -n note-app
$ curl http://localhost:8080/health   # version: v2 확인
```

### Session 3 — ConfigMap, Secret
```powershell
$ kubectl apply -f manifests/03-config/
$ kubectl exec -n note-app deploy/api -- env | grep -E "DATA_DIR|LOG_LEVEL|API_KEY"
```

### Session 4 — PV, PVC
```powershell
$ kubectl apply -f manifests/04-storage/
# 노트 생성 후 Pod 삭제 → 재생성 후 데이터 유지 확인
$ curl -X POST http://localhost:8080/api/notes -H "Content-Type: application/json" -d '{"text":"PVC 테스트"}'
$ kubectl delete pod -n note-app -l app=api
$ curl http://localhost:8080/api/notes   # 데이터 유지 확인
```

### Session 5 — Job, CronJob, DaemonSet
```powershell
# Job: 초기 데이터 시드 (1회 실행)
$ kubectl apply -f manifests/05-jobs/01-cm-seed.yaml
$ kubectl apply -f manifests/05-jobs/02-job-seed.yaml
$ kubectl logs -n note-app job/seed

# CronJob: 1분마다 5분 이상 된 노트 삭제
$ kubectl apply -f manifests/05-jobs/03-cm-cleanup.yaml
$ kubectl apply -f manifests/05-jobs/04-cronjob-cleanup.yaml
$ kubectl get cronjob -n note-app

# DaemonSet: 노드당 1개 log-agent Pod
$ kubectl apply -f manifests/05-jobs/05-daemonset-log.yaml
$ kubectl logs -n note-app -l app=log-agent
```

## 정리

```powershell
$ kubectl delete namespace note-app
```
