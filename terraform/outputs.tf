# 出力値（ローカルテストや参照用）

output "memory_id" {
  value       = aws_bedrockagentcore_memory.main.id
  description = "AgentCore Memory ID（ローカルテスト用）"
}

output "runtime_arn" {
  value       = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn
  description = "AgentCore Runtime ARN"
}

output "runtime_id" {
  value       = aws_bedrockagentcore_agent_runtime.main.agent_runtime_id
  description = "AgentCore Runtime ID"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.main.repository_url
  description = "ECRリポジトリURL"
}

output "current_image_digest" {
  value       = data.aws_ecr_image.latest.image_digest
  description = "現在デプロイされているイメージのダイジェスト"
}

output "prod_endpoint_arn" {
  value       = var.enable_prod_endpoint ? aws_bedrockagentcore_agent_runtime_endpoint.prod[0].agent_runtime_endpoint_arn : null
  description = "PRODエンドポイントARN（enable_prod_endpoint=true時のみ）"
}
