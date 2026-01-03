# 運用・動作確認ガイド

このドキュメントでは、ローカル環境からAgentCoreの動作確認を行う手順を説明します。

## 前提条件

- AWS CLIがインストール・設定済み
- AWS認証が有効（期限切れの場合は `aws login` を実行）
- Terraformでデプロイ済み（`make deploy` または `make deploy-init` 完了）

### 環境変数の確認

```bash
# Terraform出力から必要な情報を取得
cd terraform
terraform output

# 出力例:
# runtime_id = "agentcore_runtime-XXXXXXXXXX"
# memory_id = "agentcore_memory-XXXXXXXXXX"
# ecr_repository_url = "123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/agentcore-repo"
```

## エージェント直接呼び出し

AWS CLIを使用してAgentCore Runtimeを直接呼び出します。

### 基本的な呼び出し

```bash
# Runtime IDを取得
RUNTIME_ID=$(cd terraform && terraform output -raw runtime_id)

# エージェントを呼び出し（テキスト入力）
aws bedrock-agentcore-runtime invoke-agent-runtime \
    --agent-runtime-id $RUNTIME_ID \
    --agent-runtime-endpoint-name DEFAULT \
    --payload $(echo '{"input": {"text": "こんにちは、何ができますか？"}}' | base64) \
    --region ap-northeast-1 \
    output.json

# 結果を確認
cat output.json | jq -r '.response_payload' | base64 -d | jq .
```

### セッション付き呼び出し（会話の継続）

```bash
# セッションIDを指定して呼び出し
SESSION_ID="test-session-$(date +%s)"

aws bedrock-agentcore-runtime invoke-agent-runtime \
    --agent-runtime-id $RUNTIME_ID \
    --agent-runtime-endpoint-name DEFAULT \
    --session-id $SESSION_ID \
    --payload $(echo '{"input": {"text": "私の名前は田中です"}}' | base64) \
    --region ap-northeast-1 \
    output1.json

# 同じセッションで継続
aws bedrock-agentcore-runtime invoke-agent-runtime \
    --agent-runtime-id $RUNTIME_ID \
    --agent-runtime-endpoint-name DEFAULT \
    --session-id $SESSION_ID \
    --payload $(echo '{"input": {"text": "私の名前を覚えていますか？"}}' | base64) \
    --region ap-northeast-1 \
    output2.json
```

## S3トリガーによる呼び出し

S3バケットにファイルをアップロードしてLambda経由でエージェントを呼び出します。

### テストファイルのアップロード

```bash
# テストファイルを作成
echo "これはテストファイルです。内容を要約してください。" > /tmp/test_file.txt

# S3にアップロード（Lambda → AgentCore が起動）
aws s3 cp /tmp/test_file.txt s3://agentcore-trigger-bucket/test_file.txt

# アップロード確認
aws s3 ls s3://agentcore-trigger-bucket/
```

### Lambda実行ログの確認

```bash
# 最新のログストリームを取得
LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name /aws/lambda/agentcore-invoker \
    --order-by LastEventTime \
    --descending \
    --limit 1 \
    --query 'logStreams[0].logStreamName' \
    --output text \
    --region ap-northeast-1)

# ログを表示
aws logs get-log-events \
    --log-group-name /aws/lambda/agentcore-invoker \
    --log-stream-name "$LOG_STREAM" \
    --limit 50 \
    --region ap-northeast-1 \
    --query 'events[*].message' \
    --output text
```

## ログ・トレースの確認

### APPLICATION_LOGS（エージェントログ）

エージェントの標準出力・エラーログを確認します。

```bash
# ロググループ名
LOG_GROUP="/aws/vendedlogs/bedrock-agentcore/runtime/agentcore_runtime/APPLICATION_LOGS"

# 最新のログストリームを取得
LOG_STREAM=$(aws logs describe-log-streams \
    --log-group-name "$LOG_GROUP" \
    --order-by LastEventTime \
    --descending \
    --limit 1 \
    --query 'logStreams[0].logStreamName' \
    --output text \
    --region ap-northeast-1)

# ログを表示
aws logs get-log-events \
    --log-group-name "$LOG_GROUP" \
    --log-stream-name "$LOG_STREAM" \
    --limit 20 \
    --region ap-northeast-1 \
    --query 'events[*].message' \
    --output text
```

### USAGE_LOGS（リソース使用量）

セッションレベルのCPU/メモリ使用量を確認します。

```bash
LOG_GROUP="/aws/vendedlogs/bedrock-agentcore/runtime/agentcore_runtime/USAGE_LOGS"

# 最新のログを確認
aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --limit 10 \
    --region ap-northeast-1 \
    --query 'events[*].message' \
    --output text
```

### TRACES（X-Ray トレース）

X-Rayコンソールまたはログで確認します。

```bash
# X-Rayトレースログ
LOG_GROUP="aws/spans"

aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --filter-pattern "agentcore" \
    --limit 10 \
    --region ap-northeast-1 \
    --query 'events[*].message' \
    --output text
```

**AWSコンソールでの確認**:
1. CloudWatch > Settings > Traces で「Transaction Search」を有効化
2. CloudWatch > X-Ray traces > Traces で検索

### Memory ログ

```bash
LOG_GROUP="/aws/vendedlogs/bedrock-agentcore/agentcore_memory"

aws logs filter-log-events \
    --log-group-name "$LOG_GROUP" \
    --limit 10 \
    --region ap-northeast-1 \
    --query 'events[*].message' \
    --output text
```

## 長期メモリの確認

Semantic Memoryに保存されたレコードを確認します。

### メモリレコード一覧

