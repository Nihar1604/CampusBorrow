provider "kubernetes" {
  config_path = "~/.kube/config"
}

resource "kubernetes_namespace" "booking" {
  metadata {
    name = "booking"
  }
}
