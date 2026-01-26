#!/bin/bash
set -e

echo "🧹 Cleaning up DevOps Lab resources..."

kubectl delete -f k3s/ingress.yaml --ignore-not-found=true
kubectl delete -f k3s/service.yaml --ignore-not-found=true
kubectl delete -f k3s/deployment.yaml --ignore-not-found=true

kubectl wait --for=delete pod -l app=myapp --timeout=60s 2>/dev/null || true

read -p "Delete Docker images? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi myapp:latest 2>/dev/null || true
    sudo k3s ctr images rm docker.io/library/myapp:latest 2>/dev/null || true
    echo "✓ Images deleted"
fi

echo "✓ Cleanup completed"
