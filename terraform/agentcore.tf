# Agent Core Runtime Resource
# terraform_data.image_digest_triggerの変更でリソース更新がトリガーされる
resource "aws_bedrockagentcore_agent_runtime" "main" {
  agent_runtime_name = "${var.project_name}_runtime"
  role_arn           = aws_iam_role.agent_role.arn

  agent_runtime_artifact {
    container_configuration {
      container_uri = "${aws_ecr_repository.main.repository_url}:latest"
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  tags = {
    Environment = "dev"
    Project     = var.project_name
  }

  # イメージダイジェストが変わったらリソースを更新
  lifecycle {
    replace_triggered_by = [terraform_data.image_digest_trigger]
  }
}

# Agent Core Memory Resource
resource "aws_bedrockagentcore_memory" "main" {
  name                  = "${var.project_name}_memory"
  event_expiry_duration = 30
}