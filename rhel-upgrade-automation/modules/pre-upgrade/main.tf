terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

# Pre-upgrade checks for each host
resource "null_resource" "pre_upgrade_check" {
  for_each = { for idx, host in var.hosts : host.hostname => host }
  
  triggers = {
    host       = each.value.hostname
    ip_address = each.value.ip_address
    role       = each.value.role
    always_run = timestamp()
  }
  
  # Copy pre-upgrade script to host
  provisioner "file" {
    source      = "${path.module}/scripts/pre_upgrade_check.sh"
    destination = "/tmp/pre_upgrade_check.sh"
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "5m"
    }
  }
  
  # Execute pre-upgrade checks
  provisioner "remote-exec" {
    inline = [
      "chmod +x /tmp/pre_upgrade_check.sh",
      "/tmp/pre_upgrade_check.sh ${each.value.role} ${var.backup_path}"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "10m"
    }
  }
  
  # Download pre-upgrade report
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p ${var.backup_path}/pre-upgrade-reports
      scp -i ${var.ssh_private_key} -o StrictHostKeyChecking=no \
        ${var.ssh_user}@${each.value.ip_address}:/tmp/pre_upgrade_report.json \
        ${var.backup_path}/pre-upgrade-reports/${each.value.hostname}.json
    EOT
  }
}

# Aggregate results and check for blockers
resource "null_resource" "check_blockers" {
  depends_on = [null_resource.pre_upgrade_check]
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/check_blockers.sh ${var.backup_path}/pre-upgrade-reports"
  }
}


