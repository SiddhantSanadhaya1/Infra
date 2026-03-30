terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "infra-terraform-state"
    key            = "global/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Application = "InsureCo Insurance Portal"
      Environment = var.environment
      Owner       = "InsureCo-Engineering"
      ManagedBy   = "Terraform"
      Project     = var.project_name
    }
  }
}

# ─── Modules ─────────────────────────────────────────────────────────────────

module "networking" {
  source = "./modules/networking"

  project_name       = var.project_name
  environment        = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
}

module "security" {
  source = "./modules/security"

  project_name = var.project_name
  environment  = var.environment
  vpc_id       = module.networking.vpc_id
}

module "storage" {
  source = "./modules/storage"

  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = module.security.kms_key_arn
}

module "database" {
  source = "./modules/database"

  project_name       = var.project_name
  environment        = var.environment
  vpc_id             = module.networking.vpc_id
  private_subnet_ids = module.networking.private_subnet_ids
  db_sg_id           = module.security.db_security_group_id
  kms_key_arn        = module.security.kms_key_arn
}

module "compute" {
  source = "./modules/compute"

  project_name        = var.project_name
  environment         = var.environment
  vpc_id              = module.networking.vpc_id
  public_subnet_ids   = module.networking.public_subnet_ids
  private_subnet_ids  = module.networking.private_subnet_ids
  app_sg_id           = module.security.app_security_group_id
  alb_sg_id           = module.security.alb_security_group_id
  s3_bucket_arn       = module.storage.app_bucket_arn
  db_endpoint         = module.database.db_endpoint
  instance_type       = var.instance_type
  min_size            = var.asg_min_size
  max_size            = var.asg_max_size
  desired_capacity    = var.asg_desired_capacity
}
