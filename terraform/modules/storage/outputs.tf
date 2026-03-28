output "app_bucket_name"    { value = aws_s3_bucket.app.id }
output "app_bucket_arn"     { value = aws_s3_bucket.app.arn }
output "cloudfront_domain"  { value = aws_cloudfront_distribution.app.domain_name }
output "sqs_queue_url"      { value = aws_sqs_queue.main.id }
output "sns_topic_arn"      { value = aws_sns_topic.alerts.arn }
output "redis_endpoint"     { value = aws_elasticache_replication_group.redis.primary_endpoint_address }
