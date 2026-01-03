# ==============================================================================
# Lambda Function: AgentCore Invoker
# ==============================================================================
# S3トリガーからAgentCoreを呼び出すLambda関数
# S3にファイルがアップロードされるとこのLambdaが起動し、AgentCoreを実行
# Note: ../build_lambda.sh でlambda_function_payload.zipを作成すること
resource "aws_lambda_function" "invoker" {
  function_name = local.lambda_function_name
  role          = aws_iam_role.lambda_role.arn
  handler       = "invoker.lambda_handler"
  runtime       = var.lambda_runtime
  filename      = "${path.module}/../lambda_function_payload.zip"
  timeout       = var.lambda_timeout_seconds
  memory_size   = var.lambda_memory_mb

  source_code_hash = filebase64sha256("${path.module}/../lambda_function_payload.zip")

  environment {
    variables = {
      AGENT_RUNTIME_ARN   = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn
      AGENTCORE_MEMORY_ID = aws_bedrockagentcore_memory.main.id
      OUTPUT_BUCKET       = aws_s3_bucket.trigger.bucket
    }
  }

  tags = merge(local.common_tags, {
    Purpose = "AgentCore invoker"
  })
}

# ==============================================================================
# Lambda Permission: S3 Trigger
# ==============================================================================
# S3バケットがLambda関数を呼び出すための権限
resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.invoker.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.trigger.arn
}

# ==============================================================================
# IAM Role for Lambda
# ==============================================================================
# Lambda関数が使用するIAMロール
# S3、AgentCore、CloudWatch Logsへのアクセス権限を付与
resource "aws_iam_role" "lambda_role" {
  name = local.lambda_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = local.common_tags
}

# ==============================================================================
# IAM Policy for Lambda
# ==============================================================================
# Lambda関数がS3、AgentCore、CloudWatch Logsにアクセスするためのポリシー
resource "aws_iam_policy" "lambda_policy" {
  name        = local.lambda_policy_name
  description = "Lambda関数がS3、AgentCore、CloudWatch Logsにアクセスするためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:HeadObject"
        ]
        Resource = "${aws_s3_bucket.trigger.arn}/*"
      },
      {
        # エージェント応答をS3に出力するための権限
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.trigger.arn}/outputs/*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:InvokeAgentRuntime"
        ]
        Resource = [
          aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn,
          "${aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.region}:*:log-group:${local.lambda_log_group_name}:*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  policy_arn = aws_iam_policy.lambda_policy.arn
  role       = aws_iam_role.lambda_role.name
}

# ==============================================================================
# CloudWatch Log Group for Lambda
# ==============================================================================
# Lambda関数のログを保存するCloudWatch Logsロググループ
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = local.lambda_log_group_name
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}
