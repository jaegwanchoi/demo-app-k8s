# Session 3 이론 — ConfigMap / Secret

## 설정과 이미지를 분리하는 이유
Session 2까지의 Deployment는 설정값이 이미지 안에 하드코딩되어 있었다.

- DB 호스트, API 엔드포인트 같이 환경마다 달라야 하는 값을 바꾸려면 이미지를 새로 빌드해야 함
- 비밀번호, API 키 같은 민감 정보를 이미지에 넣으면 이미지를 볼 수 있는 사람이 모두 읽을 수 있음
- K8s의 해법: 설정과 이미지를 별도 객체로 분리해 런타임에 주입

## ConfigMap
평문 설정을 저장하는 객체.

- 환경변수, 설정 파일, 명령줄 인수 등 민감하지 않은 값을 담음
- 저장 형식: key-value 쌍
- Pod이 참조하면 런타임에 주입됨 → 이미지 재빌드 없이 설정 변경 가능
- 이번 실습에서 쓴 ConfigMap 세 가지
  - `auth-code`: auth.py 파이썬 코드를 파일로 마운트
  - `api-code`: api.py 파이썬 코드를 파일로 마운트
  - `api-config`: AUTH_URL, LOG_LEVEL을 환경변수로 일괄 주입
  - `web-nginx`: nginx.conf를 파일로 마운트

## Secret
민감 정보를 저장하는 객체.

- ConfigMap과 구조가 동일하지만 값이 base64 인코딩되어 저장됨
- **base64는 암호화가 아님** — 누구나 decode 가능. 인코딩은 바이너리 데이터를 텍스트로 안전하게 전송하기 위한 규격
- K8s 기본 Secret의 실제 보안 수준
  - etcd에 base64로 저장됨 (etcd 접근 권한이 있으면 읽을 수 있음)
  - `kubectl get secret -o yaml` 로 base64 값이 노출됨
  - RBAC으로 접근 제한하는 것이 1차 방어선
- 실무 Secret 관리: AWS Secrets Manager, HashiCorp Vault, External Secrets Operator
  - 이 도구들은 Secret 값을 외부 저장소에 두고 K8s Secret에는 참조만 두는 방식

## 주입 패턴 3가지

### 패턴 1 — 파일 마운트
ConfigMap의 키-값을 컨테이너 내부 파일로 마운트.

```yaml
volumes:
  - name: code
    configMap:
      name: auth-code      # ConfigMap 이름
volumeMounts:
  - name: code
    mountPath: /app        # 컨테이너 내부 경로
```

- ConfigMap의 키 = 파일명, 값 = 파일 내용
- `auth-code`의 키 `auth.py`가 컨테이너 내부 `/app/auth.py`로 생성됨
- 이번 실습: auth.py, api.py, nginx.conf를 이미지 빌드 없이 컨테이너에 주입

### 패턴 2 — 개별 env var
Secret 또는 ConfigMap의 특정 키 하나를 환경변수 하나로 주입.

```yaml
env:
  - name: JWT_SECRET           # 컨테이너 내부 환경변수 이름
    valueFrom:
      secretKeyRef:
        name: auth-secret      # Secret 이름
        key: jwt-secret        # Secret 내 키 이름
```

- `configMapKeyRef`로 바꾸면 ConfigMap에서도 동일하게 사용
- 민감 정보는 필요한 키 하나만 골라 주입 → 불필요한 Secret 전체가 env에 노출되지 않음
- 이번 실습: `auth-secret`의 `jwt-secret` → auth Pod의 `JWT_SECRET`

### 패턴 3 — 일괄 env var
ConfigMap 전체를 한 번에 환경변수로 주입.

```yaml
envFrom:
  - configMapRef:
      name: api-config         # ConfigMap 전체가 env var로
```

- ConfigMap의 모든 키-값이 그대로 환경변수가 됨
- `api-config`의 `AUTH_URL`, `LOG_LEVEL`이 api Pod에 한 번에 주입됨
- 설정 항목이 많을 때 하나씩 나열하는 패턴 2보다 간결

## 패턴 선택 기준
| 상황 | 권장 패턴 |
|---|---|
| 설정 파일(conf, yaml, 코드 등)을 넣어야 함 | 패턴 1 (파일 마운트) |
| 민감 정보를 env var로 주입 | 패턴 2 (개별 env var) |
| 비민감 설정을 여러 개 한 번에 주입 | 패턴 3 (일괄 envFrom) |

## 이번 실습의 전체 흐름
web(nginx) → auth(Flask) → JWT 발급 → api(Flask) → auth 검증 → 데이터 반환

- web은 ConfigMap으로 nginx.conf를 마운트 → `/auth/`, `/api/` 경로를 각 서비스로 reverse proxy
- auth는 ConfigMap으로 auth.py를 마운트, Secret으로 JWT_SECRET 주입 → JWT 발급/검증
- api는 ConfigMap으로 api.py를 마운트, envFrom으로 AUTH_URL/LOG_LEVEL 주입 → auth 서버 호출

## ConfigMap 수정 후 반영 방법
ConfigMap을 수정해도 실행 중인 Pod에 자동 반영되지 않는다.

- 환경변수(`env`, `envFrom`)로 주입한 경우: Pod 재시작 필요
- 파일 마운트(`volume`)로 주입한 경우: kubelet이 주기적으로 갱신 (기본 약 1분), 앱이 파일 변경을 감지해야 반영됨
- 가장 확실한 방법: `kubectl rollout restart deployment/<name>`

## 자주 쓴 명령
```powershell
kubectl get configmap -n app-dev
kubectl get secret -n app-dev
kubectl describe configmap <name> -n app-dev
kubectl exec -n app-dev deploy/<name> -- env | grep LOG_LEVEL
```
