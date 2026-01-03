# S3 Bucket for triggering AgentCore
resource "aws_s3_bucket" "trigger" {
  bucket = "${var.project_name}-trigger-bucket"

  tags = {
    Environment = var.environment
    Project     = var.project_name
    Purpose     = "AgentCore trigger bucket"
  }
}

# Enable versioning for the trigger bucket
resource "aws_s3_bucket_versioning" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Block public access to the trigger bucket
resource "aws_s3_bucket_public_access_block" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3バケットのサーバーサイド暗号化設定
resource "aws_s3_bucket_server_side_encryption_configuration" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket notification to trigger Lambda
resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.invoker.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = var.s3_trigger_suffix
  }

  depends_on = [aws_lambda_permission.s3]
}
