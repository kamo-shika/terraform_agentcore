resource "aws_ecr_repository" "main" {
  name                 = "${var.project_name}-repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECRイメージの最新ダイジェストを取得
# :latestタグの中身が変わった場合にTerraformが変更を検知できるようにする
data "aws_ecr_image" "latest" {
  repository_name = aws_ecr_repository.main.name
  image_tag       = "latest"

  # ECRリポジトリが作成された後、イメージがpushされるまでの間はエラーになるため
  # 初回デプロイ時はこのdata sourceをスキップする
  depends_on = [aws_ecr_repository.main]
}

# イメージダイジェストの変更を追跡するためのリソース
# ダイジェストが変わるとAgentCore Runtimeの更新がトリガーされる
resource "terraform_data" "image_digest_trigger" {
  input = data.aws_ecr_image.latest.image_digest
}
