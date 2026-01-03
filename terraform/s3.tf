# ==============================================================================
# S3 Bucket: Trigger Bucket
# ==============================================================================
# AgentCoreを起動するトリガーとなるS3バケット
# ファイルがアップロードされるとLambda経由でAgentCoreが起動
resource "aws_s3_bucket" "trigger" {
  bucket = local.trigger_bucket_name

  tags = merge(local.common_tags, {
    Purpose = "AgentCore trigger bucket"
  })
}

# ==============================================================================
# S3 Bucket Versioning
# ==============================================================================
# トリガーバケットのバージョニングを有効化
# 誤削除や上書きからファイルを保護
resource "aws_s3_bucket_versioning" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ==============================================================================
# S3 Bucket Public Access Block
# ==============================================================================
# トリガーバケットへのパブリックアクセスをブロック
# セキュリティベストプラクティスに従い、すべてのパブリックアクセスを遮断
resource "aws_s3_bucket_public_access_block" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ==============================================================================
# S3 Bucket Server-Side Encryption
# ==============================================================================
# トリガーバケットのサーバーサイド暗号化設定
# AES256でデータを自動的に暗号化
resource "aws_s3_bucket_server_side_encryption_configuration" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ==============================================================================
# S3 Bucket Notification
# ==============================================================================
# S3バケットイベント通知設定
# 指定した拡張子のファイルが作成されるとLambda関数を起動
resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.trigger.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.invoker.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = var.s3_trigger_suffix
  }

  depends_on = [aws_lambda_permission.s3]
}
