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
- `app/memory.py` - AgentCore Memoryの統合設定（現在はmainハンドラに未接続）

### インフラストラクチャ（Terraform）
- `terraform/agentcore.tf` - AgentCore RuntimeとMemoryリソース
- `terraform/ecr.tf` - Dockerイメージ用のECRリポジトリ
- `terraform/iam.tf` - Bedrock AgentCoreサービス用のIAMロールとポリシー
- `terraform/backend.tf` - Terraformステートバックエンド設定
- `terraform/variables.tf` - プロジェクト設定（デフォルトは`ap-northeast-1`）

### アーキテクチャの重要な注意点
- AgentCore RuntimeはECRからコンテナイメージを取得
- コンテナはAgentCoreの呼び出しモデルと互換性のあるhandler関数を公開する必要がある
- Memory統合は`memory.py`に存在するが、現在はmainハンドラでは使用されていない
- ネットワークモードはPUBLIC（agentcore.tf:13で設定）

## 開発コマンド

### ローカル開発
```bash
# 依存関係のセットアップ
make setup                    # uv syncで依存関係をインストール
```

### Dockerビルドとプッシュ
```bash
# Dockerイメージをビルド
make build                   # agentcore-repo:latestとしてタグ付けされたイメージをビルド

# ECRにログイン
make login                   # DockerをECRで認証

# ECRにビルドしてプッシュ
make push                    # login + build + tag + pushを実行
```

### Terraformデプロイメント
```bash
# Terraformの初期化
make init                    # cd terraform && terraform init

# インフラストラクチャの変更をプレビュー
make plan                    # デフォルト変数で変更をプレビュー

# インフラストラクチャを適用
make apply                   # すべてのリソースをデプロイ/更新

# インフラストラクチャを破棄
make destroy                 # すべてのリソースを削除
```

### デプロイメントワークフロー

**初回デプロイメント**（ECR、次にイメージ、次にエージェントを作成）：
```bash
make deploy-init             # 1. ECRリポジトリを作成
                            # 2. イメージをビルド＆プッシュ
                            # 3. AgentCore runtimeとmemoryを作成
```

**通常のデプロイメント**（コード変更時）：
```bash
make deploy                  # 1. 新しいイメージをビルド＆プッシュ（latestとgit commit hashタグ）
                            # 2. Terraformを適用（UpdateAgentRuntime APIでin-place更新）
```

**イメージ変更検知とバージョン管理の仕組み**：
- ECRイメージには`latest`タグとGit commit hashタグ（例: `abc1234`）の両方が付与される
- `container_uri`の変更時は`UpdateAgentRuntime` APIでin-place更新される（destroy→createではない）
- 更新のたびにAgentCore Runtimeの新しいバージョン（V1, V2, V3...）が自動作成される
- バージョン履歴は保持され、ロールバック可能
- DEFAULTエンドポイントは自動的に最新バージョンを指す

**AgentCoreエンドポイント・バージョン管理**：
```bash
make get-runtime-info        # Runtime情報とエンドポイント状態を表示
make list-versions           # Runtime全バージョン一覧を表示
make list-endpoints          # 全エンドポイント一覧を表示
make update-endpoint         # DEFAULTエンドポイントを最新バージョンに更新
make rollback VERSION=V1     # PRODエンドポイントを指定バージョンにロールバック
```

**PRODエンドポイントの有効化**：
本番環境で手動バージョン管理が必要な場合、Terraformで有効化できます：
```bash
make apply -- -var="enable_prod_endpoint=true"
```
PRODエンドポイントはDEFAULTと異なり、明示的に`make rollback`を実行しない限りバージョンが変更されません。

### AWS認証

デプロイメントやAWSリソース操作を行う前に、AWS認証が必要です。セッションが期限切れの場合は以下を実行してください：

```bash
aws login                    # AWS SSOで認証を取得
```

**注意事項：**
- `make push`、`make deploy`などのコマンド実行前に認証が必要
- セッションは一定時間で期限切れになるため、定期的に再認証が必要
- 認証エラー（"Your session has expired"）が発生した場合は`aws login`を実行

## 設定

### デフォルト設定（Makefile）
- PROJECT_NAME: `agentcore`
- REGION: `ap-northeast-1`
- Model: `jp.anthropic.claude-sonnet-4-5-20250929-v1:0`（日本リージョンエンドポイント）

### 設定の変更
Makefile変数をオーバーライドするか、`terraform/variables.tf`のデフォルトを編集します。Terraformコマンドは実行時のカスタマイズのために`-var`フラグを受け付けます。

## エージェント開発

### エージェントにツールを追加
`app/agent.py`を編集し、`tools=[]`パラメータにツールを追加します。`strands-agents-tools`パッケージから利用可能です。

