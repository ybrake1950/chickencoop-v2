# Chicken Coop v2 - AWS Infrastructure
# Terraform configuration for all required AWS resources

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "production"
}

variable "coop_name" {
  description = "Name identifier for the chicken coop"
  type        = string
  default     = "chickencoop"
}

variable "alert_email" {
  description = "Email address for SNS alert notifications"
  type        = string
}

# =============================================================================
# S3 Bucket - Video and CSV Storage
# =============================================================================

resource "aws_s3_bucket" "coop_storage" {
  bucket = "${var.coop_name}-${var.environment}-storage"

  tags = {
    Name        = "${var.coop_name}-storage"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "coop_storage_versioning" {
  bucket = aws_s3_bucket.coop_storage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "coop_storage_sse" {
  bucket = aws_s3_bucket.coop_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "coop_storage_public_access_block" {
  bucket = aws_s3_bucket.coop_storage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "coop_storage_lifecycle" {
  bucket = aws_s3_bucket.coop_storage.id

  rule {
    id     = "video-expiration"
    status = "Enabled"

    filter {
      prefix = "videos/"
    }

    expiration {
      days = 120
    }
  }
}

# =============================================================================
# SNS Topic - Alert Notifications
# =============================================================================

resource "aws_sns_topic" "coop_alerts" {
  name = "${var.coop_name}-${var.environment}-alerts"

  tags = {
    Name        = "${var.coop_name}-alerts"
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email_alert" {
  topic_arn = aws_sns_topic.coop_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# =============================================================================
# IoT Core - Device Management
# =============================================================================

resource "aws_iot_thing" "coop_device" {
  name = "${var.coop_name}-${var.environment}-pi"

  attributes = {
    environment = var.environment
    device_type = "raspberry_pi_4"
  }
}

resource "aws_iot_policy" "coop_device_policy" {
  name = "${var.coop_name}-${var.environment}-device-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "iot:Connect"
        ]
        Resource = "arn:aws:iot:*:*:client/${var.coop_name}-${var.environment}-*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "iot:Publish",
          "iot:Subscribe",
          "iot:Receive"
        ]
        Resource = "arn:aws:iot:*:*:topic/${var.coop_name}/${var.environment}/*"
      }
    ]
  })
}

# =============================================================================
# DynamoDB - Command Queue
# =============================================================================

resource "aws_dynamodb_table" "command_queue" {
  name         = "${var.coop_name}-${var.environment}-commands"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "command_id"
  range_key    = "timestamp"

  attribute {
    name = "command_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Name        = "${var.coop_name}-commands"
    Environment = var.environment
  }
}

# =============================================================================
# IAM - Roles and Policies
# =============================================================================

resource "aws_iam_role" "coop_device_role" {
  name = "${var.coop_name}-${var.environment}-device-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "iot.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.coop_name}-device-role"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "coop_device_policy" {
  name = "${var.coop_name}-${var.environment}-device-policy"
  role = aws_iam_role.coop_device_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.coop_storage.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = aws_sns_topic.coop_alerts.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = aws_dynamodb_table.command_queue.arn
      }
    ]
  })
}
