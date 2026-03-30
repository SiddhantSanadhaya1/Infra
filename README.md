# InsureCo Insurance Portal — Application & Infrastructure

Full-stack insurance management platform for InsureCo, covering policy lifecycle, claims processing, and customer self-service. Infrastructure is managed with Terraform on AWS.

## Application Overview

The **InsureCo Insurance Portal** is a policy management and claims processing system serving InsureCo's Auto, Home, Life, and Commercial insurance lines.

### Key Features

| Feature | Description |
|---------|-------------|
| **Policy Management** | Create, view, renew, and cancel insurance policies across all product lines |
| **Claims Filing** | Submit and track claims with document upload and status notifications |
| **Quote Calculator** | Real-time premium quotes based on coverage type and customer profile |
| **Document Management** | Secure upload and retrieval of policy documents and claim evidence via S3 |
| **Async Notifications** | SQS-driven Lambda workers handle welcome emails, renewal reminders, and claim updates |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS — hosted via CloudFront + S3 |
| **Backend API** | Python 3.11, FastAPI, SQLAlchemy (async) — containerised, deployed on ASG behind ALB |
| **Database** | Aurora PostgreSQL — policies, claims, customers, documents |
| **Session Store** | DynamoDB — user sessions |
| **Cache** | ElastiCache Redis — quote results, rate limiting |
| **Async Workers** | Python Lambda — `PROCESS_CLAIM`, `WELCOME_EMAIL`, `POLICY_RENEWAL_REMINDER` job types |
| **Queue** | SQS (main + DLQ) + SNS — decouples API from Lambda workers |
| **CDN** | CloudFront — serves Next.js static assets and policy documents |

### Application → Infrastructure Mapping

```
Browser
  └── CloudFront (CDN + SSL termination)
        ├── /api/*  →  ALB  →  ASG (FastAPI containers in private subnets)
        │                         └── Aurora PostgreSQL (multi-AZ)
        │                         └── ElastiCache Redis
        └── /*      →  S3 (Next.js static export / assets)

FastAPI  →  SQS  →  Lambda workers
                      ├── PROCESS_CLAIM       (adjudication logic)
                      ├── WELCOME_EMAIL       (new customer onboarding)
                      └── POLICY_RENEWAL_REMINDER (30-day advance notice)

Secrets: Credentials and API keys stored in Secrets Manager, injected at runtime via SSM
Logs:    CloudWatch Logs + Dashboard; SQS DLQ captures failed Lambda invocations
```

---

## Infrastructure

### Architecture

| Layer | Services |
|-------|----------|
| **Networking** | VPC, Public/Private Subnets (3 AZs), IGW, NAT Gateways, Route Tables, VPC Flow Logs |
| **Security** | KMS, Security Groups (ALB / App / DB), IAM Roles, Secrets Manager, SSM Parameters |
| **Compute** | ECR, ALB, Launch Template, Auto Scaling Group, Lambda, CloudWatch Alarms & Dashboard |
| **Database** | Aurora PostgreSQL (cluster), RDS Cluster Instances, DynamoDB (session store) |
| **Storage** | S3 (app assets + logs), CloudFront CDN, SQS (main + DLQ), SNS, ElastiCache Redis |

### Directory Structure

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

### Usage

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