```bash
MEMORY_ID=$(cd terraform && terraform output -raw memory_id)

# メモリレコードを一覧表示
aws bedrock-agentcore list-memory-records \
    --memory-id $MEMORY_ID \
    --region ap-northeast-1
```

### 特定のネームスペースのレコード

```bash
# ファイル要約が保存されるネームスペース
aws bedrock-agentcore list-memory-records \
    --memory-id $MEMORY_ID \
    --namespace "/file-summaries/anonymous" \
    --region ap-northeast-1
```

### メモリ検索

```bash
# セマンティック検索
aws bedrock-agentcore search-memory \
    --memory-id $MEMORY_ID \
    --query-text "テストファイルの内容" \
    --region ap-northeast-1
```

## Runtime・エンドポイントの状態確認

### Runtime情報

```bash
make get-runtime-info

# または直接実行
RUNTIME_ID=$(cd terraform && terraform output -raw runtime_id)
aws bedrock-agentcore-control get-agent-runtime \
    --agent-runtime-id $RUNTIME_ID \
    --region ap-northeast-1
```

### バージョン一覧

```bash
make list-versions
```

### エンドポイント一覧

```bash
make list-endpoints
```

## トラブルシューティング

### AWS認証エラー

```
Your session has expired. Please reauthenticate using 'aws login'
```

**解決方法**:
```bash
aws login
```

### Runtime IDが取得できない

```
Error: Could not get Runtime ID
```

**解決方法**:
```bash
# Terraformの状態を確認
cd terraform && terraform output

# 必要に応じて再デプロイ
make apply
```

### エージェントが応答しない

1. **Runtime状態を確認**
   ```bash
   make get-runtime-info
   ```
   ステータスが `ACTIVE` であることを確認

2. **APPLICATION_LOGSを確認**
   ```bash
   # エラーログを検索
   aws logs filter-log-events \
       --log-group-name "/aws/vendedlogs/bedrock-agentcore/runtime/agentcore_runtime/APPLICATION_LOGS" \
       --filter-pattern "ERROR" \
       --limit 20 \
       --region ap-northeast-1
   ```

3. **Lambdaログを確認**（S3トリガーの場合）
   ```bash
   aws logs filter-log-events \
       --log-group-name /aws/lambda/agentcore-invoker \
       --filter-pattern "ERROR" \
       --limit 20 \
       --region ap-northeast-1
   ```

### レスポンスがnull

AgentCore APPLICATION_LOGSの `response_payload` フィールドは現在CloudWatch Logsでは記録されません。
エージェントの応答内容を確認するには：

- **直接呼び出し**: 出力ファイル（`output.json`）を確認
- **S3トリガー**: S3出力ファイルまたはLambdaログで `Agent response:` を検索

## S3出力ファイルの確認

S3トリガー経由でエージェントを呼び出した場合、処理結果がS3に自動保存されます。

### 出力ファイル一覧

```bash
# 出力バケットの内容を確認
aws s3 ls s3://agentcore-trigger-bucket/outputs/
```

### 最新の出力ファイルを確認

```bash
# 最新の出力ファイルをダウンロードして表示
LATEST_OUTPUT=$(aws s3 ls s3://agentcore-trigger-bucket/outputs/ --recursive | sort | tail -n 1 | awk '{print $4}')

aws s3 cp "s3://agentcore-trigger-bucket/$LATEST_OUTPUT" - | jq .
```

### 出力ファイル形式

```json
{
  "timestamp": "2026-01-03T12:00:00Z",
  "session_id": "bucket_path_to_file",
  "actor_id": "user-id-from-metadata",
  "source": {
    "bucket": "agentcore-trigger-bucket",
    "key": "input/test.txt"
  },
  "input": "S3ファイルを処理してください: s3://...",
  "response": "エージェントからの応答テキスト"
}
```

### 特定のセッションの出力を検索

```bash
# セッションIDで検索
aws s3 ls s3://agentcore-trigger-bucket/outputs/ | grep "session-id"
```

## Actor状態の確認

エージェントが保存したActor状態を確認します。

### Actor状態レコード一覧

```bash
MEMORY_ID=$(cd terraform && terraform output -raw memory_id)

# 特定のActorの状態を確認
aws bedrock-agentcore list-memory-records \
    --memory-id $MEMORY_ID \
    --namespace "/actor-state/anonymous" \
    --region ap-northeast-1
```

### Actor状態の検索

```bash
# 直近の活動状態を検索
aws bedrock-agentcore search-memory \
    --memory-id $MEMORY_ID \
    --namespace "/actor-state/anonymous" \
    --query-text "直近の活動状態" \
    --region ap-northeast-1
```

## クイックリファレンス

| 操作 | コマンド |
|-----|---------|
| エージェント直接呼び出し | `aws bedrock-agentcore-runtime invoke-agent-runtime ...` |
| S3トリガーテスト | `aws s3 cp test.txt s3://agentcore-trigger-bucket/` |
| S3出力確認 | `aws s3 ls s3://agentcore-trigger-bucket/outputs/` |
| Runtime状態確認 | `make get-runtime-info` |
| バージョン確認 | `make list-versions` |
| APPLICATION_LOGS確認 | CloudWatch Logs `/aws/vendedlogs/bedrock-agentcore/runtime/agentcore_runtime/APPLICATION_LOGS` |
| Lambdaログ確認 | CloudWatch Logs `/aws/lambda/agentcore-invoker` |
| メモリレコード確認 | `aws bedrock-agentcore list-memory-records --memory-id $MEMORY_ID` |
| Actor状態確認 | `aws bedrock-agentcore list-memory-records --namespace "/actor-state/{actorId}" ...` |
| AWS再認証 | `aws login` |
