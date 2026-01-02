# AgentCore S3統合プロジェクト進捗レポート

**日付**: 2026-01-02
**ステータス**: Lambda統合完了、AgentCore Runtime調整中

---

## 📋 プロジェクト概要

S3 PUTイベントをトリガーとしてBedrock AgentCoreエージェントを起動し、アップロードされたファイルを自動処理・要約するシステムの実装。

### 主要機能
- ✅ S3イベント駆動型のエージェント起動
- ✅ ユーザーごとの長期記憶（AgentCore Memory）
- ✅ 外部プロンプト管理システム
- ⚠️  S3ファイル読み取りと要約（実装済み、動作確認中）

---

## 🎯 実装完了項目

### Issue #1: Terraformインフラストラクチャ (PR #6)
**ステータス**: ✅ 完了・マージ済み

**実装内容**:
- `terraform/s3.tf`: S3トリガーバケットとイベント通知設定
- `terraform/lambda.tf`: Lambda関数、IAMロール、権限
- `terraform/iam.tf`: AgentCore用S3アクセスポリシー

**主要リソース**:
```hcl
resource "aws_s3_bucket" "trigger" {
  bucket = "agentcore-trigger-bucket"
  # .txtファイルのPUTイベントでLambdaをトリガー
}

resource "aws_lambda_function" "invoker" {
  function_name = "agentcore-invoker"
  runtime       = "python3.12"
  timeout       = 300
  memory_size   = 512
}
```

---

### Issue #2: Lambda Invoker (PR #7)
**ステータス**: ✅ 完了・マージ済み

**実装内容**: `lambda/invoker.py`
- S3イベント処理とメタデータ抽出
- AgentCore Runtime APIの呼び出し
- ストリーミングレスポンス処理

**重要な修正**:
```python
# boto3クライアント (修正後)
bedrock_agentcore = boto3.client('bedrock-agentcore')

# API呼び出しパラメータ
response = bedrock_agentcore.invoke_agent_runtime(
    agentRuntimeArn=agent_runtime_arn,
    runtimeSessionId=session_id,  # sessionId → runtimeSessionId
    payload=json.dumps(payload).encode('utf-8')  # inputPayload → payload
)
```

**フロー**:
```
S3 PUT event
  ↓
Lambda: S3メタデータからuser-id抽出
  ↓
sessionId = "{bucket}/{key}" (ファイルパスベース)
actorId = user-id (メタデータから)
  ↓
AgentCore Runtime呼び出し
```

---

### Issue #3: プロンプト管理システム (PR #8)
**ステータス**: ✅ 完了・マージ済み

**実装内容**:
- `app/prompts/loader.py`: プロンプト読み込みユーティリティ
- `app/prompts/__init__.py`: モジュールエクスポート
- `app/prompts/summarize.txt`: S3ファイル要約用プロンプト

**使用例**:
```python
from app.prompts import load_prompt

# 変数置換してプロンプトを読み込む
prompt = load_prompt(
    "summarize",
    bucket="my-bucket",
    key="file.txt",
    user_id="user123"
)
```

**プロンプト構造**:
```
あなたはファイル内容を要約するアシスタントです。

## 出力形式
1. **概要**: ファイルの主な内容を1-2文で説明
2. **主要ポイント**: 重要な情報を箇条書きで3-5個
3. **キーワード**: 関連するキーワードを5個以内

## ファイル情報
- バケット: {bucket}
- キー: {key}
- ユーザーID: {user_id}
```

---

### Issue #4: AgentCoreアプリ統合 (PR #9)
**ステータス**: ✅ 完了・マージ済み

**実装内容**:
- `app/agent.py`: `use_aws`ツールを追加、カスタムプロンプト対応
- `app/main.py`: S3イベント処理とプロンプト統合

**エージェント設定**:
```python
from strands import Agent
from strands_tools import use_aws

agent = Agent(
    name="S3FileProcessingAgent",
    model="jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
    system_prompt=loaded_prompt,  # 外部プロンプト
    tools=[use_aws],  # S3ファイル読み取り
    session_manager=session_manager  # AgentCore Memory
)
```

---

## 🔧 デプロイと修正履歴

