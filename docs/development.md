# 開発ガイド

このドキュメントでは、開発環境のセットアップ、テスト方針、Git戦略について説明します。

## 開発環境セットアップ

### 前提条件

- Python 3.12+
- uv（Python依存関係管理ツール）
- Docker
- Terraform
- AWS CLI

### セットアップ

```bash
# 依存関係のインストール
make setup
```

## テスト

### コマンド

```bash
# 全テストを実行
make test

# カバレッジ付きでテストを実行
make test-cov

# 特定のテストファイルを実行
uv run pytest tests/test_main.py -v

# 特定のテスト関数を実行
uv run pytest tests/test_main.py::TestHandler::test_handler_with_valid_input -v
```

### テストディレクトリ構造

```
tests/
├── __init__.py              # テストパッケージ
├── conftest.py              # 共通フィクスチャとpytest設定
├── test_main.py             # app/main.pyのテスト
├── test_memory.py           # app/memory.pyのテスト
├── test_tools.py            # app/tools.pyのテスト（カスタムツール）
├── test_workflow.py         # app/workflow.pyのテスト（ワークフロー）
├── test_config.py           # app/config.pyのテスト
├── test_prompts.py          # app/prompts/のテスト
├── test_server.py           # app/server.pyのテスト
└── fixtures/                # テストデータとヘルパー
    └── __init__.py
```

### テスト方針

**重要原則**: モックはなるべく使用せず、実際の環境でテストすることを優先。

**モックを使用してよい場合（最小限）**:
- 課金が発生する外部サービス（EC2起動、S3への大量書き込みなど）
- 制御できない外部依存（サードパーティAPIなど）
- 時間がかかりすぎる処理（数分以上）

**避けるべきモックの使用**:
- 自分たちのコード内の関数をモック化する
- boto3クライアントを安易にモック化する
- テストの簡便さのためだけにモックを使用する

### フィクスチャ

`tests/conftest.py` に定義された共通フィクスチャ：

| フィクスチャ | 用途 |
|-------------|------|
| `sample_event` | 標準的なAgentCoreイベント |
| `sample_event_with_session` | セッション情報付きイベント |
| `sample_s3_event` | S3ファイル処理用イベント |
| `empty_event` / `invalid_event` | エラーハンドリングテスト用 |
| `clean_env` | 環境変数をクリーンにする |
| `set_memory_env` | Memory関連環境変数を設定 |

## TDD（テスト駆動開発）

### Red-Green-Refactorサイクル

1. **Red** - テストを先に書く（失敗を確認）
2. **Green** - 最小限の実装でテストを通す
3. **Refactor** - コードを改善（テストが通ることを確認しながら）

### ワークフロー例

```bash
# 1. テストを実装（Red）
# tests/test_new_feature.py を作成

# 2. テスト実行して失敗を確認
make test

# 3. 実装（Green）
# app/new_feature.py を実装

# 4. テスト実行して成功を確認
make test

# 5. リファクタリング（Refactor）
# コードを改善

# 6. カバレッジ確認
make test-cov
```

## Git/ブランチ戦略

すべての作業は別ワークツリーで実施し、マージ前にプルリクエストを作成してください。

### ワークフロー

#### 1. 別ワークツリーの作成

```bash
# Issue番号に基づいたブランチ名で別ワークツリー作成
git worktree add -b feature/issue-XX-description ../terraform_agentcore-issue-XX
cd ../terraform_agentcore-issue-XX
```

#### 2. 作業実施

コードの実装・修正・テスト

#### 3. 変更のコミット

```bash
git add .
git status
git diff --staged
git commit -m "[Issue #XX] 変更内容の要約"
```

#### 4. プルリクエスト作成

```bash
git push -u origin feature/issue-XX-description
gh pr create --title "Issue #XX対応: タイトル" --body "変更内容の説明"
```

#### 5. 実環境での動作確認（Pythonコード変更時）

```bash
# ワークツリーからデプロイ
make deploy

# Runtime情報を確認
make get-runtime-info
```

#### 6. ワークツリーのクリーンアップ（マージ後）

```bash
cd ../terraform_agentcore
git worktree remove ../terraform_agentcore-issue-XX
git branch -d feature/issue-XX-description
git pull origin main
```

## エージェント開発

### ツールの追加

`app/tools.py` を編集し、`@tool` デコレータを使用してツールを追加します。

```python
from strands import tool

@tool
def my_custom_tool(param1: str, param2: int) -> str:
    """
    カスタムツールの説明。

    Args:
        param1: パラメータ1の説明
        param2: パラメータ2の説明

    Returns:
        処理結果
    """
    # ツールの処理
    return result
```

