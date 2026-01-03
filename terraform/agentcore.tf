# ==============================================================================
# Bedrock AgentCore Runtime
# ==============================================================================
# エージェントのコンテナ実行環境を提供するリソース
# ECRからコンテナイメージを取得し、Bedrockモデルを使用してエージェントを実行する
#
# バージョン管理:
# - container_uriの変更時はUpdateAgentRuntime APIでin-place更新される
# - 更新のたびに新しいバージョン（V1, V2, V3...）が自動作成される
# - バージョン履歴は保持され、ロールバック可能
# - DEFAULTエンドポイントは自動的に最新バージョンを指す
resource "aws_bedrockagentcore_agent_runtime" "main" {
  agent_runtime_name = local.runtime_name
  role_arn           = aws_iam_role.agent_role.arn

  agent_runtime_artifact {
    container_configuration {
      # 常に:latestタグを参照するが、Makefileでgit commit hashタグも付与される
      container_uri = "${aws_ecr_repository.main.repository_url}:latest"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  tags = local.common_tags

  # 注意: lifecycle.replace_triggered_byは使用しない
  # 理由: リソースをdestroy→createするとバージョン履歴が失われる
  # 代わりにcontainer_uriの変更でin-place更新（UpdateAgentRuntime API）を使用
}

# ==============================================================================
# Bedrock AgentCore Memory
# ==============================================================================
# エージェントの会話履歴やコンテキストを保持するメモリリソース
# セッション管理とイベント保持期間を設定
resource "aws_bedrockagentcore_memory" "main" {
  name                  = local.memory_name
  event_expiry_duration = var.memory_event_expiry_days

  tags = local.common_tags
}

# ==============================================================================
# Bedrock AgentCore Memory Strategy - Semantic (ファイル要約蓄積)
# ==============================================================================
# ファイル要約を長期メモリとして蓄積するためのSemantic Memory Strategy
# ユーザー（actorId）別にファイル要約を保存・取得する
resource "aws_bedrockagentcore_memory_strategy" "file_summary" {
  name        = "FileSummaryExtractor"
  memory_id   = aws_bedrockagentcore_memory.main.id
  type        = "SEMANTIC"
  namespaces  = ["/file-summaries/{actorId}"]
  description = "S3ファイル要約を蓄積し、過去の要約を統合した出力を可能にするSemantic Memory Strategy"
}

# ==============================================================================
# Bedrock AgentCore Runtime Endpoint - PROD
# ==============================================================================
# 本番環境用のカスタムエンドポイント
# DEFAULTエンドポイントとは異なり、特定バージョンを明示的に指定可能
#
# 使い方:
# - 初回作成時: 最新バージョン（V1）を指す
# - ロールバック時: `make rollback VERSION=V1` で特定バージョンに切り替え
# - バージョン確認: `make list-versions` でバージョン一覧を表示
#
# 注意: DEFAULTエンドポイントはAWSが自動作成・管理するため、
# Terraformでは管理しない（常に最新バージョンを指す）
resource "aws_bedrockagentcore_agent_runtime_endpoint" "prod" {
  count = var.enable_prod_endpoint ? 1 : 0

  agent_runtime_id = aws_bedrockagentcore_agent_runtime.main.agent_runtime_id
  name             = "PROD"
  description      = "Production endpoint - manually updated for controlled deployments"

  # 注意: agent_runtime_versionは初回作成時のみ指定
  # 以降のバージョン更新は `make rollback VERSION=VX` で実行
  # Terraformでバージョンを管理すると、apply時に意図しないバージョン変更が発生する可能性がある
}