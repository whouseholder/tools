variable "hosts" {
  description = "List of hosts to validate"
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

variable "expected_version" {
  description = "Expected RHEL version after upgrade"
  type        = string
}

variable "parallel_execution" {
  description = "Execute validations in parallel"
  type        = bool
  default     = true
}


