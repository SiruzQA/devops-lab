
K3s Platform QA Testing Guide
Bu layihə K3s üzərində çalışan tətbiqlər üçün platform səviyyəli QA testlərinin necə aparıldığını göstərir. Məqsəd real deploy-dan sonra sistemin davranışını yoxlamaq, routing və health check-ləri doğrulamaq və CI/CD axınında avtomatik test dəstəyi təmin etməkdir.

## Test Coverage

### 1. Health Check Tests
- ✅ K3s servisinin işlək olması
- ✅ Pod-ların Ready state-də olması  
- ✅ Liveness probe konfiqurasiyası
- ✅ Readiness probe konfiqurasiyası
- ✅ Startup probe konfiqurasiyası
- ✅ Service endpoint-lərin aktiv olması

### 2. Ingress Routing Tests
- ✅ Ingress resource-ların mövcudluğu
- ✅ Routing qaydalarının düzgünlüyü
- ✅ Backend service-lərin mövcudluğu
- ✅ HTTP connectivity testləri
- ✅ Host-based routing yoxlanması

### 3. Platform Stability Tests
- ✅ Horizontal pod scaling
- ✅ Rolling update ssenariləri
- ✅ Resource limit testləri
- ✅ Pod restart davranışı

## İstifadə Qaydası

### Lokal Test İcrası

1. **Test skriptini hazırla**
```bash
# Repo-nu klonla
git clone https://github.com/SiruzQA/devops-lab.git
cd devops-lab

# Test faylını yerləşdir
mkdir -p tests
# k3s_qa_tests.py faylını tests/ direktorisinə köçür
```

2. **Python dependency-lərini yüklə**
```bash
pip install requests pyyaml
```

3. **K3s və deployment hazırla**
```bash
# Docker image build et
cd docker
docker build -t myapp:latest .

# K3s-ə import et
docker save myapp:latest -o /tmp/myapp.tar
sudo k3s ctr images import /tmp/myapp.tar

# Deploy et
cd ../k3s
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml
```

4. **Testləri işə sal**
```bash
cd tests
python k3s_qa_tests.py
```

### GitHub Actions ilə Avtomatik Test

CI/CD pipeline avtomatik işləyir:
- Hər `push` zamanı (main/develop branch)
- Hər `pull request` zamanı
- Manual trigger ilə

**Workflow faylı:** `.github/workflows/qa-pipeline.yml`

## 📊 Test Nəticələri

### Uğurlu Test Output Nümunəsi
```
=== K3s Service Health Check ===
✓ PASSED - K3s Service Running
  └─ Status: active

=== Pod Readiness Check ===
✓ PASSED - Pod Ready: myapp-deployment-abc123
  └─ Phase: Running, Ready: True
✓ PASSED - Pod Ready: myapp-deployment-def456
  └─ Phase: Running, Ready: True

=== Liveness/Readiness Probe Check ===
✓ PASSED - Probes: myapp-deployment-abc123/myapp
  └─ Liveness: True, Readiness: True

== TEST COVERAGE REPORT ==
Health Checks: 8 passed, 0 failed
Routing Tests: 5 passed, 0 failed

Total Tests: 13
Passed: 13
Failed: 0
Coverage: 100.0%
```

### Failed Test Output Nümunəsi
```
FAILED - Pod Ready: myapp-deployment-xyz789
 └─ Phase: Pending, Ready: False

 FAILED - Service Endpoints: myapp-service
  └─ Active endpoints: 0
```

##  Debugging

### Pod-lar Ready olmursa

```bash
# Pod status yoxla
kubectl get pods -o wide

# Pod describe et (events görmək üçün)
kubectl describe pod <pod-name>

# Pod logs bax
kubectl logs <pod-name>

# Container içərisinə gir
kubectl exec -it <pod-name> -- /bin/sh
```

### Ingress işləmirsə

```bash
# Ingress status
kubectl get ingress -o yaml

# Traefik ingress controller yoxla
kubectl get pods -n kube-system | grep traefik

# Traefik logs
kubectl logs -n kube-system <traefik-pod-name>

# Service endpoints yoxla
kubectl get endpoints
```

### Probe-lar fail olursa

```bash
# Probe konfiqurasiyasını yoxla
kubectl get deployment myapp-deployment -o yaml | grep -A 10 "probe"

# Manual olaraq health endpoint test et
kubectl exec -it <pod-name> -- wget -O- http://localhost:80/

# Probe timing-i artır (əgər app yavaş başlayırsa)
# deployment.yaml-da initialDelaySeconds və timeoutSeconds parametrlərini dəyişdir
```

## 📝 Test Case Sənədləşdirmə

### TC-001: Pod Readiness Verification
**Məqsəd:** Pod-ların Ready state-ə keçdiyini yoxlamaq  
**Preconditions:** K3s cluster running, deployment applied  
**Steps:**
1. `kubectl get pods` əmri ilə pod-ları siyahıla
2. Hər pod-un `STATUS=Running` və `READY=1/1` olmasını yoxla
3. Pod condition-larını `kubectl get pod -o json` ilə verify et

