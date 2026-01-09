# CLAUDE.md

このファイルは、Claude Code (claude.ai/code) がこのリポジトリで作業する際のガイダンスを提供します。

## プロジェクト概要

このプロジェクトは、コンテナ化されたランタイムを使用してAIエージェントをAWSにパッケージ化・デプロイするBedrock AgentCoreデプロイメントプロジェクトです。以下の技術を使用しています：
- **Strands Agents framework** - エージェント実装
- **Bedrock AgentCore** - AWSでのマネージドエージェントホスティング
- **Terraform** - インフラストラクチャのプロビジョニング
- **Docker + ECR** - コンテナ化されたエージェントのデプロイ
- **uv** - Python依存関係管理

## アーキテクチャ

### アプリケーション構造
- `app/main.py` - AgentCore Runtimeから呼び出される`handler()`関数を持つエントリーポイント
- `app/agent.py` - Strandsフレームワークを使用したエージェント設定（Claude Sonnet 4.5モデル）
- `app/config.py` - アプリケーション設定（環境変数、LTM設定、ロギング）
- `app/memory.py` - AgentCore Memoryの統合設定（セッション管理、LTM取得・保存）
- `app/tools.py` - カスタムツール（@toolデコレータ付き、エージェントから呼び出し可能）
- `app/workflow.py` - S3ファイル要約ワークフロー（3ステップ処理）
- `app/server.py` - ローカル開発用HTTPサーバー
- `app/prompts/` - プロンプトテンプレート
  - `workflow/summarize.md` - S3ファイル要約用
  - `workflow/analyze.md` - パターン分析用
  - `workflow/profile.md` - プロファイル生成用

### インフラストラクチャ（Terraform）
- `terraform/agentcore.tf` - AgentCore RuntimeとMemoryリソース
- `terraform/ecr.tf` - Dockerイメージ用のECRリポジトリ
- `terraform/iam.tf` - Bedrock AgentCoreサービス用のIAMロールとポリシー
- `terraform/backend.tf` - Terraformステートバックエンド設定
- `terraform/variables.tf` - プロジェクト設定（デフォルトは`ap-northeast-1`）

### 処理モード
**S3ワークフローモード**: S3ファイルアップロードをトリガーに3ステップのワークフローを実行
- Step 1: S3ファイル読み取り・要約・メモリ保存
- Step 2: 過去の要約を取得・パターン分析
- Step 3: ユーザープロファイル生成・メモリ保存

## 設定

### デフォルト設定（Makefile）
- PROJECT_NAME: `agentcore`
- REGION: `ap-northeast-1`
- Model: `jp.anthropic.claude-sonnet-4-5-20250929-v1:0`（日本リージョンエンドポイント）

### 設定の変更
Makefile変数をオーバーライドするか、`terraform/variables.tf`のデフォルトを編集します。

## 開発リファレンス

### Memory統合

**セッションメモリ（短期記憶）**
```python
from app.memory import create_memory
session_manager = create_memory(memory_id, session_id, actor_id)
agent = create_agent(session_manager=session_manager)
```

**長期メモリ直接操作（memory.py）**
```python
from app.memory import retrieve_past_summaries, retrieve_actor_state, save_actor_state

summaries = retrieve_past_summaries(memory_id, actor_id, query="検索クエリ")
states = retrieve_actor_state(memory_id, actor_id)
record_id = save_actor_state(memory_id, actor_id, state_text="ユーザーの傾向...")
```

**Namespace設計**:
- `/file-summaries/{actorId}` - ファイル要約の保存（Semantic Strategy）
- `/actor-state/{actorId}` - ユーザープロファイルの保存（User Preference Strategy）

### ワークフロー機能

```python
from app.workflow import run_workflow

result = run_workflow(
    s3_info={"bucket": "bucket-name", "key": "path/to/file.txt"},
    actor_id="user-123",
    session_id="session-123",
    memory_id="agentcore_memory-xxx"
)
```

### イベント構造

AgentCoreは以下の形式のイベントで呼び出します：

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

## 開発ルール

このプロジェクトでは、`.claude/rules/`に定義されたルールを**必ず**遵守してください。

| ルール | 概要 |
|-------|------|
| `tdd.md` | Pythonコード実装時はテストを先に書く |
| `worktree.md` | mainブランチでの直接作業禁止、別ワークツリーで作業 |
| `coding-conventions.md` | コメント・docstringは日本語、命名規則 |
| `testing.md` | テスト方針、モック使用の判断基準 |
| `deployment.md` | デプロイメントワークフロー、AWS認証 |
| `agents.md` | サブエージェントの選択・利用ガイド |
