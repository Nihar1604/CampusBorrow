output "namespace" {
  value = kubernetes_namespace.booking.metadata[0].name
}