### boto3バージョン更新
**問題**: Lambda環境のboto3が`bedrock-agentcore`クライアントに非対応
**解決策**:
- `lambda/requirements.txt`: boto3を1.34.0 → 1.42.19に更新
- `build_lambda.sh`: 依存関係を含むデプロイパッケージ作成スクリプト

```bash
#!/bin/bash
# lambda/以下の依存関係をインストールしてzipパッケージ作成
uv pip install -r lambda/requirements.txt --target lambda_build --python-version 3.12
cp lambda/*.py lambda_build/
cd lambda_build && zip -r ../lambda_function_payload.zip .
```

### IAM権限修正
**問題**: Lambda関数がAgentCore Runtimeを呼び出せない
**解決策**: `terraform/lambda.tf`のIAMポリシー修正

```hcl
# 修正前
Action = ["bedrock-agent-runtime:InvokeAgentRuntime"]
Resource = aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn

# 修正後
Action = ["bedrock-agentcore:InvokeAgentRuntime"]
Resource = [
  aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn,
  "${aws_bedrockagentcore_agent_runtime.main.agent_runtime_arn}/*"
]
```

**理由**:
- サービス名が`bedrock-agent-runtime` → `bedrock-agentcore`
- リソースARNに`/runtime-endpoint/DEFAULT`サフィックスが追加されるためワイルドカードが必要

---

## 🧪 テスト結果

### 成功した統合テスト

#### 1. S3 → Lambda トリガー
```bash
aws s3 cp test.txt s3://agentcore-trigger-bucket/test.txt \
  --metadata user-id=test-user-001
```

**結果**: ✅ Lambda関数が正常にトリガーされた

**ログ出力**:
```
Processing S3 event: ObjectCreated:Put - s3://agentcore-trigger-bucket/test.txt
User ID from metadata: test-user-001
Session ID: agentcore-trigger-bucket_test.txt
```

#### 2. Lambda → AgentCore API呼び出し
**結果**: ✅ IAM権限が正しく設定され、API呼び出しに成功

**ログ出力**:
```
Invoking agent runtime: arn:aws:bedrock-agentcore:ap-northeast-1:457386253464:runtime/agentcore_runtime-0ni0OrGfCU
Payload: {
  "input": {"text": "S3ファイルを処理してください: s3://..."},
  "s3_info": {"bucket": "agentcore-trigger-bucket", "key": "test.txt"},
  "sessionId": "agentcore-trigger-bucket_test.txt",
  "actorId": "test-user-001"
}
```

### 現在の問題

#### AgentCore Runtime: 502 Bad Gateway
**エラーメッセージ**:
```
RuntimeClientError: Received error (502) from runtime.
Please check your CloudWatch logs for more information.
```

**実行時間**: 約60秒後にタイムアウト

**根本原因**: DockerコンテナがAgentCore要件を満たしていない

**現在の設定** (`Dockerfile`):
```dockerfile
CMD ["main.handler"]  # Lambda形式（誤り）
```

**必要な設定**:
- ポート8080でHTTPサーバーを公開
- `/invocations` POST エンドポイント
- `/ping` GET エンドポイント

---

## 📊 アーキテクチャ全体図

