# EKS 학습 플랜

> 대상: AWS 중급 / Kubernetes 초급
> 목표: EKS 이론 + 실습 완주
> 예상 기간: 6~8주 (주 10시간 기준)

---

## Phase 1: Kubernetes 기초 (1.5~2주)

EKS는 K8s 위에 AWS 통합을 얹은 것. K8s 자체를 모르면 EKS의 부가가치를 이해할 수 없음.

### 이론 체크리스트
- [ ] 컨테이너 vs VM, 오케스트레이터의 필요성
- [ ] K8s 아키텍처
  - [ ] Control Plane: API Server, etcd, Scheduler, Controller Manager
  - [ ] Data Plane: kubelet, kube-proxy, CRI(Container Runtime Interface)
- [ ] 핵심 오브젝트: Pod, ReplicaSet, Deployment, Service, ConfigMap, Secret, Namespace
- [ ] 워크로드 종류: Deployment, StatefulSet, DaemonSet, Job, CronJob
- [ ] 네트워킹: ClusterIP, NodePort, LoadBalancer, Ingress
- [ ] 스토리지: PV, PVC, StorageClass
- [ ] RBAC, ServiceAccount

### 실습 체크리스트 (로컬, 비용 0원)
- [ ] Docker Desktop / kind / minikube로 로컬 클러스터 구성
- [ ] kubectl 기본 명령 (get, describe, logs, exec, apply, delete)
- [ ] nginx Deployment + Service 배포
- [ ] ConfigMap / Secret 마운트, 환경변수 주입
- [ ] Liveness / Readiness probe 동작 실험
- [ ] Rolling update / Rollback
- [ ] Namespace 분리, RBAC 권한 부여 실험

### 추천 자료
- Kubernetes 공식 docs Tutorials
- "쿠버네티스 인 액션" 1~9장
- Katacoda / Killercoda 인터랙티브 실습

---

## Phase 2: EKS 핵심 개념 (1주)

이론 중심. AWS 공식 docs + 다이어그램 위주로 학습.

### 왜 EKS인가
- [ ] Self-managed K8s vs EKS vs ECS 비교
- [ ] EKS 책임 분담 모델 (AWS가 관리하는 부분 / 내가 관리하는 부분)
- [ ] EKS 가격 모델 (Control Plane $0.10/hr + 노드 비용)

### EKS 아키텍처
- [ ] EKS Control Plane (멀티 AZ, AWS 관리형)
- [ ] 노드 옵션 비교
  - [ ] Managed Node Groups
  - [ ] Self-Managed Nodes
  - [ ] Fargate (서버리스)
- [ ] VPC 통합과 AWS VPC CNI (Pod에 VPC IP 직접 할당)
- [ ] IAM 통합
  - [ ] IRSA (IAM Roles for Service Accounts)
  - [ ] EKS Pod Identity (신규)
- [ ] 인증/인가: aws-auth ConfigMap vs EKS Access Entries

### 필수 애드온
- [ ] 기본 애드온: VPC CNI, CoreDNS, kube-proxy
- [ ] AWS Load Balancer Controller
- [ ] EBS CSI Driver, EFS CSI Driver
- [ ] Cluster Autoscaler vs Karpenter

---

## Phase 3: EKS 첫 실습 (1주) — AWS 비용 발생 시작

⚠️ 비용 알림(Budget Alert) 설정 필수. 매일 끝나면 클러스터/노드그룹 삭제.

### 환경 준비
- [ ] AWS CLI v2 설치 및 프로필 설정
- [ ] eksctl 설치
- [ ] kubectl 설치
- [ ] helm 설치
- [ ] AWS Budget Alert ($30~50 임계값)

### 실습 단계
- [ ] eksctl로 클러스터 생성 → 동작 확인 → 삭제
- [ ] Terraform으로 같은 클러스터 재구성 (IaC 학습)
- [ ] 샘플 앱(2048 게임 등) 배포
- [ ] AWS Load Balancer Controller 설치 → ALB로 노출
- [ ] EBS CSI Driver로 PV 동적 프로비저닝
- [ ] IRSA 실습: Pod에서 S3 접근
- [ ] CloudWatch Container Insights 활성화

---

## Phase 4: 프로덕션 토픽 (1.5주)

### Observability
- [ ] CloudWatch Container Insights
- [ ] Prometheus + Grafana (kube-prometheus-stack)
- [ ] Fluent Bit으로 로그 → CloudWatch Logs

### Autoscaling
- [ ] HPA (Horizontal Pod Autoscaler)
- [ ] VPA (Vertical Pod Autoscaler)
- [ ] Karpenter로 노드 자동 스케일링

### Security
- [ ] Network Policy
- [ ] Pod Security Standards
- [ ] AWS Secrets Manager + External Secrets Operator
- [ ] 이미지 스캔: trivy, kubescape

### Networking 심화
- [ ] VPC CNI prefix delegation
- [ ] Security Group for Pods

### Upgrade
- [ ] K8s 버전 업그레이드 절차
- [ ] 노드 롤링 업데이트

---

## Phase 5: 응용 (1~2주, 선택)

- [ ] GitOps: ArgoCD 또는 Flux
- [ ] Service Mesh: Istio 맛보기
- [ ] CI/CD: GitHub Actions → ECR → EKS 배포
- [ ] 자격증 준비: CKA → AWS Certified Kubernetes Specialty

---

## 진행 기록

| Phase | 시작일 | 완료일 | 메모 |
|-------|--------|--------|------|
| 1     |        |        |      |
| 2     |        |        |      |
| 3     |        |        |      |
| 4     |        |        |      |
| 5     |        |        |      |
