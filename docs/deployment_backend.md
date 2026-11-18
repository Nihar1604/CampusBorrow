# Kubernetes Deployment: Backend

## Overview

The backend Flask API is containerised and deployed to a local Kubernetes cluster (Minikube) using standard Kubernetes manifests.

## Files Used

- `deployment-backend.yaml`: Defines the Deployment resource.
- `service-backend.yaml`: Exposes the backend via NodePort.
- `ingress.yaml`: Routes `/api/*` traffic to the backend.
- `configMap.yaml`: Injects environment variables.

## Deployment Steps

1. Ensure Docker image is built and pushed to GHCR:
   ```bash
   docker build -t ghcr.io/<your-user>/meeting-backend:latest ./backend
   docker push ghcr.io/<your-user>/meeting-backend:latest
   ```

2. Apply Kubernetes resources:
   ```bash
   kubectl apply -f infra/k8s/
   ```

3. Add this line to `/etc/hosts`:
   ```
   192.168.49.2 meeting.local
   ```

4. Test:
   ```bash
   curl http://meeting.local/api/health
   ```

## Notes

- Namespace: `booking`
- Image pull secrets required for GHCR private images.
- Ingress uses NGINX controller.