```
┌─────────────────────────────────────────────────────────────┐
│                    S3 Trigger Bucket                         │
│  agentcore-trigger-bucket                                    │
│  - Event: ObjectCreated:* (*.txt)                            │
│  - Metadata: x-amz-meta-user-id                              │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ S3 Event Notification
                     ↓
┌─────────────────────────────────────────────────────────────┐
│              Lambda Function: agentcore-invoker              │
│  Runtime: Python 3.12 | Timeout: 300s | Memory: 512MB       │
│                                                              │
│  1. S3イベント受信                                            │
│  2. s3_client.head_object() → user-id抽出                    │
│  3. sessionId = "{bucket}/{key}"                             │
│  4. bedrock_agentcore.invoke_agent_runtime()                 │
│     - agentRuntimeArn: AgentCore Runtime ARN                 │
│     - runtimeSessionId: セッションID                          │
│     - payload: {input, s3_info, sessionId, actorId}          │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ InvokeAgentRuntime API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│           Bedrock AgentCore Runtime ⚠️ 502エラー             │
│  ARN: agentcore_runtime-0ni0OrGfCU                          │
│                                                              │
│  Container (ECR):                                            │
│  - Image: 457386253464.dkr.ecr.ap-northeast-1/agentcore-repo│
│  - Tag: latest                                               │
│  - 問題: HTTPサーバー未実装                                   │
│                                                              │
│  Expected (未実装):                                          │
│  - Port: 8080                                                │
│  - POST /invocations                                         │
│  - GET /ping                                                 │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ (修正後に有効化)
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                 Strands Agent                                │
│  - Model: Claude Sonnet 4.5 (jp endpoint)                   │
│  - Tools: use_aws (S3操作)                                   │
│  - System Prompt: app/prompts/summarize.txt                 │
│                                                              │
│  処理フロー:                                                  │
│  1. S3ファイル読み取り (use_aws tool)                         │
│  2. 内容を要約                                                │
│  3. レスポンス返却                                            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Memory API
                     ↓
┌─────────────────────────────────────────────────────────────┐
│            Bedrock AgentCore Memory                          │
│  ID: agentcore_memory-OjUlsS2kwV                            │
│  - sessionId ベースの会話履歴                                 │
│  - actorId ベースのユーザー識別                               │
│  - イベント保持期間: 30日                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 デプロイ済みリソース

### AWS リソース一覧

| リソース種別 | 名前/ARN | ステータス |
|------------|---------|----------|
| S3 Bucket | `agentcore-trigger-bucket` | ✅ 動作中 |
| Lambda Function | `agentcore-invoker` | ✅ 動作中 |
| ECR Repository | `agentcore-repo` | ✅ イメージあり |
| AgentCore Runtime | `agentcore_runtime-0ni0OrGfCU` | ⚠️ 502エラー |
| AgentCore Memory | `agentcore_memory-OjUlsS2kwV` | ✅ 作成済み |
| IAM Role (Lambda) | `agentcore-lambda-role` | ✅ 権限OK |
| IAM Role (Agent) | `agentcore-agent-role` | ✅ 権限OK |

### Terraform Outputs
```hcl
ecr_repository_url = "457386253464.dkr.ecr.ap-northeast-1.amazonaws.com/agentcore-repo"
memory_id          = "agentcore_memory-OjUlsS2kwV"
runtime_arn        = "arn:aws:bedrock-agentcore:ap-northeast-1:457386253464:runtime/agentcore_runtime-0ni0OrGfCU"
```

---

## 🐛 トラブルシューティング履歴

### 1. Docker コマンド未検出
**問題**: `docker: command not found`
**原因**: Rancher Desktop使用、~/.rd/binがPATHに含まれていない
**解決**: `export PATH="$HOME/.rd/bin:$PATH"`

### 2. Terraform Handler Not Found
**問題**: `Handler 'lambda_handler' missing on module 'invoker'`
**原因**: Terraformがプレースホルダーコードを使用
**解決**: `data.archive_file`を実際のlambdaディレクトリ参照に変更

### 3. boto3 UnknownServiceError
**問題**: `Unknown service: 'bedrock-agentcore-runtime'`
**原因**: boto3 1.34.0が古く、AgentCore APIに非対応
**解決**: boto3を1.42.19に更新、依存関係をLambdaパッケージに同梱

### 4. boto3 クライアント名誤り
**問題**: `bedrock-agentcore-runtime`クライアントが存在しない
**原因**: 正しいクライアント名は`bedrock-agentcore`
**解決**: `boto3.client('bedrock-agentcore')`に修正

### 5. IAM AccessDeniedException
**問題**: `not authorized to perform: bedrock-agentcore:InvokeAgentRuntime`
**原因**:
- アクション名が`bedrock-agent-runtime:*`（誤）
- リソースARNにワイルドカードなし

**解決**:
```hcl
Action = ["bedrock-agentcore:InvokeAgentRuntime"]
Resource = [
  "arn:aws:bedrock-agentcore:...:runtime/agentcore_runtime-0ni0OrGfCU",
  "arn:aws:bedrock-agentcore:...:runtime/agentcore_runtime-0ni0OrGfCU/*"
]
```

### 6. AgentCore Runtime 502 Error (現在の課題)
**問題**: `RuntimeClientError: Received error (502) from runtime`
**原因**: DockerコンテナがLambda形式（`CMD ["main.handler"]`）でHTTPサーバー未実装
**次のステップ**:
- Dockerfileを修正してHTTPサーバー実装
- `/invocations`と`/ping`エンドポイント追加
- ポート8080公開

---

## 📝 次のアクションアイテム

### 優先度: 高 🔴

#### 1. AgentCore RuntimeコンテナをHTTPサーバーモードに修正
**ファイル**: `Dockerfile`, `app/main.py` または新規サーバーファイル

**必要な変更**:
```dockerfile
# Dockerfileの例
FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /var/task
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
ENV PATH="/var/task/.venv/bin:$PATH"

