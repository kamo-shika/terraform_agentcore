# アーキテクチャ

このドキュメントでは、プロジェクトのアーキテクチャについて説明します。

## システム構成図

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   S3 Bucket     │────▶│     Lambda      │────▶│ AgentCore       │
│  (トリガー)      │     │   (Invoker)     │     │  Runtime        │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                │                        │
                                │                        ▼
                                │              ┌─────────────────┐
                                │              │ Strands Agent   │
                                │              │ (Docker/ECR)    │
                                │              └────────┬────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐     ┌─────────────────┐
                       │   S3 Bucket     │     │ AgentCore       │
                       │  (出力保存)     │     │   Memory        │
                       └─────────────────┘     └─────────────────┘
```

## コンポーネント

### AgentCore Runtime

AWSが提供するマネージドエージェントホスティングサービス。

- ECRからコンテナイメージを取得して実行
- エンドポイントを通じてエージェントを呼び出し可能
- バージョン管理機能を提供

### Strands Agent（Docker/ECR）

実際のエージェントロジックを実装したコンテナ。

| ファイル | 説明 |
|---------|------|
| `app/main.py` | AgentCoreから呼び出される `handler()` 関数 |
| `app/agent.py` | Strands frameworkを使用したエージェント設定（Claude Sonnet 4.5使用） |
| `app/config.py` | 設定モジュール（環境変数、バリデーション） |
| `app/memory.py` | AgentCore Memory統合設定 |
| `app/tools.py` | カスタムツール（retrieve_memory_tool, save_memory_tool） |
| `app/workflow.py` | S3ファイル要約ワークフロー（3ステップ処理） |
| `app/server.py` | FastAPIサーバー（コンテナ内エンドポイント） |
| `app/prompts/` | プロンプトテンプレート |

### AgentCore Memory

エージェントの長期記憶を管理するサービス。

- セッション間で情報を永続化
- ログ・トレース配信設定でオブザーバビリティを確保

### Lambda Invoker

S3イベントをトリガーにAgentCoreを呼び出すLambda関数。

- S3にファイルがアップロードされると起動
- AgentCore Runtimeのエンドポイントを呼び出し
- エージェントのレスポンスをS3に保存（`outputs/`配下）

#### S3出力機能

エージェントの処理結果は自動的にS3に保存されます：

- **出力先**: `s3://{OUTPUT_BUCKET}/outputs/{timestamp}_{session_id}.json`
- **出力形式**:
  ```json
  {
    "timestamp": "2026-01-03T12:00:00Z",
    "session_id": "bucket_path_to_file",
    "actor_id": "user-id-from-metadata",
    "source": {
      "bucket": "入力バケット名",
      "key": "入力ファイルキー"
    },
    "input": "エージェントへの入力テキスト",
    "response": "エージェントからの応答"
  }
  ```

## プロジェクト構成

```
.
├── app/
│   ├── main.py          # エントリーポイント（handler関数）
│   ├── agent.py         # エージェント設定（Claude Sonnet 4.5使用）
│   ├── config.py        # 設定モジュール（環境変数管理）
│   ├── memory.py        # AgentCore Memory統合設定
│   ├── tools.py         # カスタムツール（retrieve/save_memory_tool）
│   ├── workflow.py      # S3ファイル要約ワークフロー
│   ├── server.py        # FastAPIサーバー
│   └── prompts/         # プロンプトテンプレート
│       └── workflow/
│           ├── summarize.md  # 要約タスク用
│           ├── analyze.md    # 分析タスク用
│           └── profile.md    # プロファイル生成用
├── terraform/
│   ├── agentcore.tf     # AgentCore RuntimeとMemoryリソース
│   ├── ecr.tf           # ECRリポジトリ
│   ├── iam.tf           # IAMロールとポリシー
│   ├── lambda.tf        # Lambda関数（S3トリガー用）
│   ├── s3.tf            # S3トリガーバケット
│   ├── observability.tf # ログ・トレース配信設定
│   ├── locals.tf        # ローカル変数定義
│   ├── outputs.tf       # Terraform出力
│   ├── backend.tf       # Terraformステート管理
│   ├── variables.tf     # プロジェクト設定
│   └── versions.tf      # Terraformバージョン指定
├── lambda/
│   └── invoker.py       # S3イベントからAgentCoreを呼び出すLambda
├── tests/               # テストコード
├── docs/                # ドキュメント
├── .claude/agents/      # サブエージェント定義
├── Dockerfile           # コンテナイメージ定義
├── Makefile             # 便利なコマンド集
└── pyproject.toml       # Python依存関係
```

## Terraformリソース

