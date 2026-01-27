terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

# Stop CDP cluster services before upgrade
resource "null_resource" "stop_cluster_services" {
  triggers = {
    always_run = timestamp()
  }
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/stop_cluster.sh ${var.cm_server_host} ${var.cm_api_user} ${var.cm_api_password} ${var.cluster_name}"
  }
}

# Stop CM agents on all nodes
resource "null_resource" "stop_agents" {
  depends_on = [null_resource.stop_cluster_services]
  
  for_each = { for idx, host in concat(var.master_hosts, var.edge_hosts, var.worker_hosts) : host.hostname => host }
  
  provisioner "remote-exec" {
    inline = [
      "echo 'Stopping Cloudera Manager Agent on ${each.value.hostname}'",
      "systemctl stop cloudera-scm-agent || true",
      "systemctl disable cloudera-scm-agent || true",
      "sleep 5",
      "if systemctl is-active --quiet cloudera-scm-agent; then",
      "  echo 'WARNING: Agent still running, forcing stop'",
      "  killall -9 supervisord || true",
      "  killall -9 python || true",
      "fi"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "5m"
    }
  }
}

# Stop CM Server on master nodes
resource "null_resource" "stop_cm_server" {
  depends_on = [null_resource.stop_agents]
  
  for_each = { for idx, host in var.master_hosts : host.hostname => host if host.hostname == var.cm_server_host }
  
  provisioner "remote-exec" {
    inline = [
      "echo 'Stopping Cloudera Manager Server'",
      "systemctl stop cloudera-scm-server || true",
      "systemctl disable cloudera-scm-server || true",
      "sleep 10"
    ]
    
    connection {
      type        = "ssh"
      host        = each.value.ip_address
      user        = var.ssh_user
      private_key = file(var.ssh_private_key)
      timeout     = "5m"
    }
  }
}

# Create cluster state backup
resource "null_resource" "backup_cluster_state" {
  depends_on = [null_resource.stop_cm_server]
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/backup_cluster_state.sh ${var.cm_server_host} ${var.ssh_user} ${var.ssh_private_key}"
  }
}


