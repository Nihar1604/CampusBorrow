# Terraform: Local Kubernetes Cluster Provisioning

This setup provisions a local Kubernetes namespace and sets context using Terraform and `kubectl`.

## File: `infra/terraform/main.tf`

```hcl
resource "null_resource" "create_booking_namespace" {
  provisioner "local-exec" {
    command = "kubectl create namespace booking || echo 'Namespace already exists'"
  }
}

resource "null_resource" "set_kubectl_context" {
  provisioner "local-exec" {
    command = "kubectl config set-context --current --namespace=booking"
  }

  depends_on = [null_resource.create_booking_namespace]
}
```

## Usage

1. Navigate to the Terraform directory:
   ```bash
   cd infra/terraform
   ```

2. Initialise and apply:
   ```bash
   terraform init
   terraform apply
   ```

## Outcome

- Creates a dedicated namespace `booking`.
- Sets `kubectl` context to target `booking` automatically.
