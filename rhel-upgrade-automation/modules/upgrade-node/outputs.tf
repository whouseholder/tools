output "upgraded_hosts" {
  description = "List of successfully upgraded hosts"
  value       = [for host in var.hosts : host.hostname]
}

output "node_type" {
  description = "Type of nodes upgraded"
  value       = var.node_type
}


