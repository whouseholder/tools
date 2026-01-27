variable "hosts" {
  description = "List of hosts to check"
  type = list(object({
    hostname    = string
    ip_address  = string
    role        = string
    description = string
  }))
}

variable "ssh_user" {
  description = "SSH user"
  type        = string
}

variable "ssh_private_key" {
  description = "Path to SSH private key"
  type        = string
}

variable "backup_path" {
  description = "Path for backups and reports"
  type        = string
}

variable "parallel_execution" {
  description = "Execute checks in parallel"
  type        = bool
  default     = true
}


