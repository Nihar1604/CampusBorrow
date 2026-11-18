# Environment Overview

## Local Development

- **Container Runtime**: Docker
- **Cluster**: Minikube
- **Ingress Controller**: NGINX
- **Hostname**: `meeting.local` mapped to Minikube IP in `/etc/hosts`

## Environment Variables

Managed using a `ConfigMap`, replacing the use of `.env` files in Kubernetes:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
data:
  FLASK_ENV: development
  SECRET_KEY: your-dev-secret
  DATABASE_URL: sqlite:///../dev.db
```

## Accessing the App

- API Health Check: `http://meeting.local/api/health`
- NodePort Service: `localhost:30001`

## CI/CD

- GitHub Actions CI pipeline builds and pushes image to GHCR.
- Deployment triggered via Kubernetes manifests.
