# Session 1 이론 — Namespace / Pod / Service

## 컨테이너 오케스트레이션이란?
컨테이너 수십~수백 개를 사람이 손으로 관리할 수 없으니 자동화하는 시스템.

- 컨테이너 1~2개는 `docker run`으로 충분, 그러나 실서비스는 다름
- 자동화가 필요한 대표 작업
  - 죽은 컨테이너 자동 재시작, 트래픽 변동에 따른 자동 증감
  - 무중단 배포 / 롤백
  - 서비스 간 통신과 로드밸런싱
  - 설정·시크릿 관리, 노드 장애 시 다른 노드로 재배치
- Kubernetes(K8s)가 사실상의 표준 오케스트레이터

---

## Kubernetes 아키텍처
Control Plane(두뇌)과 Data Plane(워커 노드)으로 나뉘는 클러스터 구조.

- **Control Plane** — 클러스터 상태 관리
  - **API Server**: 모든 요청의 진입점. kubectl도 여기로 통신
  - **etcd**: 클러스터 상태 저장 key-value DB
  - **Scheduler**: 새 Pod을 어느 노드에 배치할지 결정
  - **Controller Manager**: 원하는 상태와 현재 상태를 끊임없이 비교·조정
- **Data Plane (Worker Node)** — 실제 컨테이너 실행
  - **kubelet**: 노드 위 Pod의 생애주기 관리(컨테이너 띄우고 죽임)
  - **kube-proxy**: 노드의 네트워크 규칙(iptables/IPVS) 관리
  - **CRI(Container Runtime)**: containerd 같은 실제 컨테이너 런타임
- K8s의 Control Plane도 Pod으로 동작 (self-hosted). EKS는 이 부분을 AWS가 별도 인프라에서 운영해 주는 것

---

## K8s 매니페스트의 4대 구조
모든 K8s 객체 YAML이 공유하는 4개 필드.

- **apiVersion**: 객체가 속한 API 그룹/버전 (예: `v1`, `apps/v1`)
- **kind**: 객체 종류 (Pod, Service, Deployment 등)
- **metadata**: 식별 정보 — 이름, 네임스페이스, 라벨, 어노테이션
- **spec**: "원하는 상태(desired state)" — Controller가 이 상태로 만들고 유지함

→ Pod든 Service든 ConfigMap이든 전부 이 4구조를 따른다.

---

## 선언형(Declarative) vs 명령형(Imperative)
K8s의 핵심 철학은 선언형. 실무에서는 `kubectl apply`만 쓴다.

- **명령형**: `kubectl create`, `kubectl run` — "이걸 지금 만들어라"
  - 같은 명령을 두 번 치면 에러 (이미 있음)
- **선언형**: `kubectl apply -f file.yaml` — "이 상태가 되어 있어야 해"
  - 몇 번을 쳐도 결과가 같음 (idempotent)
  - 이미 있으면 변경분만 반영, 없으면 생성
- Controller가 "선언된 상태"를 끊임없이 현재 상태와 비교하며 맞춰감 → **reconciliation loop**

---

## Namespace
물리적 클러스터 1개를 논리적으로 분리하는 가상 공간. 회사로 치면 부서 같은 개념.

- 같은 이름의 리소스를 서로 다른 Namespace에 동시에 생성 가능
- RBAC, ResourceQuota, NetworkPolicy 등을 Namespace 단위로 적용 가능
- 리소스를 한 번에 정리하기 쉬움 (Namespace 삭제 → 내부 리소스 전체 삭제)
- 기본 Namespace는 `default`
- 시스템 Namespace는 절대 삭제 금지
  - `default`, `kube-system`, `kube-node-lease`, `kube-public` — K8s가 부팅 시 자동 생성
  - 환경별 추가본(예: Docker Desktop의 `local-path-storage`)도 시스템이 의존

---

## Pod
컨테이너 1개 이상을 묶은 K8s의 최소 배포 단위.

- Pod 안의 컨테이너는 **같은 IP, 같은 네트워크 네임스페이스** 공유 → 서로 `localhost`로 통신
- 같은 Pod = 같은 노드에 항상 함께 스케줄됨
- Pod IP는 CNI 플러그인(Docker Desktop은 kindnet)이 할당, 대역 예: `10.244.x.x`
- **Pod은 mortal(필멸)**: 죽으면 새 Pod이 새 IP로 뜸 → 코드에 IP를 박으면 안 됨
- Raw Pod(Pod 객체 단독)은 **자가 치유가 없음** — 삭제하면 그대로 사라짐
  - 그래서 실무에선 Pod을 직접 만들지 않고 Deployment 같은 컨트롤러로 만듦

---

## Service
Pod 묶음 앞에 놓는 안정적인 가상 IP/DNS. 마이크로서비스 통신의 뼈대.

- Pod IP는 변하지만 Service IP(ClusterIP)는 고정
- Service IP 대역은 Pod IP 대역과 다름 (예: Service `10.96.x.x`, Pod `10.244.x.x`)
- Service IP는 **가상 IP** — 실제 인터페이스에 붙어있지 않음
  - kube-proxy가 노드의 iptables/IPVS 규칙으로 "이 IP로 가는 패킷 → 실제 Pod IP로 DNAT" 처리
  - 그래서 ping이 안 되는 경우도 흔함
- Service의 종류
  - **ClusterIP** (기본): 클러스터 내부 전용 → 마이크로서비스 간 통신
  - **NodePort**: 모든 노드의 30000–32767 포트로 외부 노출
  - **LoadBalancer**: 클라우드 LB 자동 생성 (EKS에선 ALB/NLB와 연결)
  - **ExternalName**: 외부 도메인의 CNAME 별칭 역할
