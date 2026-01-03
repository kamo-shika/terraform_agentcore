# ==============================================================================
# AgentCore Memory Observability設定
# ==============================================================================
# MemoryリソースのログとトレースをCloudWatch LogsおよびX-Rayに配信する

# ------------------------------------------------------------------------------
# CloudWatch Log Group（Memory APPLICATION_LOGS用）
# ------------------------------------------------------------------------------
# Memoryの抽出（Extraction）・統合（Consolidation）プロセスのログを保存
resource "aws_cloudwatch_log_group" "memory_logs" {
  name              = local.memory_log_group_name
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# ==============================================================================
# APPLICATION_LOGS配信設定
# ==============================================================================
# Memoryの処理ログをCloudWatch Logsに配信

# ログ配信ソース（APPLICATION_LOGS）
resource "aws_cloudwatch_log_delivery_source" "memory_logs" {
  name         = "${local.resource_prefix}-memory-logs-source"
  log_type     = "APPLICATION_LOGS"
  resource_arn = aws_bedrockagentcore_memory.main.arn

  tags = local.common_tags
}

# ログ配信先（CloudWatch Logs）
resource "aws_cloudwatch_log_delivery_destination" "memory_logs" {
  name = "${local.resource_prefix}-memory-logs-destination"

  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.memory_logs.arn
  }

  tags = local.common_tags
}

# ログ配信の接続（ソース → 配信先）
resource "aws_cloudwatch_log_delivery" "memory_logs" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.memory_logs.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.memory_logs.arn
}

# ==============================================================================
# TRACES配信設定
# ==============================================================================
# MemoryのトレースデータをX-Rayに配信
# CreateEvent, GetEvent, ListEvents, RetrieveMemoryRecordsなどのスパンデータ

# トレース配信ソース（TRACES）
resource "aws_cloudwatch_log_delivery_source" "memory_traces" {
  name         = "${local.resource_prefix}-memory-traces-source"
  log_type     = "TRACES"
  resource_arn = aws_bedrockagentcore_memory.main.arn

  tags = local.common_tags
}

# トレース配信先（X-Ray）
resource "aws_cloudwatch_log_delivery_destination" "memory_traces" {
  name                      = "${local.resource_prefix}-memory-traces-destination"
  delivery_destination_type = "XRAY"

  tags = local.common_tags
}

# トレース配信の接続（ソース → X-Ray）
resource "aws_cloudwatch_log_delivery" "memory_traces" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.memory_traces.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.memory_traces.arn
}
