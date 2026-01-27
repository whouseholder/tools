# Data sources for dynamic cluster discovery

# Fetch cluster hosts from Cloudera Manager
data "external" "cm_cluster_hosts" {
  count = var.auto_discover_hosts ? 1 : 0
  
  program = [
    "${path.module}/scripts/fetch-cm-hosts.sh",
    var.cm_server_host,
    var.cm_api_user,
    var.cm_api_password,
    var.cluster_name
  ]
}

# Local variable to merge manual and auto-discovered hosts
locals {
  # Use auto-discovered hosts if enabled, otherwise use manual configuration
  discovered_hosts = var.auto_discover_hosts ? jsondecode(data.external.cm_cluster_hosts[0].result.hosts) : []
  
  # Final host list
  cluster_hosts_final = var.auto_discover_hosts ? [
    for host in local.discovered_hosts : {
      hostname    = host.hostname
      ip_address  = host.ip_address
      role        = host.role
      description = host.description
    }
  ] : var.cluster_hosts
  
  # Auto-discovered cluster name (or use provided)
  cluster_name_final = var.cluster_name != "" ? var.cluster_name : (
    var.auto_discover_hosts && length(data.external.cm_cluster_hosts) > 0 ? 
    jsondecode(data.external.cm_cluster_hosts[0].result.cluster_name) : 
    var.cluster_name
  )
  
  # Auto-discovered CM server (or use provided)
  cm_server_host_final = var.auto_discover_hosts && length(data.external.cm_cluster_hosts) > 0 ? 
    jsondecode(data.external.cm_cluster_hosts[0].result.cm_server_host) : 
    var.cm_server_host
  
  # Auto-calculate worker batch size if set to 0
  worker_count = length([for h in local.cluster_hosts_final : h if h.role == "worker"])
  worker_batch_size_final = var.worker_batch_size == 0 ? max(2, min(10, floor(local.worker_count / 3))) : var.worker_batch_size
}

# Output discovered information for validation
output "discovered_cluster_info" {
  description = "Discovered cluster information from CM"
  value = var.auto_discover_hosts ? {
    cluster_name    = local.cluster_name_final
    cm_server_host  = local.cm_server_host_final
    total_hosts     = length(local.cluster_hosts_final)
    master_nodes    = length([for h in local.cluster_hosts_final : h if h.role == "master"])
    worker_nodes    = length([for h in local.cluster_hosts_final : h if h.role == "worker"])
    edge_nodes      = length([for h in local.cluster_hosts_final : h if h.role == "edge"])
  } : null
}

