variable "project_name"       { type = string }
variable "environment"        { type = string }
variable "vpc_id"             { type = string }
variable "private_subnet_ids" { type = list(string) }
variable "db_sg_id"           { type = string }
variable "kms_key_arn"        { type = string }
variable "db_name"            { type = string; default = "appdb" }
variable "db_username"        { type = string; default = "appuser" }
variable "db_instance_class"  { type = string; default = "db.t3.medium" }
