variable "project_name" {
  description = "プロジェクト名（リソース命名に使用）"
  type        = string
  default     = "agentcore"
}

variable "region" {
  description = "AWSリージョン"
  type        = string
  default     = "ap-northeast-1"
}

variable "environment" {
  description = "環境名（dev, stg, prdなど）"
  type        = string
  default     = "dev"
}

variable "lambda_runtime" {
  description = "Lambda関数のランタイムバージョン"
  type        = string
  default     = "python3.12"
}

variable "lambda_timeout_seconds" {
  description = "Lambda関数のタイムアウト時間（秒）"
  type        = number
  default     = 300
}

variable "lambda_memory_mb" {
  description = "Lambda関数のメモリサイズ（MB）"
  type        = number
  default     = 512
}

variable "log_retention_days" {
  description = "CloudWatch Logsの保持期間（日数）"
  type        = number
  default     = 7
}

variable "memory_event_expiry_days" {
  description = "AgentCore Memoryのイベント保持期間（日数）"
  type        = number
  default     = 30
}

variable "s3_trigger_suffix" {
  description = "S3バケットのトリガー対象ファイルの拡張子"
  type        = string
  default     = ".txt"
}
