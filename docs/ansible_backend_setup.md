# Ansible Backend Setup

This document describes how Ansible is used to configure the local host for backend development and deployment in the **Meeting Booking System** project. It ensures all critical tools are installed, handles environment setup, and supports Docker container rollout with automatic rollback.

---

## Purpose

To automate backend infrastructure preparation for local development:

- Ensure consistency across machines
- Minimise manual setup steps
- Support robust container deployment using Docker
- Simplify local onboarding for collaborators

---

## Components Installed

- **Docker**: Required for containerisation
- **Minikube**: Local Kubernetes cluster (optional)
- **pip & Python Docker SDK**: Required to manage Docker with Ansible
- **.env**: Injected secrets and configs
- **Container rollback**: Resilient fallback if a deployment fails

---

## Directory Structure



## Directory Structure

```

infra/
└── ansible/
├── inventory/
│   └── hosts.ini
├── playbooks/
│   └── site.yml
└── roles/
└── backend/
├── tasks/
       └── main.yml

ansible.cfg    


````

## ansible.cfg

Placed at project root:

```ini
[defaults]
inventory =infra/ansible/inventory/hosts.ini
roles_path = infra/ansible/roles
host_key_checking = false
ask_become_pass = true

[privilege_escalation]
become = true
become_method = sudo
````

## Inventory

**infra/ansible/inventory/hosts.ini**:

```ini
[local]
localhost ansible_connection=local
```

## Playbook

**infra/ansible/playbooks/site.yml**:

```yaml
- hosts: local
  become: true
  vars:
    env_file_path: "{{ lookup('env', 'HOME') }}/Projects/meeting-booking-system-ci-cd/.env" # change to your path directory
  roles:
    - backend
```

## Role Tasks

**infra/ansible/roles/backend/tasks/main.yml** includes:

* Docker, Minikube, pip installation
* `.kube` and `.minikube` directories
* `.env` creation and parsing into `env_vars`
* Container deployment using `community.docker.docker_container`
* Rollback to previous image if the deployment fails
* Test for sudo access by touching a file in `/root`



---

## Role: `backend`

### Role Location

**infra/ansible/roles/backend/tasks/main.yml**

### Main Tasks Performed

1. **Verify sudo access**
   * Test by creating a file in `/root`

2. **Ensure Docker is installed**
   * Uses APT package manager

3. **Start Docker service**

4. **Install Minikube (if not present)**

5. **Ensure pip and Python Docker SDK are installed**

6. **Create necessary directories**
   * `~/.kube`, `~/.minikube`

7. **Ensure `.env` file exists**
   * Critical for injecting secrets

8. **Parse `.env` into environment variables**

9. **Deploy the backend Docker container**
   * Uses latest image from GitHub Container Registry
   * Binds to port 5000
   * Injects `env_vars`

10. **If deployment fails, rollback**
    * Reverts to previous known-good container
    * Displays warning

11. **Notify on completion**
    * Shows success or rollback message

---


### Example Task: Parsing `.env`

```yaml
- name: Parse .env into dict
  ansible.builtin.set_fact:
    env_vars: >-
          {{
            dict(
              (env_file_raw.content
              | b64decode
              | string)
              .splitlines()
              | select("match", "^[A-Za-z_]+[A-Za-z0-9_]*=.*")
              | map('split', '=', 1)
            )
          }}

```

## Usage

Run the playbook using:

```bash
ansible-playbook -i infra/ansible/inventory/hosts.ini infra/ansible/playbooks/site.yml --ask-become-pass
```

## Notes

* Ensure `.env` file exists and is populated with valid `KEY=value` entries.
* A test task is included to verify `sudo` access; it touches a file in `/root`.

## Rollback Behaviour

If the new backend container fails to start, the system will:

1. Remove the failed container
2. Recreate the previous version
3. Output a rollback confirmation message

---

```plaintext
✅ Local host fully configured for development and deployment.
⚠️ Rollback completed — restored previous image.
```
---

## Next Steps

* Extend the playbook with secrets management (e.g. Vault)
* Integrate this with the CI pipeline
* Add support for Kubernetes deployment via `kubectl` or `Helm`

---