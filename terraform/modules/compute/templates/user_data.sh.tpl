#!/bin/bash
set -e

# Install Docker
yum install -y docker
systemctl enable docker
systemctl start docker

# Authenticate with ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ${ecr_repo_url}

# Pull and run the application container
docker pull ${ecr_repo_url}:latest
docker run -d \
  --name app \
  --restart unless-stopped \
  -p 8080:8080 \
  -e ENVIRONMENT=${environment} \
  -e PROJECT_NAME=${project_name} \
  -e DB_ENDPOINT=${db_endpoint} \
  ${ecr_repo_url}:latest
