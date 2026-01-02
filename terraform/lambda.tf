# Lambda function to invoke AgentCore
# Note: Use ../build_lambda.sh to create lambda_function_payload.zip with dependencies
resource "aws_lambda_function" "invoker" {
  function_name = "${var.project_name}-invoker"
  role          = aws_iam_role.lambda_role.arn
  handler       = "invoker.lambda_handler"
  runtime       = "python3.12"
  filename      = "${path.module}/../lambda_function_payload.zip"
  timeout       = 300
  memory_size   = 512

  source_code_hash = filebase64sha256("${path.module}/../lambda_function_payload.zip")

  environment {
    variables = {
      AGENT_RUNTIME_ARN = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn
      AGENTCORE_MEMORY_ID   = aws_bedrockagentcore_memory.main.id
    }
  }

  tags = {
    Environment = "dev"
    Project     = var.project_name
    Purpose     = "AgentCore invoker"
  }
}

# Lambda permission to allow S3 to invoke the function
resource "aws_lambda_permission" "s3" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.invoker.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.trigger.arn
}

# IAM role for Lambda function
resource "aws_iam_role" "lambda_role" {
  name = "${var.project_name}-lambda-role"

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

  tags = {
    Environment = "dev"
    Project     = var.project_name
  }
}

# IAM policy for Lambda function
resource "aws_iam_policy" "lambda_policy" {
  name        = "${var.project_name}-lambda-policy"
  description = "Policy for Lambda to access S3, AgentCore, and CloudWatch Logs"

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
        Resource = "arn:aws:logs:${var.region}:*:log-group:/aws/lambda/${var.project_name}-invoker:*"
      }
    ]
  })
}

# Attach the policy to the Lambda role
resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  policy_arn = aws_iam_policy.lambda_policy.arn
  role       = aws_iam_role.lambda_role.name
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-invoker"
  retention_in_days = 7

  tags = {
    Environment = "dev"
    Project     = var.project_name
  }
}
