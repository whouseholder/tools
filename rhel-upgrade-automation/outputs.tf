output "upgrade_summary" {
  description = "Summary of the upgrade process"
  value = {
    auto_discovered     = var.auto_discover_hosts
    total_hosts         = length(local.cluster_hosts_final)
    master_nodes        = length([for h in local.cluster_hosts_final : h if h.role == "master"])
    worker_nodes        = length([for h in local.cluster_hosts_final : h if h.role == "worker"])
    edge_nodes          = length([for h in local.cluster_hosts_final : h if h.role == "edge"])
    target_version      = var.target_rhel_version
    cm_server           = local.cm_server_host_final
    cluster_name        = local.cluster_name_final
  }
}

output "pre_check_status" {
  description = "Pre-upgrade check status"
  value       = module.pre_upgrade_checks.pre_check_status
}

output "edge_nodes_upgraded" {
  description = "Edge nodes that were upgraded"
  value       = module.upgrade_edge_nodes.upgraded_hosts
}

output "worker_nodes_upgraded" {
  description = "Worker nodes that were upgraded"
  value       = module.upgrade_worker_nodes.upgraded_hosts
}

output "master_nodes_upgraded" {
  description = "Master nodes that were upgraded"
  value       = module.upgrade_master_nodes.upgraded_hosts
}

output "validation_status" {
  description = "Post-upgrade validation status"
  value       = module.post_upgrade_validation.validation_status
}

output "cluster_status" {
  description = "CDP cluster status"
  value       = module.cdp_restore.cluster_started
}

output "upgrade_complete" {
  description = "Final upgrade completion status"
  value       = module.final_validation.upgrade_complete
}

output "final_report_location" {
  description = "Location of final upgrade report"
  value       = module.final_validation.report_location
}

output "next_steps" {
  description = "Recommended next steps after upgrade"
  value = <<-EOT
  
  ========================================
  RHEL Upgrade Completed Successfully!
  ========================================
  
  Next Steps:
  
  1. Verify Cluster Health:
     - Access CM UI: http://${var.cm_server_host}:7180
     - Check all services are healthy
     - Review any warnings or alerts
  
  2. Run Test Jobs:
     - Submit a test MapReduce job
     - Run Impala queries
     - Test Spark applications
  
  3. Monitor for 24-48 hours:
     - Watch for any degraded services
     - Check logs for errors
     - Monitor resource utilization
  
  4. Clean Up (after validation):
     ssh root@<host> "dnf remove \$(rpm -qa | grep 'el7')"
     ssh root@<host> "rm -f /boot/*rescue*"
  
  5. Documentation:
     - Update your runbooks
     - Record any issues encountered
     - Note actual upgrade times
  
  Report Location: ${var.backup_path}/upgrade-report-*.json
  
  ========================================
  EOT
}