- 포트가 두 종류
  - `port`: Service IP가 listen하는 포트 (클라이언트가 호출하는 쪽)
  - `targetPort`: 실제 Pod 컨테이너의 포트
  - `nodePort`: NodePort 타입에서만 — 노드 IP의 외부 포트
  - 이 분리 덕분에 Service가 **포트 매퍼** 역할도 함

---

## 라벨(Label)과 셀렉터(Selector)
K8s 객체 간 결합을 라벨로 풀어내는 패턴. 매우 중요.

- **라벨**: `metadata.labels`에 적는 key=value 메타데이터 (예: `app=auth`)
- **셀렉터**: 다른 객체가 "이 라벨을 가진 것들 다 잡아줘"라고 선언
- Service가 어떤 Pod을 backend로 묶을지 지정할 때 **selector**로 잡음
  - Service는 Pod을 직접 가리키지 않고, 라벨로 간접 매칭
  - 셀렉터에 매칭되는 Pod들이 자동으로 backend(Endpoints)로 등록됨
- 같은 패턴이 Deployment의 ReplicaSet 관리, NetworkPolicy의 적용 대상 지정 등 곳곳에 나옴

---

## Endpoints / EndpointSlice
Service의 selector로 매칭된 실제 Pod IP 목록을 담는 객체. 자동 생성됨.

- 관계: `Service → Endpoints/EndpointSlice → 실제 Pod IP들`
- Service가 만들어지면 K8s가 같은 이름의 Endpoints를 자동 생성
- Pod이 새로 뜨거나 죽을 때마다 Endpoints가 자동 갱신됨 → 그래서 클라이언트가 Service 이름만 알면 됨
- **Endpoints v1 → EndpointSlice 전환 중**
  - K8s 1.33+ 부터 `Endpoints`는 deprecated
  - EndpointSlice는 Service당 여러 조각으로 분할 → 백엔드 Pod 수천 개 규모에서 성능 차이가 큼
- 디버깅 시 `kubectl get endpointslices -n <ns>` 로 라벨 매칭이 제대로 됐는지 확인하는 것이 중요
  - Endpoints가 비어 있으면(`<none>`) selector가 어떤 Pod도 못 잡고 있다는 뜻

---

## CoreDNS와 서비스 디스커버리
클러스터 내부 DNS. Service 이름을 ClusterIP로 풀어준다.

- `kube-system` 네임스페이스의 CoreDNS Pod이 클러스터 DNS 역할
- 모든 Pod의 `/etc/resolv.conf`에 CoreDNS IP가 nameserver로 설정됨 (예: `10.96.0.10`)
- DNS 이름 규칙: `<service>.<namespace>.svc.cluster.local`
  - 같은 namespace의 Service는 짧게 `<service>` 만 써도 통함
  - 다른 namespace는 `<service>.<namespace>` 형태 필요
- 짧은 이름이 통하는 이유는 search domain 덕분
  - `/etc/resolv.conf`의 `search`에 `<ns>.svc.cluster.local`, `svc.cluster.local`, `cluster.local` 등이 깔려 있어 후보를 차례로 시도
  - 처음 몇 번의 NXDOMAIN은 정상 동작

---

## 트러블슈팅 일반 패턴
대부분의 문제는 두 명령으로 풀린다.

- 1단계 — `kubectl describe <object>`
  - 출력 맨 아래 `Events:` 섹션이 90%의 답
  - `ImagePullBackOff`, `CrashLoopBackOff`, `FailedScheduling` 등 키워드로 원인 카테고리 좁히기
- 2단계 — `kubectl logs <pod>`
  - 컨테이너 안 앱이 뱉은 stderr/stdout
  - `-p` 플래그로 직전(crash 전) 컨테이너 로그도 볼 수 있음
- 3단계 — 가장 작은 외부 검증으로 K8s 문제 vs 환경 문제 분리
  - 예: 이미지 풀 실패 → `docker pull`로 네트워크/레지스트리 직접 확인
- "Connection refused" vs "Timeout"의 의미 차이도 디버깅 단서
  - **Refused**: Service IP 자체는 살아있지만 backend Pod이 0개 → kube-proxy가 즉시 끊음
  - **Timeout**: 네트워크 경로(NetworkPolicy, 방화벽, DNS 등)에서 막힘

---

## 환경 함정 메모
Windows + Docker Desktop 환경에서 자주 부딪히는 것들.

- **Git Bash의 path 자동 변환**
  - `kubectl exec ... -- /bin/sh` 호출 시 Git Bash가 `/bin/sh`를 `C:/Program Files/Git/usr/bin/sh`로 바꿔 컨테이너에 넘김 → 실패
  - 회피: PowerShell에서 실행하거나, `//bin/sh`로 슬래시 두 번, 또는 `MSYS_NO_PATHCONV=1`
- **Docker Desktop Kubernetes는 kind 기반**
  - 노드가 Docker 컨테이너 안에 있어, NodePort가 호스트 localhost로 자동 매핑되지 않음
  - 외부 접근은 `kubectl port-forward`로 우회 (실무 디버깅의 표준 도구이기도 함)
- **이미지 풀 일시적 실패**
  - `short read: ... unexpected EOF` 형태 — Docker Hub 연결 끊김 또는 rate limit (anonymous는 IP당 6시간에 100회)
  - 해결: `docker pull`로 캐시 워밍 후 Pod 재생성, 또는 잠시 후 재시도
