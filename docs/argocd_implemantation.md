# ArgoCD Integration for Continuous Deployment

This document outlines the integration of ArgoCD as the continuous deployment (CD) mechanism for the backend service in the Meeting Booking System project.

## Overview

ArgoCD enables GitOps-based deployment, automatically syncing Kubernetes manifests directly from the Git repository. This ensures that infrastructure and application state are always aligned with source control.

---

## Setup Summary

| Step                             | Method                                 |
|----------------------------------|----------------------------------------|
| ArgoCD installation              | Raw manifests (`kubectl apply`)        |
| Application definition           | `infra/argocd/backend-app.yaml`        |
| Deployment tracking              | Points to `infra/k8s/` (plain YAML)    |
| Sync policy                      | Automated sync with prune + self-heal  |
| Authentication                   | GitHub PAT added to ArgoCD credentials |

---

## Installation & Configuration

### 1. Install ArgoCD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
````

### 2. Expose the UI for Local Access

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

### 3. Install ArgoCD CLI

```bash
sudo curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
sudo chmod +x /usr/local/bin/argocd
```

### 4. Login to ArgoCD

```bash
argocd login localhost:8080
```

*Default credentials are `admin` and the initial password is the name of the ArgoCD server pod.*

---

## Backend Application Integration

The backend application is defined as follows:

### `infra/argocd/backend-app.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: backend-app
  namespace: argocd
spec:
  destination:
    namespace: booking
    server: https://kubernetes.default.svc
  project: default
  source:
    repoURL: https://github.com/JoyJohansson/meeting-booking-system-ci-cd.git
    targetRevision: main
    path: infra/k8s
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

Apply the configuration:

```bash
kubectl apply -f infra/argocd/backend-app.yaml
```

---

## Validation & Status

Check ArgoCD status:

```bash
argocd app list
argocd app get backend-app
```

You should observe:

* **Status**: Synced
* **Health**: Healthy
* **Auto-Sync**: Enabled
* **ConfigMap**: Synced (no health check applicable)

---

## Design Decision: Raw Manifests vs Helm

ArgoCD supports both raw manifests and Helm charts. For this project, **raw manifests were intentionally chosen**.

### Why raw manifests?

* Transparent and beginner-friendly for contributors
* No extra Helm tooling or templating needed
* Perfectly suited for a single-environment DevOps educational setup

### When to switch to Helm?

* You manage multiple environments (dev/stage/prod)
* You need advanced templating or reuse across apps
* Infrastructure complexity grows (e.g., ingress controllers, secrets management, etc.)

For now, simplicity and clarity take precedence.

---

## Authentication Notes

To access private repositories:

* A [GitHub Personal Access Token (PAT)](https://github.com/settings/tokens) must be created.
* Add it to ArgoCD via UI or CLI under `Settings > Repositories`.

---

## Future Enhancements

* Add frontend ArgoCD application
* Use Helm for more scalable configuration
* Expose ArgoCD UI securely via Ingress
* Enable RBAC for multiple user roles

---

## References

* [ArgoCD Application Manifest](../infra/argocd/backend-app.yaml)
* [Backend Deployment YAML](../infra/k8s/deployment-backend.yaml)
* [ArgoCD Docs](https://argo-cd.readthedocs.io/)

