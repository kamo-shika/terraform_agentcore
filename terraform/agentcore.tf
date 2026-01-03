# ==============================================================================
# Bedrock AgentCore Runtime
# ==============================================================================
# エージェントのコンテナ実行環境を提供するリソース
# ECRからコンテナイメージを取得し、Bedrockモデルを使用してエージェントを実行する
# terraform_data.image_digest_triggerの変更でリソース更新がトリガーされる
resource "aws_bedrockagentcore_agent_runtime" "main" {
  agent_runtime_name = local.runtime_name
  role_arn           = aws_iam_role.agent_role.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.main.repository_url}:latest"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  tags = local.common_tags

  # イメージダイジェストが変わったらリソースを更新
  lifecycle {
    replace_triggered_by = [terraform_data.image_digest_trigger]
  }
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