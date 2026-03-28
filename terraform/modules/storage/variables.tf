variable "project_name"      { type = string }
variable "environment"       { type = string }
variable "kms_key_arn"       { type = string }
variable "private_subnet_ids" { type = list(string); default = [] }
variable "cache_sg_ids"      { type = list(string); default = [] }
variable "alert_email"       { type = string; default = "ops@example.com" }
