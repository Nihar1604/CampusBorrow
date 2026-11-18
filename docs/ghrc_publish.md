# GitHub Container Registry (GHCR) Setup

## Objective

Publish backend Docker image to GHCR and pull it securely from Kubernetes.

## Steps

### 1. Authenticate Docker with GHCR
```bash
echo <YOUR_PAT> | docker login ghcr.io -u <your-username> --password-stdin
```

### 2. Build and Push
```bash
docker build -t ghcr.io/<your-username>/meeting-backend:latest ./backend
docker push ghcr.io/<your-username>/meeting-backend:latest
```

### 3. Create Kubernetes Secret
```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=https://ghcr.io \
  --docker-username=<your-username> \
  --docker-password=<YOUR_PAT> \
  --docker-email=your@email.com \
  --namespace booking
```

## Usage in Deployment YAML

```yaml
spec:
  imagePullSecrets:
    - name: ghcr-secret
```

## Notes

- Use lowercase repository/image names.
- The PAT must have `packages: write` and `repo` scope if using classic tokens.
