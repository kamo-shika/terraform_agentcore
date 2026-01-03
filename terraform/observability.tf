# ==============================================================================
# AgentCore Observability設定
# ==============================================================================
# Memory・RuntimeリソースのログとトレースをCloudWatch LogsおよびX-Rayに配信する
#
# 参考: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/observability-configure.html

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

# ==============================================================================
# AgentCore Runtime Observability設定
# ==============================================================================
# RuntimeリソースのログとトレースをCloudWatch LogsおよびX-Rayに配信する
#
# ログタイプ:
# - APPLICATION_LOGS: エージェントの標準出力・エラーログ（デバッグ、エラー調査用）
# - USAGE_LOGS: セッションレベルのCPU/メモリ使用量ログ（コスト分析、リソース監視用）
# - TRACES: InvokeAgentRuntimeなどのスパンデータ（パフォーマンス分析、リクエストトレース用）

# ------------------------------------------------------------------------------
# CloudWatch Log Group（Runtime APPLICATION_LOGS用）
# ------------------------------------------------------------------------------
# エージェントの標準出力・エラーログを保存
resource "aws_cloudwatch_log_group" "runtime_app_logs" {
  name              = local.runtime_app_log_group_name
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# ログ配信ソース（APPLICATION_LOGS）
resource "aws_cloudwatch_log_delivery_source" "runtime_app_logs" {
  name         = "${local.resource_prefix}-runtime-app-logs-source"
  log_type     = "APPLICATION_LOGS"
  resource_arn = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn

  tags = local.common_tags
}

# ログ配信先（CloudWatch Logs）
resource "aws_cloudwatch_log_delivery_destination" "runtime_app_logs" {
  name = "${local.resource_prefix}-runtime-app-logs-destination"

  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.runtime_app_logs.arn
  }

  tags = local.common_tags
}

# ログ配信の接続（ソース → 配信先）
resource "aws_cloudwatch_log_delivery" "runtime_app_logs" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.runtime_app_logs.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.runtime_app_logs.arn
}

# ------------------------------------------------------------------------------
# CloudWatch Log Group（Runtime USAGE_LOGS用）
# ------------------------------------------------------------------------------
# セッションレベルのCPU/メモリ使用量ログを保存
resource "aws_cloudwatch_log_group" "runtime_usage_logs" {
  name              = local.runtime_usage_log_group_name
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

# ログ配信ソース（USAGE_LOGS）
resource "aws_cloudwatch_log_delivery_source" "runtime_usage_logs" {
  name         = "${local.resource_prefix}-runtime-usage-logs-source"
  log_type     = "USAGE_LOGS"
  resource_arn = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn

  tags = local.common_tags
}

# ログ配信先（CloudWatch Logs）
resource "aws_cloudwatch_log_delivery_destination" "runtime_usage_logs" {
  name = "${local.resource_prefix}-runtime-usage-logs-destination"

  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.runtime_usage_logs.arn
  }

  tags = local.common_tags
}

# ログ配信の接続（ソース → 配信先）
resource "aws_cloudwatch_log_delivery" "runtime_usage_logs" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.runtime_usage_logs.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.runtime_usage_logs.arn
}

# ------------------------------------------------------------------------------
# Runtime TRACES配信設定
# ------------------------------------------------------------------------------
# RuntimeのトレースデータをX-Rayに配信
# InvokeAgentRuntimeなどのスパンデータ

# トレース配信ソース（TRACES）
resource "aws_cloudwatch_log_delivery_source" "runtime_traces" {
  name         = "${local.resource_prefix}-runtime-traces-source"
  log_type     = "TRACES"
  resource_arn = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn

  tags = local.common_tags
}

# トレース配信先（X-Ray）
# MemoryとRuntimeで同じX-Ray配信先を共有可能だが、
# 管理の明確化のため個別に定義
resource "aws_cloudwatch_log_delivery_destination" "runtime_traces" {
  name                      = "${local.resource_prefix}-runtime-traces-destination"
  delivery_destination_type = "XRAY"

  tags = local.common_tags
}

# トレース配信の接続（ソース → X-Ray）
resource "aws_cloudwatch_log_delivery" "runtime_traces" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.runtime_traces.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.runtime_traces.arn
}
