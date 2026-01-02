# Bedrock AgentCore デプロイメントプロジェクト

AWS Bedrock AgentCoreを使用して、コンテナ化されたAIエージェントをAWSにデプロイするためのプロジェクトです。

## 🚀 概要

このプロジェクトは以下の技術スタックで構築されています：

- **Strands Agents framework** - エージェント実装フレームワーク
- **Bedrock AgentCore** - AWSマネージドエージェントホスティング
- **Terraform** - インフラストラクチャ管理
- **Docker + ECR** - コンテナイメージ管理
- **uv** - Python依存関係管理

## 📋 前提条件

- AWS CLIがインストール・設定済み
- Dockerがインストール済み
- Terraformがインストール済み
- Python 3.12+
- uv（Python依存関係管理ツール）

## 🏗️ プロジェクト構成

```
.
├── app/
│   ├── main.py          # エントリーポイント（handler関数）
│   ├── agent.py         # エージェント設定（Claude Sonnet 4.5使用）
│   └── memory.py        # AgentCore Memory統合設定
├── terraform/
│   ├── agentcore.tf     # AgentCore RuntimeとMemoryリソース
│   ├── ecr.tf           # ECRリポジトリ
│   ├── iam.tf           # IAMロールとポリシー
│   ├── backend.tf       # Terraformステート管理
│   └── variables.tf     # プロジェクト設定
├── Dockerfile           # コンテナイメージ定義
├── Makefile             # 便利なコマンド集
└── pyproject.toml       # Python依存関係
```

## 🎯 クイックスタート

### 1. 初回デプロイ

プロジェクトを初めてデプロイする場合：

```bash
# 依存関係のインストール
make setup

# 初回デプロイ（ECR作成 → イメージビルド&プッシュ → AgentCore作成）
make deploy-init
```

このコマンドで以下が実行されます：
1. ECRリポジトリの作成
2. Dockerイメージのビルドとプッシュ
3. AgentCore RuntimeとMemoryの作成

### 2. ローカルでのテスト

デプロイ前にローカルでエージェントをテストできます：

```bash
# エージェントをローカル実行
make run-local
```

### 3. コード変更後の更新デプロイ

エージェントのコードを変更した後：

```bash
# インフラ更新 + 新しいイメージをプッシュ
make deploy
```

## 📝 よく使うコマンド

### 開発コマンド

```bash
make setup          # 依存関係のインストール
make run-local      # エージェントをローカル実行
make build          # Dockerイメージをビルド
make push           # イメージをビルド＆ECRにプッシュ
```

### インフラコマンド

```bash
make init           # Terraformの初期化
make plan           # インフラ変更のプレビュー
make apply          # インフラを適用
make destroy        # すべてのリソースを削除
```

### デプロイコマンド

```bash
make deploy-init    # 初回デプロイ（ECR → イメージ → AgentCore）
make deploy         # 通常のデプロイ（インフラ更新 + イメージ更新）
```

## ⚙️ 設定

デフォルト設定は`Makefile`で定義されています：

- **プロジェクト名**: `agentcore`
- **リージョン**: `ap-northeast-1`
- **モデル**: `jp.anthropic.claude-sonnet-4-5-20250929-v1:0`（日本リージョン）

設定を変更する場合は、`Makefile`の変数を編集するか、`terraform/variables.tf`を変更してください。

## 🔧 エージェントのカスタマイズ

### ツールの追加

`app/agent.py`を編集して、エージェントにツールを追加できます：

```python
agent = create_agent(
    model=model,
    agent_name="agent-core",
    tools=[
        # ここにツールを追加
        # strands-agents-toolsパッケージから利用可能
    ]
)
```

### Memory統合の有効化

`app/memory.py`に既にMemory統合の準備がありますが、現在は未接続です。有効にする場合は`app/main.py`で統合してください。

## 🗂️ デプロイメントの仕組み

1. **ローカル開発**: `app/`ディレクトリでエージェントコードを開発
2. **コンテナ化**: Dockerfileでイメージをビルド
3. **ECRプッシュ**: AWSのECRリポジトリにイメージを保存
4. **AgentCore**: TerraformでAgentCore Runtimeを作成し、ECRイメージを参照
5. **実行**: AgentCoreがコンテナを起動し、`handler()`関数を呼び出し

## 📚 詳細ドキュメント

より詳細な技術情報は`CLAUDE.md`を参照してください。

## 🐛 トラブルシューティング

### ECRログインエラー

```bash
# 手動でECRにログイン
make login
```

### Terraformエラー

```bash
# Terraformの状態をリセット
cd terraform
terraform init -reconfigure
```

### イメージプッシュの失敗

ECRリポジトリが先に作成されているか確認してください：

```bash
make init
make apply  # ECRリソースのみ適用
```

## 📄 ライセンス

このプロジェクトは個人プロジェクトです。
