variable "auto_discover_hosts" {
  description = "Automatically discover cluster hosts from Cloudera Manager"
  type        = bool
  default     = false
}

variable "cluster_hosts" {
  description = "List of all cluster hosts with their roles (only used if auto_discover_hosts is false)"
  type = list(object({
    hostname    = string
    ip_address  = string
    role        = string # master, worker, or edge
    description = string
  }))
  default = []
  
  validation {
    condition     = length(var.cluster_hosts) == 0 || alltrue([for host in var.cluster_hosts : contains(["master", "worker", "edge"], host.role)])
    error_message = "Host role must be one of: master, worker, edge"
  }
}

variable "cm_server_host" {
  description = "Cloudera Manager server hostname or IP"
  type        = string
}

variable "cm_api_user" {
  description = "Cloudera Manager API username"
  type        = string
  default     = "admin"
}

variable "cm_api_password" {
  description = "Cloudera Manager API password"
  type        = string
  sensitive   = true
}

variable "cluster_name" {
  description = "Name of the CDP cluster (auto-detected if empty and auto_discover_hosts is true)"
  type        = string
  default     = ""
}

variable "ssh_user" {
  description = "SSH user for connecting to hosts"
  type        = string
  default     = "root"
}

variable "ssh_private_key" {
  description = "Path to SSH private key"
  type        = string
}

variable "target_rhel_version" {
  description = "Target RHEL version"
  type        = string
  default     = "8.10"
}

variable "backup_path" {
  description = "Path for backups and reports"
  type        = string
  default     = "/backup/rhel-upgrade"
}

variable "worker_batch_size" {
  description = "Number of worker nodes to upgrade in parallel (0 = auto-calculate based on cluster size)"
  type        = number
  default     = 0
  
  validation {
    condition     = var.worker_batch_size >= 0 && var.worker_batch_size <= 10
    error_message = "Worker batch size must be between 0 (auto) and 10"
  }
}

variable "enable_rollback" {
  description = "Enable automatic rollback on failure"
  type        = bool
  default     = true
}

variable "max_upgrade_time" {
  description = "Maximum time (in minutes) to wait for each node upgrade"
  type        = number
  default     = 120
}

variable "pre_upgrade_snapshot" {
  description = "Create VM snapshots before upgrade (if supported)"
  type        = bool
  default     = true
}

variable "skip_services" {
  description = "List of CDP services to skip during stop/start"
  type        = list(string)
  default     = []
}

