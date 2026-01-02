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
