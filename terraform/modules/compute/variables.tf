variable "project_name"         { type = string }
variable "environment"          { type = string }
variable "vpc_id"               { type = string }
variable "public_subnet_ids"    { type = list(string) }
variable "private_subnet_ids"   { type = list(string) }
variable "app_sg_id"            { type = string }
variable "alb_sg_id"            { type = string }
variable "app_instance_profile" { type = string; default = "" }
variable "s3_bucket_arn"        { type = string }
variable "db_endpoint"          { type = string; default = "" }
variable "sqs_queue_arn"        { type = string; default = "" }
variable "instance_type"        { type = string; default = "t3.medium" }
variable "min_size"             { type = number; default = 2 }
variable "max_size"             { type = number; default = 10 }
variable "desired_capacity"     { type = number; default = 3 }
variable "acm_certificate_arn"  { type = string; default = "" }
variable "domain_name"          { type = string; default = "example.com" }
