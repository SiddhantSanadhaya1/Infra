# ─── RDS Aurora PostgreSQL ────────────────────────────────────────────────────

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.private_subnet_ids

  tags = { Name = "${var.project_name}-${var.environment}-db-subnet" }
}

resource "aws_rds_cluster" "main" {
  cluster_identifier     = "${var.project_name}-${var.environment}-cluster"
  engine                 = "aurora-postgresql"
  engine_version         = "15.4"
  database_name          = var.db_name
  master_username        = var.db_username
  manage_master_user_password = true
  master_user_secret_kms_key_id = var.kms_key_arn

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.db_sg_id]

  storage_encrypted = true
  kms_key_id        = var.kms_key_arn

  backup_retention_period = 7
  preferred_backup_window = "03:00-04:00"
  skip_final_snapshot     = false
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final"

  enabled_cloudwatch_logs_exports = ["postgresql"]

  deletion_protection = var.environment == "prod" ? true : false

  tags = { Name = "${var.project_name}-${var.environment}-aurora" }
}

resource "aws_rds_cluster_instance" "main" {
  count = var.environment == "prod" ? 2 : 1

  identifier         = "${var.project_name}-${var.environment}-instance-${count.index + 1}"
  cluster_identifier = aws_rds_cluster.main.id
  instance_class     = var.db_instance_class
  engine             = aws_rds_cluster.main.engine
  engine_version     = aws_rds_cluster.main.engine_version

  monitoring_interval = 60
  monitoring_role_arn = aws_iam_role.rds_monitoring.arn

  performance_insights_enabled          = true
  performance_insights_kms_key_id       = var.kms_key_arn
  performance_insights_retention_period = 7

  tags = { Name = "${var.project_name}-${var.environment}-aurora-${count.index + 1}" }
}

# ─── Enhanced Monitoring Role ─────────────────────────────────────────────────

resource "aws_iam_role" "rds_monitoring" {
  name = "${var.project_name}-${var.environment}-rds-monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "monitoring.rds.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# ─── DynamoDB — Session Store ──────────────────────────────────────────────────

resource "aws_dynamodb_table" "sessions" {
  name           = "${var.project_name}-${var.environment}-sessions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled     = true
    kms_key_arn = var.kms_key_arn
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = { Name = "${var.project_name}-${var.environment}-sessions" }
}
