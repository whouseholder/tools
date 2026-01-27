terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
    local = {
      source = "hashicorp/local"
    }
  }
}

# Final comprehensive validation
resource "null_resource" "final_validation" {
  triggers = {
    always_run = timestamp()
  }
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/final_validation.sh ${var.cm_server_host} ${var.cm_api_user} ${var.cm_api_password} ${var.cluster_name} ${var.report_path}"
  }
}

# Generate final report
resource "local_file" "upgrade_report" {
  depends_on = [null_resource.final_validation]
  
  filename = var.report_path
  content = jsonencode({
    timestamp = timestamp()
    cluster_name = var.cluster_name
    cm_server = var.cm_server_host
    total_hosts = length(var.hosts)
    upgraded_hosts = [for host in var.hosts : {
      hostname = host.hostname
      ip_address = host.ip_address
      role = host.role
    }]
    status = "completed"
  })
}