### agentcore.tf

- `aws_bedrockagentcore_agent_runtime` - AgentCore Runtime
- `aws_bedrockagentcore_memory` - AgentCore Memory
- `aws_bedrockagentcore_memory_strategy` - Memory Strategy（ファイル要約・Actor状態追跡）
- エンドポイント設定（DEFAULT, PROD）

### observability.tf

- ログ配信設定（APPLICATION_LOGS, USAGE_LOGS）
- トレース配信設定（X-Ray）

### ecr.tf

- `aws_ecr_repository` - Dockerイメージ用リポジトリ

### iam.tf

- AgentCore用のIAMロール
- Bedrock、ECR、CloudWatch Logsへのアクセス権限

### lambda.tf / s3.tf

- S3トリガー用のLambda関数
- トリガー用S3バケット

## イベント構造

AgentCoreはエージェントを以下の形式で呼び出します（S3ワークフローモードのみサポート）：

```python
{
  "input": {
    "text": "S3ファイルを処理してください"
  },
  "s3_info": {
    "bucket": "bucket-name",
    "key": "path/to/file.txt"
  },
  "sessionId": "session-123",
  "actorId": "user-123"
}
```

## Memory統合

### 設定ファイル

`app/memory.py` で AgentCore Memory との統合を設定：

- Memory ID、Session ID、Actor IDを使用
- Strands frameworkのsession_managerと連携

### Memory利用方法

Memory機能は以下の2つの方法で利用可能です：

#### 1. セッションメモリ（短期記憶）

```python
from app.memory import create_memory
session_manager = create_memory(memory_id, session_id, actor_id)
agent = create_agent(session_manager=session_manager)
```

#### 2. カスタムツール（長期記憶）

```python
from app.tools import retrieve_memory_tool, save_memory_tool

# 過去の要約を取得
records = retrieve_memory_tool(memory_id, actor_id, query="検索クエリ")

# メモリに保存
record_id = save_memory_tool(
    namespace="/file-summaries/{actorId}",
    memory_id=memory_id,
    actor_id=actor_id,
    content="保存するコンテンツ"
)
```

### Memory Strategy

AgentCore Memoryは2つのMemory Strategyを使用して長期記憶を管理：

| Strategy名 | タイプ | Namespace | 用途 |
|------------|--------|-----------|------|
| FileSummaryExtractor | SEMANTIC | `/file-summaries/{actorId}` | S3ファイル要約の蓄積・検索 |
| ActorStateTracker | USER_PREFERENCE | `/actor-state/{actorId}` | Actorの活動状態と傾向の追跡 |

詳細は `terraform/agentcore.tf` のMemory Strategyリソース定義を参照してください。

### Actor状態追跡

エージェントはファイル処理後に自動的にActor状態を保存します：

```python
# app/memory.py の主要関数
retrieve_actor_state()  # Actor状態を取得
save_actor_state()      # Actor状態を保存
```

保存される情報：
- 処理したファイルのキー
- 参照した過去の要約数
- 処理結果の概要（500文字以内）

これにより、同じActorの過去の活動パターンを参照しながら処理を行うことができます。

### オブザーバビリティ

AgentCore Memory・Runtimeはログ・トレース配信設定をサポート：

- **APPLICATION_LOGS**: エージェントの標準出力・エラーログ
- **USAGE_LOGS**: セッションレベルのCPU/メモリ使用量
- **TRACES**: X-Rayへのトレースデータ配信

詳細は `terraform/observability.tf` のObservability設定を参照してください。

## ワークフロー機能

S3ファイルアップロードをトリガーに、3ステップのワークフローを実行します：

### ワークフロー概要

```
Step 1: S3ファイル読み取り → 要約生成 → メモリ保存
    ↓
Step 2: 過去の要約を取得 → パターン分析
    ↓
Step 3: ユーザープロファイル生成 → メモリ保存
```

### 使用例

```python
from app.workflow import run_workflow

result = run_workflow(
    s3_info={"bucket": "bucket-name", "key": "path/to/file.txt"},
    actor_id="user-123",
    memory_id="agentcore_memory-xxx"
)
```

### プロンプトテンプレート

| ファイル | 用途 |
|---------|------|
| `app/prompts/workflow/summarize.md` | S3ファイル要約用 |
| `app/prompts/workflow/analyze.md` | パターン分析用 |
| `app/prompts/workflow/profile.md` | プロファイル生成用 |

## ネットワーク設定

現在のネットワークモードは `PUBLIC` に設定されています（`agentcore.tf`）。

プライベートネットワークが必要な場合は、VPC設定を追加してください。
