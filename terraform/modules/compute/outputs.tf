output "alb_dns_name"      { value = aws_lb.main.dns_name }
output "ecr_repository_url" { value = aws_ecr_repository.app.repository_url }
output "asg_name"           { value = aws_autoscaling_group.app.name }
output "lambda_arn"         { value = aws_lambda_function.worker.arn }