### Memory統合
`app/memory.py`の`create_memory()`関数は準備できていますが、まだ統合されていません。有効にするには：
1. `main.py`でインポート
2. eventからmemory_id、session_id、actor_idを抽出
3. session_managerをエージェント設定に渡す

### イベント構造
AgentCoreは以下の形式のイベントで呼び出します：
```python
{
  "input": {
    "text": "user input here"
  }
}
```

## 開発ルール（必須）

このプロジェクトでは、`.claude/rules/`に定義されたルールを**必ず**遵守してください。

| ルール | 概要 | 詳細 |
|-------|------|------|
| **TDD** | Pythonコード実装時はテストを先に書く | `.claude/rules/tdd.md` |
| **Worktree** | mainブランチでの直接作業禁止、別ワークツリーで作業 | `.claude/rules/worktree.md` |

### クイックリファレンス

**TDD（Red-Green-Refactor）**:
1. テストを先に書く → `make test` で失敗確認
2. 最小限の実装 → `make test` で成功確認
3. リファクタリング → `make test-cov` でカバレッジ確認

**Worktree**:
```bash
# 作業開始
git worktree add -b feature/issue-XX-description ../terraform_agentcore-issue-XX

# PR作成
git push -u origin feature/issue-XX-description && gh pr create

# クリーンアップ（マージ後）
git worktree remove ../terraform_agentcore-issue-XX
```

## テスト

### テストコマンド
```bash
# 全テストを実行
make test                    # uv run pytest tests/ -v

# カバレッジ付きでテストを実行
make test-cov                # uv run pytest tests/ --cov=app --cov-report=term-missing

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

**重要原則**: モックはなるべく使用せず、実際の環境でテストすることを優先してください。

- **実際のコードで動作確認**: 可能な限り実装されたコードそのものをテスト
- **インテグレーションテスト**: コンポーネント間の統合も実際に動作確認
- **エンドツーエンドテスト**: 実際のユースケースに沿った動作確認

**モックを使用してよい場合（最小限）**:
- 課金が発生する外部サービス（EC2起動、S3への大量書き込みなど）
- 制御できない外部依存（サードパーティAPIなど）
- 時間がかかりすぎる処理（数分以上）

**避けるべきモックの使用**:
- 自分たちのコード内の関数をモック化する
- boto3クライアントを安易にモック化する
- テストの簡便さのためだけにモックを使用する

### フィクスチャの活用

`tests/conftest.py`に定義された共通フィクスチャを活用してください：

| フィクスチャ | 用途 |
|-------------|------|
| `sample_event` | 標準的なAgentCoreイベント |
| `sample_event_with_session` | セッション情報付きイベント |
| `sample_s3_event` | S3ファイル処理用イベント |
| `empty_event` / `invalid_event` | エラーハンドリングテスト用 |
| `clean_env` | 環境変数をクリーンにする |
| `set_memory_env` | Memory関連環境変数を設定 |

## サブエージェント

このプロジェクトでは、専門領域ごとにサブエージェントを定義しています。

### エージェント一覧

| エージェント | 専門領域 | 定義ファイル |
|-------------|---------|-------------|
| `terraform-specialist` | Terraform/AWSインフラ構築、IAM設計 | `.claude/agents/terraform-specialist.md` |
| `python-developer` | Pythonアプリケーション、Lambda関数実装 | `.claude/agents/python-developer.md` |
| `strands-agent-developer` | Strands Agents、AgentCore統合 | `.claude/agents/strands-agent-developer.md` |
| `integrator` | 統合検証、デプロイ確認 | `.claude/agents/integrator.md` |
| `test-specialist` | TDD、テスト実装、カバレッジ分析 | `.claude/agents/test-specialist.md` |
| `cloudwatch-investigator` | CloudWatchログ調査、エラー分析 | `.claude/agents/cloudwatch-investigator.md` |

### 使用方法

```
Task(subagent_type="python-developer", prompt="xxx機能を実装してください")
```

各エージェントは上記の「Git/ブランチ戦略」に従って作業します。

## コーディング規約

### コメントとドキュメント
- **すべてのコメントとdocstringは日本語で記載してください**
- Python関数のdocstringは以下の形式で記載：
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
- インラインコメントも日本語で記載（`# S3バケットとオブジェクト情報を抽出`）
- Shellスクリプトのコメントも日本語で記載
- Terraformのコメント（`#`）も日本語で記載

### その他の規約
- 変数名や関数名は英語で記載（Pythonの命名規則に従う）
- ログメッセージは英語でも日本語でも可
- エラーメッセージは状況に応じて適切な言語を選択
