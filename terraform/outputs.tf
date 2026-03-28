output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.compute.alb_dns_name
}

output "app_bucket_name" {
  description = "Name of the S3 application bucket"
  value       = module.storage.app_bucket_name
}

output "db_endpoint" {
  description = "RDS endpoint (without port)"
  value       = module.database.db_endpoint
  sensitive   = true
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain name"
  value       = module.storage.cloudfront_domain
}

output "ecr_repository_url" {
  description = "ECR repository URL for the application image"
  value       = module.compute.ecr_repository_url
}