**Expected Result:** Bütün pod-lar Ready state-də  
**Severity:** Critical

### TC-002: Liveness Probe Configuration
**Məqsəd:** Liveness probe-ların düzgün konfiqurasiya edildiyini yoxlamaq  
**Preconditions:** Deployment applied  
**Steps:**
1. `kubectl describe pod` ilə probe konfiqurasiyasını oxu
2. httpGet/exec/tcpSocket method mövcudluğunu yoxla
3. initialDelaySeconds, periodSeconds parametrlərini verify et

**Expected Result:** Liveness probe configured, pod auto-restarts on failure  
**Severity:** High

### TC-003: Ingress HTTP Routing
**Məqsəd:** Ingress routing-in düzgün işlədiyini yoxlamaq  
**Preconditions:** Ingress applied, service running  
**Steps:**
1. `kubectl get ingress` ilə ingress-i siyahıla
2. Host və path routing rules oxu
3. `curl -H "Host: <hostname>" http://localhost` ilə test et

**Expected Result:** HTTP 200 response alınır, düzgün content qaytarılır  
**Severity:** Critical

### TC-004: Horizontal Scaling
**Məqsəd:** Pod-ların horizontal scale olduğunu yoxlamaq  
**Preconditions:** Deployment running with 3 replicas  
**Steps:**
1. `kubectl scale deployment myapp-deployment --replicas=5`
2. Pod-ların 5-ə çatmasını gözlə
3. `kubectl get pods | grep Running | wc -l` ilə say

**Expected Result:** 5 running pod, hər biri Ready state-də  
**Severity:** Medium

### TC-005: Rolling Update
**Məqsəd:** Zero-downtime rolling update-in işlədiyini yoxlamaq  
**Preconditions:** Deployment running, new image available  
**Steps:**
1. `kubectl set image deployment/myapp-deployment myapp=myapp:v2`
2. `kubectl rollout status` ilə update prosesini izlə
3. Update zamanı service availability-ni monitor et

**Expected Result:** Pod-lar tədricən update olunur, downtime olmur  
**Severity:** High

## 🎓 Best Practices

### 1. Probe Konfiqurasiyası
- **initialDelaySeconds**: Tətbiqin başlaması üçün kifayət vaxt ver
- **periodSeconds**: Çox tez-tez yoxlama performance-ə təsir edir
- **failureThreshold**: 3-5 arası optimal
- **Liveness probe**: Ciddi yoxlamalar (məsələn, database connection)
- **Readiness probe**: Traffic almağa hazır olma yoxlaması

### 2. Resource Limits
```yaml
resources:
  requests:
    memory: "64Mi"   # Minimum ehtiyac
    cpu: "100m"
  limits:
    memory: "128Mi"  # Maksimum istifadə
    cpu: "200m"
```

### 3. Rolling Update Strategy
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1  # Downtime minimuma endirmək
    maxSurge: 1        # Resource istifadəsini optimallaşdırmaq
```

### 4. Testing Checklist
- [ ] Bütün pod-lar Ready state-də
- [ ] Probes konfiqurasiya edilib və işləyir
- [ ] Service endpoints aktiv
- [ ] Ingress routing düzgün işləyir
- [ ] HTTP connectivity test keçir
- [ ] Scaling işləyir
- [ ] Rolling update downtime yaratmır

## 📈 Metrics & Monitoring

### Əsas Göstəricilər
- **Pod Readiness Rate**: % Ready pods / Total pods
- **Probe Success Rate**: % Successful probes / Total probe checks  
- **Service Uptime**: Service availability percentage
- **Response Time**: Average HTTP response time
- **Error Rate**: % Failed requests / Total requests

### Monitoring Tools (Optional)
- Prometheus: Metrics collection
- Grafana: Visualization
- Loki: Log aggregation
- AlertManager: Alert routing

## 🔄 CI/CD Integration

GitHub Actions workflow avtomatik:
1. K3s cluster qurur
2. Docker image build edir
3. Kubernetes-ə deploy edir
4. Health check testlərini işə salır
5. Routing testlərini işə salır
6. Scaling testlərini yerinə yetirir
7. Test report generasiya edir

## Əsas suallar?


**S: Probe-lar nə zaman fail olur?**  
C: Timeout aşdıqda, HTTP status 200-399 arası olmadıqda, və ya failureThreshold limitinə çatdıqda.

**S: Liveness və Readiness probe fərqi nədir?**  
C: Liveness pod-un restart edilməsi üçün, Readiness isə traffic almaq üçün hazır olma yoxlamasıdır.

**S: Test nə qədər vaxt aparır?**  
C: Lokal: ~2-3 dəqiqə, CI/CD: ~5-7 dəqiqə (K3s setup daxil olmaqla)

**S: Test fail olarsa nə etməli?**  
C: Logs yoxla (`kubectl logs`), events bax (`kubectl get events`), pod describe et.
