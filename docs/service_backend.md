# Backend Service Configuration

## Overview

This document outlines the configuration of the Kubernetes Service for the backend Flask application. The service enables internal and external communication with the backend pods.

## Service Type

**NodePort**: Exposes the backend service on a static port across all nodes in the cluster.

## YAML Configuration

```yaml
apiVersion: v1
kind: Service
metadata:
  name: backend-service
  labels:
    app: backend
spec:
  selector:
    app: backend
  type: NodePort
  ports:
    - port: 5000
      targetPort: 5000
      nodePort: 30001
```

## Notes

- The `nodePort` is exposed on port `30001` and maps to container port `5000`.
- It uses a label selector (`app: backend`) to target the pods.
