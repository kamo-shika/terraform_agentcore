resource "aws_iam_role" "agent_role" {
  name = "${var.project_name}-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock-agentcore.amazonaws.com"
        }
      }
    ]
  })
}

# AgentCoreがBedrockモデルを呼び出すための最小権限ポリシー
resource "aws_iam_policy" "agent_bedrock_access" {
  name        = "${var.project_name}-agent-bedrock-policy"
  description = "最小権限でAgentCoreがBedrockモデルを呼び出すためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "agent_bedrock_access" {
  policy_arn = aws_iam_policy.agent_bedrock_access.arn
  role       = aws_iam_role.agent_role.name
}

resource "aws_iam_policy" "agent_ecr_access" {
  name        = "${var.project_name}-agent-ecr-policy"
  description = "Allow Bedrock Agent to pull images from ECR"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "agent_ecr_attach" {
  policy_arn = aws_iam_policy.agent_ecr_access.arn
  role       = aws_iam_role.agent_role.name
}

# Policy to allow AgentCore to access S3 trigger bucket
resource "aws_iam_policy" "agent_s3_access" {
  name        = "${var.project_name}-agent-s3-policy"
  description = "Allow AgentCore to read from S3 trigger bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:HeadObject"
        ]
        Resource = "arn:aws:s3:::${var.project_name}-trigger-bucket/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${var.project_name}-trigger-bucket"
      }
    ]
  })
}

# Attach S3 access policy to AgentCore role
resource "aws_iam_role_policy_attachment" "agent_s3_attach" {
  policy_arn = aws_iam_policy.agent_s3_access.arn
  role       = aws_iam_role.agent_role.name
}
