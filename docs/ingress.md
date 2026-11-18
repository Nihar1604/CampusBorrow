# Ingress: Backend Exposure via meeting.local

The Ingress resource enables access to the backend API at `http://meeting.local/api`.

## File: `infra/k8s/ingress.yaml`

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: backend-ingress
  namespace: booking
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  ingressClassName: nginx
  rules:
    - host: meeting.local
      http:
        paths:
          - path: /api/(.*)
            pathType: Prefix
            backend:
              service:
                name: backend-service
                port:
                  number: 5000
```

## Local Setup

Update `/etc/hosts`:

```bash
sudo nano /etc/hosts
```

Add:

```
192.168.49.2 meeting.local
```

> Replace IP with `minikube ip` output.

## Expected Behaviour

- `curl http://meeting.local/api/health` → returns `{"status": "ok"}`.
- Redirects all `/api/*` requests to the Flask service.
