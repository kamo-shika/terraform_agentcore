# ==============================================================================
# IAM Role for AgentCore
# ==============================================================================
# Bedrock AgentCoreが使用するIAMロール
# Bedrockモデル呼び出し、ECRイメージ取得、S3アクセスの権限を付与
resource "aws_iam_role" "agent_role" {
  name = local.agent_role_name

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

  tags = local.common_tags
}

# ==============================================================================
# IAM Policy: Bedrock Model Access
# ==============================================================================
# AgentCoreがBedrockモデルを呼び出すための最小権限ポリシー
# Claude Sonnetなどの基盤モデルを使用してエージェントを実行
resource "aws_iam_policy" "agent_bedrock_access" {
  name        = local.agent_bedrock_policy_name
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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_bedrock_access" {
  policy_arn = aws_iam_policy.agent_bedrock_access.arn
  role       = aws_iam_role.agent_role.name
}

# ==============================================================================
# IAM Policy: ECR Access
# ==============================================================================
# AgentCoreがECRからコンテナイメージを取得するためのポリシー
# エージェントの実行環境をECRから取得
resource "aws_iam_policy" "agent_ecr_access" {
  name        = local.agent_ecr_policy_name
  description = "AgentCoreがECRからイメージを取得するためのポリシー"

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

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_ecr_attach" {
  policy_arn = aws_iam_policy.agent_ecr_access.arn
  role       = aws_iam_role.agent_role.name
}

# ==============================================================================
# IAM Policy: S3 Access
# ==============================================================================
# AgentCoreがS3トリガーバケットにアクセスするためのポリシー
# S3に配置されたファイルを読み取ってエージェント処理を実行
resource "aws_iam_policy" "agent_s3_access" {
  name        = local.agent_s3_policy_name
  description = "AgentCoreがS3トリガーバケットから読み取るためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:HeadObject"
        ]
        Resource = "arn:aws:s3:::${local.trigger_bucket_name}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = "arn:aws:s3:::${local.trigger_bucket_name}"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_s3_attach" {
  policy_arn = aws_iam_policy.agent_s3_access.arn
  role       = aws_iam_role.agent_role.name
}

# ==============================================================================
# IAM Policy: AgentCore Memory Access
# ==============================================================================
# AgentCoreがMemoryにアクセスするためのポリシー
# セッション管理、イベント記録、ファクト取得などに必要
resource "aws_iam_policy" "agent_memory_access" {
  name        = "${var.project_name}-agent-memory-policy"
  description = "AgentCoreがMemoryにアクセスするためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          # イベント操作
          "bedrock-agentcore:CreateEvent",
          "bedrock-agentcore:GetEvent",
          "bedrock-agentcore:DeleteEvent",
          "bedrock-agentcore:ListEvents",
          # セッション・アクター操作
          "bedrock-agentcore:ListSessions",
          "bedrock-agentcore:ListActors",
          # メモリレコード操作（LTM/Semantic Memory）
          "bedrock-agentcore:ListMemoryRecords",
          "bedrock-agentcore:GetMemoryRecord",
          "bedrock-agentcore:RetrieveMemoryRecords",
          "bedrock-agentcore:BatchCreateMemoryRecords",
          "bedrock-agentcore:BatchUpdateMemoryRecords",
          "bedrock-agentcore:BatchDeleteMemoryRecords",
          "bedrock-agentcore:DeleteMemoryRecord"
        ]
        Resource = [
          aws_bedrockagentcore_memory.main.arn,
          "${aws_bedrockagentcore_memory.main.arn}/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_memory_attach" {
  policy_arn = aws_iam_policy.agent_memory_access.arn
  role       = aws_iam_role.agent_role.name
}

# ==============================================================================
# Data Sources
# ==============================================================================
# IAMポリシーでリージョンやアカウントIDを動的に取得するためのデータソース
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ==============================================================================
# IAM Policy: CloudWatch Logs Access
# ==============================================================================
# AgentCore RuntimeがCloudWatch Logsにログを出力するためのポリシー
# runtime-logs（コンテナのstdout/stderr）の出力に必要
# 参考: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html
resource "aws_iam_policy" "agent_logs_access" {
  name        = "${var.project_name}-agent-logs-policy"
  description = "AgentCore RuntimeがCloudWatch Logsにログを出力するためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CreateLogGroup"
        Effect = "Allow"
        Action = [
          "logs:DescribeLogStreams",
          "logs:CreateLogGroup"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*"
        ]
      },
      {
        Sid    = "DescribeLogGroups"
        Effect = "Allow"
        Action = [
          "logs:DescribeLogGroups"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:*"
        ]
      },
      {
        Sid    = "WriteLogEvents"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/aws/bedrock-agentcore/runtimes/*:log-stream:*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_logs_attach" {
  policy_arn = aws_iam_policy.agent_logs_access.arn
  role       = aws_iam_role.agent_role.name
}

# ==============================================================================
# IAM Policy: X-Ray Access
# ==============================================================================
# AgentCore RuntimeがX-Rayにトレースデータを送信するためのポリシー
# 分散トレーシングとパフォーマンス分析に必要
# 参考: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-permissions.html
resource "aws_iam_policy" "agent_xray_access" {
  name        = "${var.project_name}-agent-xray-policy"
  description = "AgentCore RuntimeがX-Rayにトレースを送信するためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "XRayAccess"
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "agent_xray_attach" {
  policy_arn = aws_iam_policy.agent_xray_access.arn
  role       = aws_iam_role.agent_role.name
}
