# Outputs for local testing and reference

output "memory_id" {
  value       = aws_bedrockagentcore_memory.main.id
  description = "AgentCore Memory ID for local testing"
}

output "runtime_arn" {
  value       = aws_bedrockagentcore_agent_runtime.main.arn
  description = "AgentCore Runtime ARN"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.main.repository_url
  description = "ECR Repository URL"
}
