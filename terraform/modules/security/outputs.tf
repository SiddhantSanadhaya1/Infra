output "kms_key_arn"             { value = aws_kms_key.main.arn }
output "alb_security_group_id"  { value = aws_security_group.alb.id }
output "app_security_group_id"  { value = aws_security_group.app.id }
output "db_security_group_id"   { value = aws_security_group.db.id }
output "app_instance_profile"   { value = aws_iam_instance_profile.app.name }
output "db_secret_arn"          { value = aws_secretsmanager_secret.db_credentials.arn }
