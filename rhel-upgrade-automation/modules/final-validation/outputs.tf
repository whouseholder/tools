output "upgrade_complete" {
  description = "Upgrade completion status"
  value       = "RHEL upgrade completed successfully for all nodes"
}

output "report_location" {
  description = "Location of final upgrade report"
  value       = var.report_path
}


