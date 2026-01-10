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
- `app/config.py` - アプリケーション設定（環境変数、LTM設定、ロギング）
- `app/memory.py` - AgentCore Memoryの統合設定（セッション管理、LTM取得・保存）
- `app/tools.py` - カスタムツール（@toolデコレータ付き、エージェントから呼び出し可能）
- `app/workflow.py` - CS通話ログ分析ワークフロー（3ステップ処理）
- `app/server.py` - ローカル開発用HTTPサーバー
- `app/prompts/` - プロンプトテンプレート
  - `workflow/system.md` - ワークフロー用システムプロンプト
  - `workflow/step1.md` - Step 1: ライフイベント検出用
  - `workflow/step2.md` - Step 2: 履歴照合・パターン分析用
  - `workflow/step3.md` - Step 3: レコメンド生成用

### インフラストラクチャ（Terraform）
- `terraform/agentcore.tf` - AgentCore RuntimeとMemoryリソース
- `terraform/ecr.tf` - Dockerイメージ用のECRリポジトリ
- `terraform/iam.tf` - Bedrock AgentCoreサービス用のIAMロールとポリシー
- `terraform/backend.tf` - Terraformステートバックエンド設定
- `terraform/variables.tf` - プロジェクト設定（デフォルトは`ap-northeast-1`）

### 処理モード
**CS通話ログ分析モード**: CS通話ログをトリガーにシングルエージェント方式で3ステップのワークフローを実行
- 同一エージェントインスタンスを3回呼び出し、コンテキストを保持
- Step 1: 通話ログからライフイベントを検出
- Step 2: 過去の通話要約と照合・パターン分析
- Step 3: 顧客向けレコメンド生成
- SessionManagerによる会話履歴の自動永続化とMemory Strategyによるライフイベント自動抽出

## 設定

### デフォルト設定（Makefile）
- PROJECT_NAME: `agentcore`
- REGION: `ap-northeast-1`
- Model: `jp.amazon.nova-2-lite-v1:0`（Amazon Nova 2 Lite、日本リージョン用推論プロファイル）

### 設定の変更
Makefile変数をオーバーライドするか、`terraform/variables.tf`のデフォルトを編集します。

## 開発リファレンス

### Memory統合

**セッションメモリ（短期記憶）**
```python
from app.memory import create_memory
session_manager = create_memory(memory_id, session_id, actor_id)
```

**長期メモリ直接操作（memory.py）**
```python
from app.memory import retrieve_past_summaries, retrieve_actor_state, save_actor_state

summaries = retrieve_past_summaries(memory_id, actor_id, query="検索クエリ")
states = retrieve_actor_state(memory_id, actor_id)
record_id = save_actor_state(memory_id, actor_id, state_text="ライフイベント情報...")
```

**Namespace設計**:
- `/call-summaries/{actorId}` - 通話要約の保存（Semantic Strategy）
- `/life-events/{actorId}` - ライフイベント検出結果の保存（User Preference Strategy）

### ワークフロー機能

```python
from app.workflow import run_workflow

result = run_workflow(
    s3_info={"bucket": "bucket-name", "key": "path/to/call-log.txt"},
    actor_id="customer-123",
    session_id="session-123",
    memory_id="agentcore_memory-xxx"
)
```

### イベント構造

AgentCoreは以下の形式のイベントで呼び出します：

```python
{
  "input": {
    "text": "通話ログを分析してください"
  },
  "s3_info": {
    "bucket": "bucket-name",
    "key": "path/to/call-log.txt"
  },
  "sessionId": "session-123",
  "actorId": "customer-123"
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
