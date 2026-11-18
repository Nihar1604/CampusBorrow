# System Plan: Meeting Booking System

## 1. Architecture Overview

We'll build a containerised, web-based booking system with a clear separation of concerns.

```
User ⇄ Frontend (HTML/React) ⇄ Backend API (Flask) ⇄ PostgreSQL
                                     ⇵
                                CI/CD + K8s
```

---

## 2. Core Components

| Component        | Technology         | Description |
|------------------|--------------------|-------------|
| Frontend         | HTML/CSS or React  | Simple UI to view slots, book/cancel |
| Backend          | Flask (Python)     | API for auth, booking, admin control |
| Database         | PostgreSQL         | Stores users, bookings, time slots |
| Containerisation | Docker             | Containerise frontend, backend |
| Orchestration    | Kubernetes         | Deploy and manage services |
| Provisioning     | Terraform          | Create local cluster (Minikube) |
| Config/Setup     | Ansible            | K8s node or OS configuration (with rollback support) |
| CI               | GitHub Actions     | Build → Test → Push to GHCR |
| CD               | ArgoCD             | Pull from repo → Apply to cluster |

---

## 3. System Behaviours & Rules

### User
- Can register and login
- Can book one time slot at a time
- Can cancel booking ≥24h in advance
- Can view current booking

### Admin
- Can login (hardcoded or RBAC)
- Can block/unblock time slots
- Can book/unbook any time slot
- Can see all bookings

---

## 4. Entities & Data Model (Initial)

```
User
- id
- username
- email
- phone
- password (hashed)
- is_admin (boolean)

Booking
- id
- user_id (FK)
- slot_id (FK)
- created_at

TimeSlot
- id
- datetime (timestamp)
- status: ["available", "booked", "blocked"]
```

---

## 5. API Design (Sketch)

| Endpoint              | Method | Auth  | Description                  |
|-----------------------|--------|-------|------------------------------|
| /register             | POST   | No    | Register user                |
| /login                | POST   | No    | Login and get token          |
| /slots                | GET    | Yes   | Get all available slots      |
| /book                 | POST   | Yes   | Book a slot (1 per user)     |
| /cancel               | DELETE | Yes   | Cancel booking (≥24h ahead)  |
| /me                   | GET    | Yes   | Get current user info        |
| /admin/slots          | GET    | Admin | View all slots               |
| /timeslot/<id>/block  | PUT    | Admin | Block a time slot            |
| /timeslot/<id>/unblock| PUT    | Admin | Unblock a time slot          |

---

## 6. Environments

| Env       | Details                                     |
|-----------|---------------------------------------------|
| Local Dev | Docker + Minikube + localhost ingress       |
| CI/CD     | GitHub Actions → GHCR + Kubernetes Apply    |
| Prod      | Optional: Azure AKS, GCP GKE, etc.          |

---
