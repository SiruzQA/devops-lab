# Deployment Guide

## Quick Deploy
\`\`\`bash
./scripts/deploy.sh
\`\`\`

## Manual Steps
1. Build: `cd docker && docker build -t myapp:latest .`
2. Import: `docker save myapp:latest -o /tmp/myapp.tar`
3. Load: `sudo k3s ctr images import /tmp/myapp.tar`
4. Deploy: `kubectl apply -f k3s/`

## Verify
\`\`\`bash
kubectl get pods,svc,ingress
curl http://localhost
\`\`\`
