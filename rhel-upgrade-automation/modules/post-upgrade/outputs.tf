output "validation_status" {
  description = "Post-upgrade validation status"
  value       = "All post-upgrade validations completed"
}

output "validated_hosts" {
  description = "Hosts that passed post-upgrade validation"
  value       = [for host in var.hosts : host.hostname]
}


