---
name: User Story
about: Agile User Story template for CampusBorrow features and enhancements
title: 'USER STORY: [Short Title]'
labels: 'user story, enhancement'
assignees: ''
---

### 📋 Story Description
**As a** [role: Student / Lab Coordinator / Administrator]  
**I want** [capability / feature]  
**So that** [benefit / business value / outcome]  

---

### 🎯 Acceptance Criteria
```gherkin
Given [initial context or system state]
When [an event or action occurs]
Then [ensure these outcomes]
```

- [ ] **Criterion 1**: [Input validation and error handling (HTTP 400/404/409)]
- [ ] **Criterion 2**: [Expected response structure and state update]
- [ ] **Criterion 3**: [Automated Pytest coverage (Unit & Integration tests)]
- [ ] **Criterion 4**: [Security & RBAC authorization check]

---

### 🛠️ Technical Details & Notes
- **API Endpoint(s)**: `METHOD /api/...`
- **Database Model(s)**: `User` / `Resource` / `BorrowRequest`
- **RBAC Required**: `Student` / `Lab Coordinator` / `Public`
- **DevSecOps Checklist**:
  - [ ] Input sanitized and schema validated
  - [ ] Flask-Talisman security headers preserved
  - [ ] Prometheus metrics incremented where appropriate
