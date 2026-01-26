#!/bin/bash
set -e

echo "⏮️  Rolling back deployment..."

echo "Current rollout history:"
kubectl rollout history deployment/myapp-deployment

if kubectl rollout undo deployment/myapp-deployment; then
    echo "✓ Rollback initiated"
    kubectl rollout status deployment/myapp-deployment
    echo "✓ Rollback completed successfully"
    kubectl get pods
else
    echo "✗ Rollback failed"
    exit 1
fi
