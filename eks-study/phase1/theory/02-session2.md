# Session 2 이론 — Deployment / ReplicaSet

## Controller 패턴
Kubernetes의 거의 모든 동작은 Controller라는 무한 루프로 이루어진다.

- 사용자가 선언한 "원하는 상태(spec)"와 클러스터의 "현재 상태(status)"를 끊임없이 비교
- 차이가 있으면 차이를 메꾸는 동작을 수행
- 이 루프를 reconciliation loop라고 부름
- 자가치유(self-healing)는 별도의 기능이 아니라 이 루프의 자연스러운 결과
  - replicas=3인데 Pod이 1개로 줄면, Controller가 부족분을 감지해 2개를 더 생성
  - Pod이 죽어도 사람이 손대지 않아도 자동으로 복구되는 이유

## ReplicaSet
지정한 Pod 템플릿으로 정확히 N개의 Pod이 항상 존재하도록 보장하는 컨트롤러.

- spec에 Pod 템플릿, replicas 개수, selector 명시
- selector로 매칭되는 Pod 수가 부족하면 새로 생성, 많으면 삭제
- 실무에서 ReplicaSet을 직접 만드는 일은 거의 없음
  - Deployment가 자동으로 만들어주기 때문

## Deployment
ReplicaSet의 상위 추상이며, 실제로 사람이 작성하는 워크로드 객체.

- ReplicaSet의 "N개 유지" 기능에 다음 두 가지를 추가
  - 버전 관리 (revision history)
  - 무중단 배포 전략 (Rolling Update)
- Pod 템플릿이 바뀌면 새 ReplicaSet을 자동으로 생성
- 옛 ReplicaSet은 `replicas=0`으로 축소된 상태로 보존되어 즉시 롤백 가능
- 객체 계층은 다음과 같음

```
Deployment <name>
   └─ ReplicaSet <name>-<해시>      ← Pod 템플릿의 해시
         └─ Pod <name>-<해시>-<랜덤>
```

## 두 객체로 분리한 이유
단일 책임 원칙(Single Responsibility).

- Deployment의 책임: 버전 관리 + 배포 전략
- ReplicaSet의 책임: N개 유지
- 책임이 분리되어 있어 다른 워크로드 컨트롤러(StatefulSet 등)도 비슷한 패턴으로 자체 하위 메커니즘을 가짐

## Service와 Deployment의 느슨한 결합
Deployment를 학습할 때 가장 중요한 인사이트.

- Service는 Deployment의 존재를 모름
- Service는 라벨 셀렉터로 Pod만 잡을 뿐, 그 Pod이 어떤 컨트롤러에 의해 관리되는지는 신경 쓰지 않음
- 그 결과
  - 기존 Service를 그대로 두고 raw Pod을 Deployment로 교체해도, Service는 새 Pod을 자동으로 backend로 등록
  - 같은 라벨을 유지하는 한 Deployment를 통째로 지웠다 다시 만들어도 Service는 변경되지 않음
- 이것이 K8s의 핵심 디자인 원칙인 loose coupling의 실제 모습

## Rolling Update
기본 배포 전략. 트래픽이 끊기지 않도록 옛 Pod과 새 Pod을 점진적으로 교체.

- Pod 템플릿이 바뀌면 새 ReplicaSet이 만들어짐
- 옛 ReplicaSet의 Pod을 일부 죽이고, 새 ReplicaSet의 Pod을 그만큼 띄움
- 이 과정이 동시에 진행되어 항상 일정 수의 가용 Pod이 유지됨
- `spec.strategy`로 세부 조정 가능
  - `maxUnavailable`: 동시에 사용 불가능해도 되는 Pod 수
  - `maxSurge`: 일시적으로 추가로 띄울 수 있는 Pod 수
- `kubectl rollout status`로 진행 상황 추적, 도중에 문제 발견 시 즉시 중단/롤백 가능

## Rollback과 revision 관리
Deployment는 옛 ReplicaSet을 보존하기 때문에 롤백이 빠르다.

