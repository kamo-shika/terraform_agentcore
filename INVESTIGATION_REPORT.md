# Issue #57: AgentCore Memoryの設定調査レポート

## 概要

Issue #55で実装したLTM（長期メモリー）統合が実際に機能しているか調査を行った。

## 最終結果

**Memory機能は正常に動作することを確認しました。**

| 項目 | 状態 | 詳細 |
|------|------|------|
| Docker ENV設定 | ✅ 正常 | `AGENTCORE_MEMORY_ID=agentcore_memory-OjUlsS2kwV` |
| Memory Strategy | ✅ 正常 | `FileSummaryExtractor` (SEMANTIC) ACTIVE |
| Namespace | ✅ 正常 | `/file-summaries/{actorId}` |
| Session Manager作成 | ✅ 正常 | `session_manager_created=True` 確認済み |
| Actorリスト | ✅ 正常 | `testuser001` がリストに追加されている |

## 発見された問題と修正

### 問題1: IAM権限不足

**エラー:**
```
AccessDeniedException: User: arn:aws:sts::457386253464:assumed-role/agentcore-agent-role/BedrockAgentCore-...
is not authorized to perform: bedrock-agentcore:ListEvents
on resource: arn:aws:bedrock-agentcore:ap-northeast-1:457386253464:memory/agentcore_memory-OjUlsS2kwV
```

**原因:** AgentCore RuntimeのIAMロール（`agentcore-agent-role`）にMemoryへのアクセス権限がなかった。

**修正:** `terraform/iam.tf` に Memory アクセス用の IAM ポリシーを追加

```hcl
resource "aws_iam_policy" "agent_memory_access" {
  name        = "${var.project_name}-agent-memory-policy"
  description = "AgentCoreがMemoryにアクセスするためのポリシー"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock-agentcore:CreateEvent",
          "bedrock-agentcore:GetEvent",
          "bedrock-agentcore:DeleteEvent",
          "bedrock-agentcore:ListEvents",
          "bedrock-agentcore:ListSessions",
          "bedrock-agentcore:ListActors",
          "bedrock-agentcore:ListMemoryRecords",
          "bedrock-agentcore:GetMemoryRecord",
          "bedrock-agentcore:BatchCreateMemoryRecords",
          "bedrock-agentcore:BatchUpdateMemoryRecords",
          "bedrock-agentcore:BatchDeleteMemoryRecords",
          "bedrock-agentcore:DeleteMemoryRecord"
        ]
        Resource = [
          aws_bedrockagentcore_memory.main.arn,
          "${aws_bedrockagentcore_memory.main.arn}/*"
        ]
      }
    ]
  })
}
```

### 問題2: sessionId/actorIdのフォーマット不正

**エラー:**
```
ValidationException: 2 validation errors detected:
- Value at 'actorId' failed to satisfy constraint: Member must satisfy regular expression pattern: [a-zA-Z0-9][a-zA-Z0-9-_/]*
- Value at 'sessionId' failed to satisfy constraint: Member must satisfy regular expression pattern: [a-zA-Z0-9][a-zA-Z0-9-_]*
```

**原因:**
- `sessionId` にドット（`.`）が含まれていた（例: `agentcore-trigger-bucket_test_file.txt`）
- `actorId` が英数字以外の文字で始まる可能性があった

**修正:** `lambda/invoker.py` にサニタイズ関数を追加

```python
def sanitize_session_id(value: str) -> str:
    """sessionIdをAgentCore Memory APIの正規表現パターンに準拠させる。"""
    sanitized = re.sub(r'[^a-zA-Z0-9-_]', '_', value)
    if sanitized and not sanitized[0].isalnum():
        sanitized = 's' + sanitized
    return sanitized or 'session'

def sanitize_actor_id(value: str) -> str:
    """actorIdをAgentCore Memory APIの正規表現パターンに準拠させる。"""
    sanitized = re.sub(r'[^a-zA-Z0-9-_/:]', '_', value)
    if sanitized and not sanitized[0].isalnum():
        sanitized = 'u' + sanitized
    return sanitized or 'anonymous'
```

## 調査手順

### 1. 環境変数の確認

```bash
docker inspect agentcore-repo:latest --format '{{range .Config.Env}}{{println .}}{{end}}'
# 結果: AGENTCORE_MEMORY_ID=agentcore_memory-OjUlsS2kwV, LTM_ENABLED=true
```

### 2. AgentCore Memory API調査

```bash
# Memoryの状態確認
aws bedrock-agentcore-control get-memory --memory-id agentcore_memory-OjUlsS2kwV --region ap-northeast-1
# 結果: ACTIVE, Strategy: FileSummaryExtractor (SEMANTIC)

# アクターリスト確認（修正後）
aws bedrock-agentcore list-actors --memory-id agentcore_memory-OjUlsS2kwV --region ap-northeast-1
# 結果:
# ACTORSUMMARIES	agent_default
# ACTORSUMMARIES	local-user
# ACTORSUMMARIES	session_agentcore-trigger-bucket_test_memory_v2_txt
# ACTORSUMMARIES	session_local-session-001
# ACTORSUMMARIES	testuser001
```

### 3. デバッグプロセス

1. `main.py`, `memory.py`, `server.py`, `agent.py` にデバッグログを追加
2. レスポンスにデバッグ情報を埋め込んでエラーを確認
3. IAM権限エラー → ポリシー追加
4. ValidationException → サニタイズ関数追加
5. 再テストで `session_manager_created=True` を確認

## 修正されたファイル

| ファイル | 変更内容 |
|---------|---------|
| `terraform/iam.tf` | Memory アクセス用 IAM ポリシー追加 |
| `lambda/invoker.py` | sessionId/actorId サニタイズ関数追加 |
| `app/main.py` | デバッグコード削除（クリーンアップ） |
| `app/memory.py` | デバッグコード削除（クリーンアップ） |
| `app/agent.py` | デバッグコード削除（クリーンアップ） |
| `app/server.py` | デバッグコード削除（クリーンアップ） |

## 検証結果

テスト実行結果: **89 passed**

```
======================== 89 passed, 3 warnings in 0.41s ========================
```

## 学んだこと

1. **AgentCore RuntimeのIAM権限**: Runtimeが使用するIAMロールには、Memoryへのアクセス権限を明示的に付与する必要がある
2. **ID形式の制約**: AgentCore Memory APIのsessionId/actorIdには厳密な正規表現パターンがあり、ドットなどの特殊文字は使用できない
3. **ログの可視性**: AgentCore Runtimeコンテナの内部ログはCloudWatchに直接出力されないため、レスポンスにデバッグ情報を埋め込む方法が有効

## 関連ファイル

- `terraform/iam.tf` - IAMポリシー定義
- `terraform/agentcore.tf` - Memory Strategy設定
- `lambda/invoker.py` - S3イベント処理とID生成
- `app/memory.py` - RetrievalConfig設定
- `app/main.py` - Memory初期化ロジック
