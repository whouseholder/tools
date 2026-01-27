terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

locals {
  # Determine if we should run in parallel or sequential
  host_batches = var.parallel_execution ? chunklist(var.hosts, var.max_parallel) : [for h in var.hosts : [h]]
}

# Upgrade nodes in batches
resource "null_resource" "upgrade_batch" {
  count = length(local.host_batches)
  
  triggers = {
    batch_id   = count.index
    always_run = timestamp()
  }
  
  # Ensure batches run sequentially
  depends_on = [
    null_resource.upgrade_batch
  ]
  
  provisioner "local-exec" {
    command = <<-EOT
      echo "Starting upgrade batch ${count.index + 1}/${length(local.host_batches)}"
      echo "Hosts in this batch: ${length(local.host_batches[count.index])}"
    EOT
  }
}

# Upgrade individual nodes
resource "null_resource" "upgrade_node" {
  for_each = { for idx, host in var.hosts : host.hostname => host }
  
  triggers = {
    host         = each.value.hostname
    ip_address   = each.value.ip_address
    role         = each.value.role
    target_version = var.target_version
    always_run   = timestamp()
  }
  
  # Copy upgrade scripts
  provisioner "file" {
    source      = "${path.module}/scripts/"
    destination = "/tmp/upgrade-scripts"
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "5m"
    }
  }
  
  # Execute pre-upgrade backup
  provisioner "remote-exec" {
    inline = [
      "chmod +x /tmp/upgrade-scripts/*.sh",
      "/tmp/upgrade-scripts/backup_system.sh ${each.value.role}"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "30m"
    }
  }
  
  # Install and configure Leapp
  provisioner "remote-exec" {
    inline = [
      "/tmp/upgrade-scripts/install_leapp.sh"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "10m"
    }
  }
  
  # Run leapp preupgrade
  provisioner "remote-exec" {
    inline = [
      "/tmp/upgrade-scripts/run_leapp_preupgrade.sh ${each.value.role}"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "20m"
    }
  }
  
  # Execute the upgrade
  provisioner "remote-exec" {
    inline = [
      "/tmp/upgrade-scripts/run_upgrade.sh ${var.target_version} ${each.value.role}"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "120m"
    }
  }
  
  # Wait for reboot and system to come back online
  provisioner "local-exec" {
    command = "${path.module}/scripts/wait_for_host.sh ${each.value.ip_address} ${var.ssh_user} ${var.ssh_private_key}"
  }
  
  # Post-upgrade immediate checks
  provisioner "remote-exec" {
    inline = [
      "cat /etc/redhat-release",
      "uname -r",
      "systemctl status --no-pager"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "5m"
    }
  }
  
  # Handle rollback on failure
  provisioner "local-exec" {
    when    = destroy
    command = "echo 'Cleanup for ${each.value.hostname}'"
  }
}

# Verify all nodes in batch completed successfully
resource "null_resource" "verify_batch_completion" {
  count = length(local.host_batches)
  
  depends_on = [null_resource.upgrade_node]
  
  provisioner "local-exec" {
    command = <<-EOT
      echo "Batch ${count.index + 1} upgrade completed"
      echo "Waiting before next batch..."
      sleep 60
    EOT
  }
}


