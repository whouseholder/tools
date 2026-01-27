terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

# Post-upgrade validation for each host
resource "null_resource" "post_upgrade_validation" {
  for_each = { for idx, host in var.hosts : host.hostname => host }
  
  triggers = {
    host       = each.value.hostname
    ip_address = each.value.ip_address
    role       = each.value.role
    always_run = timestamp()
  }
  
  # Copy validation script to host
  provisioner "file" {
    source      = "${path.module}/scripts/post_upgrade_validation.sh"
    destination = "/tmp/post_upgrade_validation.sh"
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "5m"
    }
  }
  
  # Execute post-upgrade validation
  provisioner "remote-exec" {
    inline = [
      "chmod +x /tmp/post_upgrade_validation.sh",
      "/tmp/post_upgrade_validation.sh ${each.value.role} ${var.expected_version}"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "10m"
    }
  }
  
  # Download validation report
  provisioner "local-exec" {
    command = <<-EOT
      mkdir -p /tmp/post-upgrade-reports
      scp -i ${var.ssh_private_key} -o StrictHostKeyChecking=no \
        ${var.ssh_user}@${each.value.ip_address}:/tmp/post_upgrade_report.json \
        /tmp/post-upgrade-reports/${each.value.hostname}.json || true
    EOT
  }
}

# Aggregate validation results
resource "null_resource" "aggregate_validation" {
  depends_on = [null_resource.post_upgrade_validation]
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/aggregate_validation.sh /tmp/post-upgrade-reports"
  }
}


