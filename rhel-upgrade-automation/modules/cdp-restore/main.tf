terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
    }
  }
}

# Start CM Server on master node
resource "null_resource" "start_cm_server" {
  for_each = { for idx, host in var.master_hosts : host.hostname => host if host.hostname == var.cm_server_host }
  
  triggers = {
    always_run = timestamp()
  }
  
  provisioner "remote-exec" {
    inline = [
      "echo 'Starting Cloudera Manager Server'",
      "systemctl enable cloudera-scm-server",
      "systemctl start cloudera-scm-server",
      "echo 'Waiting for CM Server to start...'",
      "sleep 30"
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

# Wait for CM Server to be ready
resource "null_resource" "wait_for_cm_server" {
  depends_on = [null_resource.start_cm_server]
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/wait_for_cm.sh ${var.cm_server_host} ${var.cm_api_user} ${var.cm_api_password}"
  }
}

# Start CM agents on all nodes
resource "null_resource" "start_agents" {
  depends_on = [null_resource.wait_for_cm_server]
  
  for_each = { for idx, host in concat(var.master_hosts, var.edge_hosts, var.worker_hosts) : host.hostname => host }
  
  provisioner "remote-exec" {
    inline = [
      "echo 'Starting Cloudera Manager Agent on ${each.value.hostname}'",
      "systemctl enable cloudera-scm-agent",
      "systemctl start cloudera-scm-agent",
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

# Wait for all agents to connect
resource "null_resource" "wait_for_agents" {
  depends_on = [null_resource.start_agents]
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/wait_for_agents.sh ${var.cm_server_host} ${var.cm_api_user} ${var.cm_api_password} ${length(concat(var.master_hosts, var.edge_hosts, var.worker_hosts))}"
  }
}

# Start cluster services
resource "null_resource" "start_cluster_services" {
  depends_on = [null_resource.wait_for_agents]
  
  count = var.perform_health_check ? 1 : 0
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/start_cluster.sh ${var.cm_server_host} ${var.cm_api_user} ${var.cm_api_password} ${var.cluster_name}"
  }
}

# Perform health check
resource "null_resource" "health_check" {
  depends_on = [null_resource.start_cluster_services]
  
  count = var.perform_health_check ? 1 : 0
  
  provisioner "local-exec" {
    command = "${path.module}/scripts/health_check.sh ${var.cm_server_host} ${var.cm_api_user} ${var.cm_api_password} ${var.cluster_name}"
  }
}


