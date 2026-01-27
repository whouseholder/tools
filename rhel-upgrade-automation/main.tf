terraform {
  required_version = ">= 1.0"
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Main orchestration for RHEL 7.9 to 8.10 upgrade
# Handles CDP Private Base cluster upgrade with proper sequencing

locals {
  # Group hosts by role (using final computed host list)
  master_hosts = [for host in local.cluster_hosts_final : host if host.role == "master"]
  edge_hosts   = [for host in local.cluster_hosts_final : host if host.role == "edge"]
  worker_hosts = [for host in local.cluster_hosts_final : host if host.role == "worker"]
  
  # Upgrade order: Edge nodes -> Worker nodes (in batches) -> Master nodes (one at a time)
  # This minimizes cluster downtime
  
  timestamp = formatdate("YYYY-MM-DD-hhmm", timestamp())
}

# Phase 1: Pre-upgrade checks on ALL nodes
module "pre_upgrade_checks" {
  source = "./modules/pre-upgrade"
  
  hosts           = local.cluster_hosts_final
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  backup_path     = var.backup_path
  
  # Run in parallel for speed
  parallel_execution = true
}

# Phase 2: Stop CDP services in proper order
module "cdp_prepare" {
  source = "./modules/cdp-prepare"
  
  depends_on = [module.pre_upgrade_checks]
  
  cm_server_host  = local.cm_server_host_final
  cm_api_user     = var.cm_api_user
  cm_api_password = var.cm_api_password
  cluster_name    = local.cluster_name_final
  
  master_hosts = local.master_hosts
  edge_hosts   = local.edge_hosts
  worker_hosts = local.worker_hosts
  
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
}

# Phase 3: Upgrade edge nodes (parallel - lowest risk)
module "upgrade_edge_nodes" {
  source = "./modules/upgrade-node"
  
  depends_on = [module.cdp_prepare]
  
  hosts           = local.edge_hosts
  node_type       = "edge"
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  target_version  = var.target_rhel_version
  
  parallel_execution = true
  max_parallel       = length(local.edge_hosts)
  
  enable_rollback = var.enable_rollback
}

# Phase 4: Upgrade worker nodes (in batches to maintain capacity)
module "upgrade_worker_nodes" {
  source = "./modules/upgrade-node"
  
  depends_on = [
    module.upgrade_edge_nodes
  ]
  
  hosts           = local.worker_hosts
  node_type       = "worker"
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  target_version  = var.target_rhel_version
  
  # Batch processing to maintain cluster capacity
  parallel_execution = true
  max_parallel       = local.worker_batch_size_final
  
  enable_rollback = var.enable_rollback
}

# Phase 5: Upgrade master nodes (one at a time - highest risk)
module "upgrade_master_nodes" {
  source = "./modules/upgrade-node"
  
  depends_on = [
    module.upgrade_worker_nodes
  ]
  
  hosts           = local.master_hosts
  node_type       = "master"
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  target_version  = var.target_rhel_version
  
  # Masters upgraded sequentially
  parallel_execution = false
  max_parallel       = 1
  
  enable_rollback = var.enable_rollback
}

# Phase 6: Post-upgrade validation
module "post_upgrade_validation" {
  source = "./modules/post-upgrade"
  
  depends_on = [
    module.upgrade_edge_nodes,
    module.upgrade_worker_nodes,
    module.upgrade_master_nodes
  ]
  
  hosts           = local.cluster_hosts_final
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  
  expected_version = var.target_rhel_version
  parallel_execution = true
}

# Phase 7: Restart CDP services
module "cdp_restore" {
  source = "./modules/cdp-restore"
  
  depends_on = [module.post_upgrade_validation]
  
  cm_server_host  = local.cm_server_host_final
  cm_api_user     = var.cm_api_user
  cm_api_password = var.cm_api_password
  cluster_name    = local.cluster_name_final
  
  master_hosts = local.master_hosts
  edge_hosts   = local.edge_hosts
  worker_hosts = local.worker_hosts
  
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  
  perform_health_check = true
}

# Phase 8: Final validation and reporting
module "final_validation" {
  source = "./modules/final-validation"
  
  depends_on = [module.cdp_restore]
  
  cm_server_host  = local.cm_server_host_final
  cm_api_user     = var.cm_api_user
  cm_api_password = var.cm_api_password
  cluster_name    = local.cluster_name_final
  
  hosts           = local.cluster_hosts_final
  ssh_user        = var.ssh_user
  ssh_private_key = var.ssh_private_key
  
  report_path = "${var.backup_path}/upgrade-report-${local.timestamp}.json"
}

