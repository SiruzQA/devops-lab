# devops-lab
DevOps lab to learn K3s, Docker, Pods, Services, and Ingress. Minimal setup to practice deployment, scaling, rolling updates, and probes.

Yüklə: sudo apt install -y curl ca-certificates gnupg lsb-release

sudo apt install -y docker.io
sudo systemctl enable docker -- now
Yoxla docker --version
K3s docker istifade etmir,ancag image build etmek ucun Docker lazimdir

curl -sfL https://get.k3s.io | sh -


- **Dockerfile** – Tətbiqin Docker image-i necə build olunur  
- **index.html** – Sadə frontend nümunəsi  
- **deployment.yaml** – Pod və containerlərin k3s cluster-də necə yaradılacağını göstərir  
- **service.yaml** – Pod-lara daxil olmaq üçün servis yaratmaq  
- **ingress.yaml** – Xaricdən trafik routinqi (domain / host əsasında)

1. Docker image build et:  
   ```bash
   docker build -t myapp:latest .

Deployment və servis tətbiq et:
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

Pod və servislərə bax:
kubectl get pods,svc,ingress

Pod loglarına baxmaq üçün:
kubectl logs <pod_name>