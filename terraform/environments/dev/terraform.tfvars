environment          = "dev"
aws_region           = "us-east-1"
project_name         = "infra-app"

vpc_cidr             = "10.0.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnets       = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
private_subnets      = ["10.0.11.0/24", "10.0.12.0/24", "10.0.13.0/24"]

instance_type        = "t3.medium"
asg_min_size         = 1
asg_max_size         = 4
asg_desired_capacity = 2

db_instance_class    = "db.t3.medium"
db_name              = "appdb"
