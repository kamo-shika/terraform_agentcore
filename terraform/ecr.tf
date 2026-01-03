# ==============================================================================
# ECR Repository
# ==============================================================================
# エージェントのDockerイメージを格納するコンテナレジストリ
# プッシュ時に自動でイメージスキャンを実行してセキュリティ脆弱性を検出
resource "aws_ecr_repository" "main" {
  name                 = local.ecr_repository_name
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = local.common_tags
}

# ==============================================================================
# ECR Image Data Source
# ==============================================================================
# ECRイメージの最新ダイジェストを取得（参照用）
# イメージのダイジェストをoutputに出力してデプロイ履歴を追跡可能にする
data "aws_ecr_image" "latest" {
  repository_name = aws_ecr_repository.main.name
  image_tag       = "latest"

  # ECRリポジトリが作成された後、イメージがpushされるまでの間はエラーになるため
  # 初回デプロイ時はこのdata sourceをスキップする
  depends_on = [aws_ecr_repository.main]
}

# 注意: terraform_data.image_digest_triggerは削除済み
# 理由: replace_triggered_byによるdestroy→createではなく
# UpdateAgentRuntime APIによるin-place更新を使用するため
