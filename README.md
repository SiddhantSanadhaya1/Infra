# Infra — AWS Terraform Infrastructure

Multi-tier AWS infrastructure managed with Terraform.

## Architecture

| Layer | Services |
|-------|----------|
| **Networking** | VPC, Public/Private Subnets (3 AZs), IGW, NAT Gateways, Route Tables, VPC Flow Logs |
| **Security** | KMS, Security Groups (ALB / App / DB), IAM Roles, Secrets Manager, SSM Parameters |
| **Compute** | ECR, ALB, Launch Template, Auto Scaling Group, Lambda, CloudWatch Alarms & Dashboard |
| **Database** | Aurora PostgreSQL (cluster), RDS Cluster Instances, DynamoDB (session store) |
| **Storage** | S3 (app assets + logs), CloudFront CDN, SQS (main + DLQ), SNS, ElastiCache Redis |

## Directory Structure

```
terraform/
├── main.tf                  # Root module — wires everything together
├── variables.tf
├── outputs.tf
├── modules/
│   ├── networking/          # VPC, subnets, IGW, NAT, route tables
│   ├── security/            # KMS, security groups, IAM, Secrets Manager
│   ├── storage/             # S3, CloudFront, SQS, SNS, ElastiCache
│   ├── database/            # Aurora PostgreSQL, DynamoDB
│   └── compute/             # ECR, ALB, ASG, Lambda, CloudWatch
└── environments/
    ├── dev/terraform.tfvars
    └── prod/terraform.tfvars
```

## Usage

```bash
cd terraform

# Dev
terraform init
terraform plan -var-file=environments/dev/terraform.tfvars
terraform apply -var-file=environments/dev/terraform.tfvars

# Prod
terraform plan -var-file=environments/prod/terraform.tfvars
terraform apply -var-file=environments/prod/terraform.tfvars
```
