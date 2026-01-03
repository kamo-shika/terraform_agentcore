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

# エージェントをローカルで実行
make run-local               # app/main.pyを直接実行してテスト
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
make deploy                  # 1. 新しいイメージをビルド＆プッシュ
                            # 2. Terraformを適用（イメージダイジェストの変更を検知）
```

**イメージ変更検知の仕組み**：
- `data.aws_ecr_image.latest`でECRイメージのダイジェストを取得
- `terraform_data.image_digest_trigger`でダイジェスト変更を追跡
- ダイジェストが変わると`lifecycle.replace_triggered_by`でAgentCore Runtimeが再作成される
- `make deploy`は必ず`push → apply`の順序で実行される（ダイジェスト取得のため）

**AgentCoreエンドポイント管理**：
```bash
make update-endpoint         # DEFAULTエンドポイントを最新バージョンに更新
make get-runtime-info        # Runtime情報とエンドポイント状態を表示
```

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

## Git/ブランチ戦略

**重要**: すべての作業は別ワークツリーで実施し、マージ前にプルリクエストを作成してください。

### ワークフロー

1. **別ワークツリーの作成**
   ```bash
   # Issue番号に基づいたブランチ名で別ワークツリー作成
   git worktree add -b feature/issue-XX-description ../terraform_agentcore-issue-XX
   cd ../terraform_agentcore-issue-XX
   ```

2. **作業実施** - コードの実装・修正・テスト

3. **変更のコミット**
   ```bash
   git add .
   git status
   git diff --staged
   git commit -m "[Issue #XX] 変更内容の要約"
   ```

4. **プルリクエスト作成**
   ```bash
   git push -u origin feature/issue-XX-description
   gh pr create --title "Issue #XX対応: タイトル" --body "変更内容の説明"
   ```

5. **ワークツリーのクリーンアップ（マージ後）**
   ```bash
   cd ../terraform_agentcore
   git worktree remove ../terraform_agentcore-issue-XX
   git branch -d feature/issue-XX-description
   git pull origin main
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

### TDD（テスト駆動開発）ワークフロー

このプロジェクトでは、`test-specialist`エージェントを使用したTDDを推奨しています。

#### Red-Green-Refactorサイクル

1. **Red（テストを先に書く）**
   - `test-specialist`が要件からテストを先に実装
   - テストを実行して失敗を確認

2. **Green（最小限の実装でテストを通す）**
   - `python-developer`がテストを通す最小限のコードを実装
   - テストを実行して成功を確認

3. **Refactor（リファクタリング）**
   - `python-developer`がコードを改善
   - テストが通ることを確認しながら改善

4. **Integration（統合検証）**
   - `integrator`がエンドツーエンドで動作確認

#### 新機能追加時の流れ

```bash
# 1. test-specialistがテストを実装（Red）
Task(subagent_type="test-specialist", prompt="XX機能のテストケースを実装")

# 2. テスト実行して失敗を確認
make test

# 3. python-developerが実装（Green）
Task(subagent_type="python-developer", prompt="XX機能を実装してテストを通す")

# 4. テスト実行して成功を確認
make test

# 5. 必要に応じてリファクタリング（Refactor）
Task(subagent_type="python-developer", prompt="XX機能をリファクタリング")

# 6. カバレッジ確認
make test-cov

# 7. 統合テスト（Integration）
Task(subagent_type="integrator", prompt="XX機能のエンドツーエンドテスト")
```

#### フィクスチャの活用

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