利用可能なツールは `strands-agents-tools` パッケージを参照してください。

### Memory統合

Memory機能は以下の2つの方法で利用可能です。

#### 1. セッションメモリ（短期記憶）

```python
from app.memory import create_memory
session_manager = create_memory(memory_id, session_id, actor_id)
```

#### 2. 長期メモリ直接操作（memory.py）

```python
from app.memory import retrieve_past_summaries, retrieve_actor_state, save_actor_state

# 過去の通話要約を取得
summaries = retrieve_past_summaries(memory_id, actor_id, query="検索クエリ")

# ライフイベント情報を取得
states = retrieve_actor_state(memory_id, actor_id)

# ライフイベント情報を保存
record_id = save_actor_state(memory_id, actor_id, state_text="ライフイベント情報...")
```

#### Namespace設計

| Namespace | Strategy | 用途 |
|-----------|----------|------|
| `/call-summaries/{actorId}` | Semantic Strategy | 通話要約の保存 |
| `/life-events/{actorId}` | User Preference Strategy | ライフイベント情報の保存 |

### ワークフロー機能

CS通話ログアップロードをトリガーに、3ステップのワークフローを実行します。

```python
from app.workflow import run_workflow

result = run_workflow(
    s3_info={"bucket": "bucket-name", "key": "path/to/call-log.txt"},
    actor_id="customer-123",
    session_id="session-123",
    memory_id="agentcore_memory-xxx"
)
```

#### ワークフロー定義のカスタマイズ

| ファイル | 用途 |
|---------|------|
| `app/prompts/workflow/system.md` | システムプロンプト |
| `app/prompts/workflow/step1.md` | ライフイベント検出タスクのプロンプト |
| `app/prompts/workflow/step2.md` | 履歴照合・パターン分析タスクのプロンプト |
| `app/prompts/workflow/step3.md` | レコメンド生成タスクのプロンプト |

## サブエージェント

Claude Codeが使用する専門サブエージェント：

| エージェント | 専門領域 | 定義ファイル |
|-------------|---------|-------------|
| `terraform-specialist` | Terraform/AWSインフラ構築、IAM設計 | `.claude/agents/terraform-specialist.md` |
| `python-developer` | Pythonアプリケーション、Lambda関数実装 | `.claude/agents/python-developer.md` |
| `strands-agent-developer` | Strands Agents、AgentCore統合 | `.claude/agents/strands-agent-developer.md` |
| `integrator` | 統合検証、デプロイ確認 | `.claude/agents/integrator.md` |
| `test-specialist` | TDD、テスト実装、カバレッジ分析 | `.claude/agents/test-specialist.md` |
| `cloudwatch-investigator` | CloudWatchログ調査、エラー分析 | `.claude/agents/cloudwatch-investigator.md` |

詳細は `.claude/agents/` ディレクトリを参照してください。

## コーディング規約

### コメントとドキュメント

- すべてのコメントとdocstringは日本語で記載
- Python関数のdocstringは以下の形式：

```python
def function_name(arg1: str, arg2: int) -> str:
    """
    関数の簡潔な説明。

    Args:
        arg1: 引数1の説明
        arg2: 引数2の説明

    Returns:
        戻り値の説明

    Raises:
        ErrorType: エラー発生条件の説明
    """
```

### その他

- 変数名や関数名は英語（Pythonの命名規則に従う）
- インラインコメントも日本語で記載

## オブザーバビリティ

### OpenTelemetry設定

AgentCore Runtimeとの統合オブザーバビリティのため、`aws-opentelemetry-distro`パッケージを使用しています。

```python
# pyproject.toml
dependencies = [
    ...
    "aws-opentelemetry-distro>=0.12.2",  # AgentCore Observability用
]
```

### トレース配信

トレースデータはX-Rayに自動配信されます。設定は`terraform/observability.tf`で管理：

- **Runtime TRACES**: InvokeAgentRuntimeなどのスパンデータ
- **Memory TRACES**: CreateEvent, GetEvent, RetrieveMemoryRecordsなどのスパンデータ

### ログ配信

CloudWatch Logsに以下のログが配信されます：

| ログタイプ | 用途 |
|-----------|------|
| APPLICATION_LOGS | エージェントの標準出力・エラーログ |
| USAGE_LOGS | セッションレベルのCPU/メモリ使用量 |

詳細なログ確認手順は [operations.md](./operations.md) を参照してください。
