# ConfigMap: Backend Environment Configuration

This ConfigMap provides the backend application with environment variables necessary for runtime operation in Kubernetes.

## File: `infra/k8s/configmap.yaml`

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: backend-config
  namespace: booking
data:
  FLASK_ENV: production
  SECRET_KEY: super-secret-key
  DATABASE_URL: sqlite:///../dev.db
```

## Purpose

- Replace `.env` file with a Kubernetes-native approach.
- Makes environment variables available to the Flask container.
- Configurable per environment (dev, staging, prod).

## Usage

The variables are injected into the container via `envFrom` in the Deployment spec:

```yaml
envFrom:
  - configMapRef:
      name: backend-config
```
