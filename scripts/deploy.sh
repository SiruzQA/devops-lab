#!/bin/bash
# scripts/deploy.sh - Tez deployment üçün

set -e

echo "🚀 DevOps Lab Deployment Script"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

log_error() {
    echo -e "${RED}✗ $1${NC}"
}

log_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

check_k3s() {
    log_info "Checking K3s..."
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl not found. Please install K3s first."
        exit 1
    fi
    
    if ! sudo systemctl is-active --quiet k3s; then
        log_error "K3s service is not running."
        exit 1
    fi
    
    log_success "K3s is running"
}

build_image() {
    log_info "Building Docker image..."
    cd docker
    
    if docker build -t myapp:latest .; then
        log_success "Docker image built successfully"
    else
        log_error "Docker build failed"
        exit 1
    fi
    
    cd ..
}

import_image() {
    log_info "Importing image to K3s..."
    
    docker save myapp:latest -o /tmp/myapp.tar
    
    if sudo k3s ctr images import /tmp/myapp.tar; then
        log_success "Image imported to K3s"
        rm /tmp/myapp.tar
    else
        log_error "Image import failed"
        exit 1
    fi
}

deploy_resources() {
    log_info "Deploying Kubernetes resources..."
    cd k3s
    
    if kubectl apply -f deployment.yaml; then
        log_success "Deployment applied"
    else
        log_error "Deployment failed"
        exit 1
    fi
    
    if kubectl apply -f service.yaml; then
        log_success "Service applied"
    else
        log_error "Service apply failed"
        exit 1
    fi
    
    if kubectl apply -f ingress.yaml; then
        log_success "Ingress applied"
    else
        log_error "Ingress apply failed"
        exit 1
    fi
    
    cd ..
}

wait_for_pods() {
    log_info "Waiting for pods to be ready..."
    
    if kubectl wait --for=condition=ready pod -l app=myapp --timeout=120s; then
        log_success "All pods are ready"
    else
        log_error "Pods failed to become ready"
        kubectl get pods
        exit 1
    fi
}

show_status() {
    echo ""
    log_info "Deployment Status:"
    echo ""
    
    echo "=== Pods ==="
    kubectl get pods -l app=myapp
    
    echo ""
    echo "=== Services ==="
    kubectl get svc
    
    echo ""
    echo "=== Ingress ==="
    kubectl get ingress
    
    echo ""
    log_success "Deployment completed successfully!"
}

main() {
    check_k3s
    build_image
    import_image
    deploy_resources
    wait_for_pods
    show_status
}

main
