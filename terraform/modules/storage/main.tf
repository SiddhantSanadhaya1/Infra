# ─── S3 Bucket — Application Assets ──────────────────────────────────────────

resource "aws_s3_bucket" "app" {
  bucket = "${var.project_name}-${var.environment}-app-assets"

  tags = { Name = "${var.project_name}-${var.environment}-app-assets" }
}

resource "aws_s3_bucket_versioning" "app" {
  bucket = aws_s3_bucket.app.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "app" {
  bucket = aws_s3_bucket.app.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = var.kms_key_arn
    }
  }
}

resource "aws_s3_bucket_public_access_block" "app" {
  bucket                  = aws_s3_bucket.app.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "app" {
  bucket = aws_s3_bucket.app.id

  rule {
    id     = "archive-old-versions"
    status = "Enabled"

    noncurrent_version_transition {
      noncurrent_days = 30
      storage_class   = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# ─── S3 Bucket — Access Logs ──────────────────────────────────────────────────

resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-${var.environment}-access-logs"

  tags = { Name = "${var.project_name}-${var.environment}-access-logs" }
}

resource "aws_s3_bucket_public_access_block" "logs" {
  bucket                  = aws_s3_bucket.logs.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ─── CloudFront Distribution ──────────────────────────────────────────────────

resource "aws_cloudfront_origin_access_control" "app" {
  name                              = "${var.project_name}-${var.environment}-oac"
  description                       = "OAC for app assets bucket"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "app" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} ${var.environment} CDN"
  default_root_object = "index.html"

  origin {
    domain_name              = aws_s3_bucket.app.bucket_regional_domain_name
    origin_id                = "S3-${aws_s3_bucket.app.id}"
    origin_access_control_id = aws_cloudfront_origin_access_control.app.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.app.id}"
    viewer_protocol_policy = "redirect-to-https"
    compress               = true

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  logging_config {
    include_cookies = false
    bucket          = aws_s3_bucket.logs.bucket_domain_name
    prefix          = "cloudfront/"
  }

  tags = { Name = "${var.project_name}-${var.environment}-cdn" }
}

# ─── SQS Queues ───────────────────────────────────────────────────────────────

resource "aws_sqs_queue" "dead_letter" {
  name                      = "${var.project_name}-${var.environment}-dlq"
  message_retention_seconds = 1209600  # 14 days
  kms_master_key_id         = var.kms_key_arn

  tags = { Name = "${var.project_name}-${var.environment}-dlq" }
}

resource "aws_sqs_queue" "main" {
  name                       = "${var.project_name}-${var.environment}-queue"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 86400
  kms_master_key_id          = var.kms_key_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 5
  })

  tags = { Name = "${var.project_name}-${var.environment}-queue" }
}

# ─── SNS Topic ────────────────────────────────────────────────────────────────

resource "aws_sns_topic" "alerts" {
  name              = "${var.project_name}-${var.environment}-alerts"
  kms_master_key_id = var.kms_key_arn

  tags = { Name = "${var.project_name}-${var.environment}-alerts" }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ─── ElastiCache (Redis) ──────────────────────────────────────────────────────

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-cache-subnet"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "${var.project_name}-${var.environment}-redis"
  description          = "Redis cache for ${var.project_name} ${var.environment}"

  node_type            = "cache.t3.micro"
  num_cache_clusters   = 2
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = var.cache_sg_ids

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  kms_key_id                 = var.kms_key_arn

  automatic_failover_enabled = true

  tags = { Name = "${var.project_name}-${var.environment}-redis" }
}
