# Secrets Management

## Overview

This document describes how to manage container registry credentials for pulling private images from GitHub Container Registry (GHCR).

## Kubernetes Secret (docker-registry type)

A secret was created using the following command:

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=https://ghcr.io \
  --docker-username=your_username \
  --docker-password=GHCR_TOKEN \
  --docker-email=email@example.com
```

## Usage in Deployment

The `ghcr-secret` is referenced in the deployment spec:

```yaml
spec:
  imagePullSecrets:
    - name: ghcr-secret
```

## Best Practices

- Do **not** store secrets in ConfigMaps or plain YAML.
- Use `.env` files locally but mount secrets in production.
