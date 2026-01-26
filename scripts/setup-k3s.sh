#!/bin/bash
set -e

echo "🔧 Setting up K3s..."

if command -v kubectl &> /dev/null; then
    echo "✓ K3s already installed"
    kubectl version --client
    exit 0
fi

echo "Installing K3s..."
curl -sfL https://get.k3s.io | sh -

sudo chmod 644 /etc/rancher/k3s/k3s.yaml
mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER ~/.kube/config

timeout 120 bash -c 'until kubectl get nodes | grep -q "Ready"; do sleep 2; done'

echo "✓ K3s setup completed"
kubectl get nodes
