# Troubleshooting

## Pods Not Ready
\`\`\`bash
kubectl describe pod <pod-name>
kubectl logs <pod-name>
kubectl get events
\`\`\`

## Ingress Issues
\`\`\`bash
kubectl get ingress -o yaml
kubectl get svc
kubectl get endpoints
\`\`\`

## K3s Down
\`\`\`bash
sudo systemctl status k3s
sudo systemctl restart k3s
\`\`\`