COPY app/ .

# HTTPサーバーを起動 (bedrock-agentcore-starter-toolkitまたはカスタム実装)
EXPOSE 8080
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
```

**参考**: [AWS AgentCore Get Started Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html)

#### 2. Observability有効化
**目的**: AgentCore Runtimeのログを確認可能にする

**設定方法**:
```bash
# AWS CLIまたはConsoleで有効化
aws bedrock-agentcore update-agent-runtime \
  --agent-runtime-id agentcore_runtime-0ni0OrGfCU \
  --enable-observability
```

#### 3. エンドツーエンドテスト
**テストシナリオ**:
1. S3に.txtファイルをアップロード（user-idメタデータ付き）
2. Lambda実行ログ確認
3. AgentCore Runtime実行ログ確認
4. エージェントレスポンス検証
5. Memory統合確認（同じsessionIdで再実行）

---

## 📚 参考リソース

### AWS Documentation
- [Bedrock AgentCore Runtime - Invoke Agent](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-invoke-agent.html)
- [AgentCore Get Started Guide](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-get-started-toolkit.html)
- [AgentCore Container Requirements](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime-troubleshooting.html)

### Strands Agents
- [GitHub: strands-agents/tools](https://github.com/strands-agents/tools)
- [use_aws Tool Documentation](https://github.com/strands-agents/tools#aws-operations)

### Project Files
- `CLAUDE.md`: プロジェクトガイダンス
- `README.md`: 使用方法とデプロイ手順
- `Makefile`: デプロイコマンド一覧

---

## 🎯 目標と成果

### 完了した目標 ✅
- [x] S3イベントトリガーでAgentCore起動
- [x] ユーザーごとの長期記憶（Memory統合）
- [x] 外部プロンプト管理
- [x] Lambda → AgentCore API統合
- [x] IAM権限の正確な設定
- [x] boto3最新版対応

### 残りのタスク ⚠️
- [ ] AgentCore RuntimeコンテナのHTTPサーバー化
- [ ] Observability有効化とログ確認
- [ ] エンドツーエンドの動作確認
- [ ] S3ファイル読み取りと要約の実動作テスト

---

## 💡 学んだこと

### 1. AgentCore Runtime vs Bedrock Agents
- **AgentCore**: コンテナベース、HTTPサーバー必須、boto3クライアント名は`bedrock-agentcore`
- **Bedrock Agents**: マネージド、boto3クライアント名は`bedrock-agent-runtime`

### 2. boto3バージョン管理の重要性
- Lambda標準環境のboto3は最新APIに非対応
- 依存関係を明示的にパッケージに含める必要あり
- `uv pip install --target`で依存関係を同梱

### 3. IAM権限の細かい要件
- サービス名: `bedrock-agentcore` (ハイフンの位置重要)
- リソースARN: 基本ARNとワイルドカード両方必要
- `/runtime-endpoint/DEFAULT`サフィックスが動的に追加される

### 4. Rancher Desktop環境
- Dockerコマンドは`~/.rd/bin/`に配置
- PATHに追加が必要: `export PATH="$HOME/.rd/bin:$PATH"`

---

**生成日時**: 2026-01-02 19:34 JST
**作成者**: Claude Code (claude.ai/code)
**プロジェクト**: terraform_agentcore
