variable "cm_server_host" {
  description = "Cloudera Manager server hostname"
  type        = string
}

variable "cm_api_user" {
  description = "CM API username"
  type        = string
}

variable "cm_api_password" {
  description = "CM API password"
  type        = string
  sensitive   = true
}

variable "cluster_name" {
  description = "CDP cluster name"
  type        = string
}

variable "hosts" {
  description = "All cluster hosts"
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

variable "report_path" {
  description = "Path to save final report"
  type        = string
}


