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
├── test_agent.py            # app/agent.pyのテスト
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

#### 5. ワークツリーのクリーンアップ（マージ後）

```bash
cd ../terraform_agentcore
git worktree remove ../terraform_agentcore-issue-XX
git branch -d feature/issue-XX-description
git pull origin main
```

## エージェント開発

### ツールの追加

`app/agent.py` を編集し、`tools=[]` パラメータにツールを追加します。

```python
from strands import Agent
from strands_tools import calculator, web_search

agent = Agent(
    model="jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
    tools=[calculator, web_search],  # ツールを追加
)
```

利用可能なツールは `strands-agents-tools` パッケージを参照してください。

### Memory統合

`app/memory.py` の `create_memory()` 関数を使用して Memory を統合できます：

1. `main.py` でインポート
2. eventからmemory_id、session_id、actor_idを抽出
3. session_managerをエージェント設定に渡す

## サブエージェント

Claude Codeが使用する専門サブエージェント：

| エージェント | 専門領域 |
|-------------|---------|
| `terraform-specialist` | Terraform/AWSインフラ構築、IAM設計 |
| `python-developer` | Pythonアプリケーション、Lambda関数実装 |
| `strands-agent-developer` | Strands Agents、AgentCore統合 |
| `integrator` | 統合検証、デプロイ確認 |
| `test-specialist` | TDD、テスト実装、カバレッジ分析 |
| `cloudwatch-investigator` | CloudWatchログ調査、エラー分析 |

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
