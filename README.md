# DevOps Lab: K3s + Docker + Pods + Services + Ingress

Bu labın məqsədi K3s cluster, Docker, Pods, Services və Ingress ilə minimal setup quraraq deployment, scaling, rolling updates və probes praktikası aparmaqdır. QA perspektivindən real sistemin arxasında nə baş verdiyini başa düşmək üçün nəzərdə tutulub. 

Sistemdə lazım olan paketləri yüklə: sudo apt install -y curl ca-certificates gnupg lsb-release.
 Docker quraşdır və aktiv et (Docker yalnız image build üçün lazımdır, K3s özü containerd istifadə edir): sudo apt install -y docker.io; sudo systemctl enable docker --now; docker --version. K3s quraşdır: curl -sfL https://get.k3s.io | sh -.

Repo daxilində aşağıdakı fayllar var: Dockerfile – tətbiqin Docker image-i necə build olunur, index.html – sadə frontend nümunəsi, deployment.yaml – pod və containerlərin K3s cluster-də necə yaradılacağını göstərir, service.yaml – pod-lara daxil olmaq üçün servis yaratmaq, ingress.yaml – xaricdən trafik routinqi (domain / host əsasında). 
Docker image build et: docker build -t myapp:latest .. 
Deployment və servis tətbiq et: kubectl apply -f deployment.yaml; kubectl apply -f service.yaml; kubectl apply -f ingress.yaml.
 Pod və servislərə bax: kubectl get pods,svc,ingress.
 Pod loglarına baxmaq üçün: kubectl logs <pod_name>.

Bu lab vasitəsilə öyrənmək olar: Containerization – Docker image build və run, Deployment workflow – kodun cluster-də necə işlədiyini başa düşmək, Platform behavior – pod, service və ingress routinqi, Observability – pod logları və sistem davranışını izləmək.

Qeyd: Docker yalnız image build üçün istifadə olunur, K3s özü containerd istifadə edir. Bu lab real CI/CD workflow-u göstərmir, amma manual deployment və platform proseslərini öyrənmək üçün nəzərdə tutulub.