output "db_endpoint"       { value = aws_rds_cluster.main.endpoint; sensitive = true }
output "db_reader_endpoint" { value = aws_rds_cluster.main.reader_endpoint; sensitive = true }
output "dynamodb_table_name" { value = aws_dynamodb_table.sessions.name }
