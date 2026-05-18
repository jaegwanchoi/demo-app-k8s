# note-app — K8s 실습 가이드

메모(note)를 생성·조회·삭제하는 REST API로 K8s 핵심 오브젝트를 순서대로 실습합니다.

## 앱 아키텍처

```
web (nginx:alpine)   NodePort :30080
  │  /api/ → proxy_pass        (Session 3부터 활성화)
  ▼
api (python:3-slim)  ClusterIP :80 → 8080
  │  notes.json
  ▼
/tmp                 (Session 1~3)
PVC api-data         (Session 4~)
```

## API 엔드포인트

| Method | Path | 설명 |
|---|---|---|
| GET | /notes | 전체 노트 조회 |
| POST | /notes | 노트 생성 `{"text": "..."}` |
| DELETE | /notes/{id} | 노트 삭제 |
| GET | /health | 헬스체크 + 버전 확인 |

---

## 사전 준비 (최초 1회)

```powershell
# context 확인
$ kubectl config current-context
# docker-desktop

# 실습 디렉토리 이동
$ cd eks-study
```

---

## Session 1 — Namespace, Pod, Service

**학습 목표**: K8s 최소 실행 단위(Pod)와 네트워크 추상화(Service)를 이해한다.

### 적용

```powershell
$ kubectl apply -f note-app/manifests/01-basics/
```

### 확인

```powershell
$ kubectl get all -n note-app
$ kubectl describe pod api -n note-app
```

### API 테스트

```powershell
# 포트 포워딩 (터미널 유지)
$ kubectl port-forward -n note-app svc/api 8080:80

# 새 터미널
$ curl http://localhost:8080/health
# {"status":"ok","version":"v1"}

$ curl -X POST http://localhost:8080/notes `
    -H "Content-Type: application/json" `
    -d '{"text":"첫 번째 노트"}'
# {"created":..., "id":"...", "text":"첫 번째 노트"}

$ curl http://localhost:8080/notes
# [{"created":..., "id":"...", "text":"첫 번째 노트"}]
```

### 핵심 확인 포인트

```powershell
# Service가 Pod을 어떻게 찾는지 확인 (라벨 셀렉터 → Endpoints)
$ kubectl get endpointslices -n note-app

# Pod IP와 Service IP 비교
$ kubectl get pod api -n note-app -o wide
$ kubectl get svc api -n note-app
```

---

## Session 2 — Deployment, ReplicaSet

**학습 목표**: Controller 패턴(reconciliation loop)과 무중단 배포(Rolling Update)를 이해한다.

### 적용

```powershell
$ kubectl apply -f note-app/manifests/02-deployment/
```

### 확인

```powershell
$ kubectl get deployment -n note-app
$ kubectl get replicaset -n note-app
$ kubectl get pods -n note-app
```

### 스케일링

```powershell
# api를 3개로 늘리기
$ kubectl scale deployment/api -n note-app --replicas=3
$ kubectl get pods -n note-app -w
```

### Rolling Update (v1 → v2)

```powershell
$ kubectl apply -f note-app/manifests/02-deployment/rollout/01-deploy-api-v2.yaml
$ kubectl rollout status deployment/api -n note-app

# 새 버전 확인
$ curl http://localhost:8080/health
# {"status":"ok","version":"v2"}

# revision 이력 확인
$ kubectl rollout history deployment/api -n note-app
```

### Rollback

```powershell
$ kubectl rollout undo deployment/api -n note-app
$ curl http://localhost:8080/health
# {"status":"ok","version":"v1"}
```

---

## Session 3 — ConfigMap, Secret

**학습 목표**: 설정과 이미지를 분리하는 3가지 주입 패턴을 이해한다.

### 적용

```powershell
$ kubectl apply -f note-app/manifests/03-config/
```

### 확인

```powershell
$ kubectl get configmap -n note-app
$ kubectl get secret -n note-app

# ConfigMap(envFrom) 주입 확인
$ kubectl exec -n note-app deploy/api -- env | grep -E "DATA_DIR|LOG_LEVEL"

# Secret 주입 확인
$ kubectl exec -n note-app deploy/api -- env | grep API_KEY
```

### web → api reverse proxy 테스트

Session 3부터 nginx가 `/api/` 경로를 api 서비스로 프록시합니다.

```powershell
# 기존 api 포트 포워딩 종료 후 web으로 변경
$ kubectl port-forward -n note-app svc/web 8080:80

# 새 터미널
$ curl http://localhost:8080/api/health
# {"status":"ok","version":"v1"}

$ curl -X POST http://localhost:8080/api/notes `
    -H "Content-Type: application/json" `
    -d '{"text":"ConfigMap 실습"}'

$ curl http://localhost:8080/api/notes
```

---

## Session 4 — PV, PVC

**학습 목표**: Pod이 재시작되어도 데이터가 유지되는 영구 볼륨을 이해한다.

### 적용

```powershell
$ kubectl apply -f note-app/manifests/04-storage/
$ kubectl get pvc -n note-app
```

### 데이터 영구성 검증

```powershell
# 1. 노트 생성
$ curl -X POST http://localhost:8080/api/notes `
    -H "Content-Type: application/json" `
    -d '{"text":"PVC 테스트 - Pod 재시작 후에도 유지되어야 함"}'

# 2. Pod 강제 삭제 (Deployment가 자동으로 재생성)
$ kubectl delete pod -n note-app -l app=api
$ kubectl get pods -n note-app -w

# 3. 재생성된 Pod에서 데이터 확인
$ curl http://localhost:8080/api/notes
# PVC 없을 때: [] (데이터 소실)
# PVC 있을 때: 노트 유지
```

### 볼륨 마운트 확인

```powershell
$ kubectl describe pod -n note-app -l app=api
# Volumes 섹션에서 api-data PVC 마운트 확인

$ kubectl exec -n note-app deploy/api -- ls /data
# notes.json
```

---

## Session 5 — Job, CronJob, DaemonSet

**학습 목표**: 일회성 작업(Job), 주기적 작업(CronJob), 노드 레벨 에이전트(DaemonSet)를 이해한다.

### Job — 초기 데이터 시드 (1회 실행)

```powershell
$ kubectl apply -f note-app/manifests/05-jobs/01-cm-seed.yaml
$ kubectl apply -f note-app/manifests/05-jobs/02-job-seed.yaml

# Job 완료 상태 확인 (COMPLETIONS: 1/1)
$ kubectl get job -n note-app

# 실행 로그 확인
$ kubectl logs -n note-app job/seed

# 생성된 노트 확인
$ curl http://localhost:8080/api/notes
```

### CronJob — 오래된 노트 정리 (1분마다)

```powershell
$ kubectl apply -f note-app/manifests/05-jobs/03-cm-cleanup.yaml
$ kubectl apply -f note-app/manifests/05-jobs/04-cronjob-cleanup.yaml

$ kubectl get cronjob -n note-app

# 1분 대기 후 Job 자동 생성 확인
$ kubectl get job -n note-app -w

# cleanup 로그 확인
$ kubectl logs -n note-app -l job-name -c cleanup
```

### DaemonSet — 노드당 1개 log-agent

```powershell
$ kubectl apply -f note-app/manifests/05-jobs/05-daemonset-log.yaml

# Docker Desktop은 노드 1개 → Pod 1개
$ kubectl get daemonset -n note-app
$ kubectl get pods -n note-app -l app=log-agent

# 로그 확인 (노드 이름 + 타임스탬프 출력)
$ kubectl logs -n note-app -l app=log-agent
```

---

## 전체 정리

```powershell
$ kubectl delete namespace note-app
```
