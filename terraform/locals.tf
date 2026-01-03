# ローカル変数定義
# 共通タグやリソース命名パターンを定義

locals {
  # 全リソースに適用する共通タグ
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  # リソース命名パターン
  # 命名規則: ${project_name}-{resource-type}-{purpose}
  resource_prefix = var.project_name

  # ECRリポジトリ名
  ecr_repository_name = "${local.resource_prefix}-repo"

  # IAMロール名
  agent_role_name  = "${local.resource_prefix}-agent-role"
  lambda_role_name = "${local.resource_prefix}-lambda-role"

  # IAMポリシー名
  agent_bedrock_policy_name = "${local.resource_prefix}-agent-bedrock-policy"
  agent_ecr_policy_name     = "${local.resource_prefix}-agent-ecr-policy"
  agent_s3_policy_name      = "${local.resource_prefix}-agent-s3-policy"
  lambda_policy_name        = "${local.resource_prefix}-lambda-policy"

  # AgentCore リソース名
  runtime_name = "${local.resource_prefix}_runtime"
  memory_name  = "${local.resource_prefix}_memory"

  # Lambda関数名
  lambda_function_name = "${local.resource_prefix}-invoker"

  # S3バケット名
  trigger_bucket_name = "${local.resource_prefix}-trigger-bucket"

  # CloudWatch Logs
  lambda_log_group_name = "/aws/lambda/${local.lambda_function_name}"

  # Memory Observability
  # vendedlogsプレフィックスはAWSのマネージドサービスログ用の標準パス
  memory_log_group_name = "/aws/vendedlogs/bedrock-agentcore/${local.memory_name}"
}