- `kubectl rollout history` 로 revision 목록 확인
- `kubectl rollout undo` 로 직전 revision으로 복귀
- `kubectl rollout undo --to-revision=N` 으로 특정 revision 지정
- 옛 ReplicaSet 보존 개수는 `spec.revisionHistoryLimit`로 조절 (기본 10)
- **동일한 Pod 템플릿은 중복 보관하지 않음**
  - 같은 템플릿이 다시 등장하면 옛 revision 번호는 사라지고 새 번호로 보존
  - history의 revision 번호에 구멍이 생기는 것이 정상

## change-cause annotation
변경 이유를 revision history에 기록하는 표준 방법.

- key: `kubernetes.io/change-cause`
- Deployment 객체의 annotation으로 저장됨
- 새 revision이 만들어질 때 그 시점의 annotation 값이 ReplicaSet에 복사되어 history에 표시
- annotation을 갱신하지 않은 채 apply하면 새 revision도 옛 사유와 동일한 값으로 기록됨
- 옛날에는 `kubectl apply --record` 플래그가 명령어를 자동으로 박아줬으나
  - K8s 1.22에서 deprecated, 1.27에서 제거
  - 지금은 사람이 명시적으로 관리해야 함
- 권장 패턴: yaml의 `metadata.annotations`에 change-cause를 함께 두기
  - 변경과 사유가 한 번의 apply로 같이 들어감
  - GitOps에서는 PR diff로 변경과 사유를 한눈에 검토 가능

## Label과 Annotation의 차이
둘 다 metadata에 들어가는 key-value지만 역할이 다름.

- **Label**
  - selector에 잡힘 → 객체들 사이의 결합에 사용 (Service↔Pod, Deployment↔Pod)
  - 짧고 범주형(`app=auth`, `tier=backend` 같은 식)이 일반적
- **Annotation**
  - selector에 안 잡힘 → 순수 메타데이터
  - 길거나 구조화된 정보 가능 (change-cause 메시지, ArgoCD sync-wave, AWS LB Controller 옵션 등)

## 스케일링 — 명령형 vs 선언형
같은 결과를 만드는 두 가지 방식이 있고, 각각 쓰임새가 다름.

- 명령형: `kubectl scale deployment/<name> --replicas=N`
  - 빠른 실험에 유용
  - 단점: yaml과 클러스터 상태가 어긋남(드리프트). GitOps 환경에서는 다음 sync 때 원복됨
- 선언형: yaml의 `spec.replicas` 수정 후 `kubectl apply`
  - 실무 표준
  - yaml이 단일 진실 공급원(source of truth)이 되어 GitOps와 호환

## spec과 실제 동작의 분리
컨테이너의 선언된 설정(args, env, volume 등)과 실제 동작(HTTP 응답 등)은 별개다.

- spec 검증: `kubectl get/describe`
- 동작 검증: 실제 호출(`wget`, `curl`, port-forward 등)
- 예를 들어 `kubectl exec ... -- wget -qO- http://auth`는 args를 직접 읽는 게 아니라
  - 클러스터 안에서 HTTP 요청을 보내고
  - 응답 본문을 출력하는 것일 뿐
  - 마침 http-echo가 args의 -text 값을 그대로 응답으로 돌려주는 단순 서버라서, 결과적으로 응답 본문이 args와 일치해 보일 뿐
- 진짜 앱(Flask, Spring 등)에서는 spec(env로 DB_URL 주입)과 동작(쿼리 결과)이 더 분명하게 분리됨

## kubectl 단축 패턴 모음
이번 세션에서 새로 익힌 편의 문법.

- `deploy/<name>`: 그 Deployment의 Pod 중 아무거나 1개 자동 선택
  - `kubectl exec ... deploy/web -- ...` 처럼 쓸 때 Pod 이름을 외울 필요 없음
- `-l <label>`: 라벨 셀렉터로 여러 객체를 한 번에 잡기
  - `kubectl delete pod -l app=auth` 식으로 묶음 처리
- `--prefix`: `kubectl logs` 출력에 `[pod/<이름>]` 접두어 표시
  - 라벨 셀렉터로 여러 Pod의 로그를 함께 볼 때 어느 Pod이 출력했는지 식별 가능
- `-w`: watch 모드. STATUS 변화를 실시간으로 출력 (Ctrl+C로 종료)
