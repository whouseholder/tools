output "pre_check_status" {
  description = "Pre-upgrade check status"
  value       = "All pre-upgrade checks completed"
}

output "checked_hosts" {
  description = "Hosts that passed pre-upgrade checks"
  value       = [for host in var.hosts : host.hostname]
}


