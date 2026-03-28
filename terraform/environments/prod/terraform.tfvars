environment          = "prod"
aws_region           = "us-east-1"
project_name         = "infra-app"

vpc_cidr             = "10.1.0.0/16"
availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
public_subnets       = ["10.1.1.0/24", "10.1.2.0/24", "10.1.3.0/24"]
private_subnets      = ["10.1.11.0/24", "10.1.12.0/24", "10.1.13.0/24"]

instance_type        = "t3.large"
asg_min_size         = 3
asg_max_size         = 20
asg_desired_capacity = 6

db_instance_class    = "db.r6g.large"
db_name              = "appdb"
