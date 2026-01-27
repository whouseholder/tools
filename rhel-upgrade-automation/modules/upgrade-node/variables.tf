variable "hosts" {
  description = "List of hosts to upgrade"
  type = list(object({
    hostname    = string
    ip_address  = string
    role        = string
    description = string
  }))
}

variable "node_type" {
  description = "Type of nodes being upgraded (master, worker, edge)"
  type        = string
}

variable "ssh_user" {
  description = "SSH user"
  type        = string
}

variable "ssh_private_key" {
  description = "Path to SSH private key"
  type        = string
}

variable "target_version" {
  description = "Target RHEL version (e.g., 8.10)"
  type        = string
}

variable "parallel_execution" {
  description = "Execute upgrades in parallel"
  type        = bool
  default     = false
}

variable "max_parallel" {
  description = "Maximum number of parallel upgrades"
  type        = number
  default     = 1
}

variable "enable_rollback" {
  description = "Enable automatic rollback on failure"
  type        = bool
  default     = true
}


