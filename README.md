# Bedrock AgentCore デプロイメントプロジェクト

AWS Bedrock AgentCoreを使用して、コンテナ化されたAIエージェントをAWSにデプロイするためのプロジェクトです。

## 概要

このプロジェクトは以下の技術スタックで構築されています：

- **Strands Agents framework** - エージェント実装フレームワーク
- **Bedrock AgentCore** - AWSマネージドエージェントホスティング
- **Terraform** - インフラストラクチャ管理
- **Docker + ECR** - コンテナイメージ管理
- **uv** - Python依存関係管理

## 前提条件

- AWS CLIがインストール・設定済み
- Dockerがインストール済み
- Terraformがインストール済み
- Python 3.12+
- uv（Python依存関係管理ツール）

## プロジェクト構成

```
.
├── app/
│   ├── main.py          # エントリーポイント（handler関数）
│   ├── agent.py         # エージェント設定（Claude Sonnet 4.5使用）
│   ├── memory.py        # AgentCore Memory統合設定
│   └── prompts/         # プロンプトテンプレート
├── terraform/
│   ├── agentcore.tf     # AgentCore RuntimeとMemoryリソース
│   ├── ecr.tf           # ECRリポジトリ
│   ├── iam.tf           # IAMロールとポリシー
│   ├── lambda.tf        # Lambda関数（S3トリガー用）
│   ├── s3.tf            # S3トリガーバケット
│   ├── backend.tf       # Terraformステート管理
│   └── variables.tf     # プロジェクト設定
├── lambda/
│   └── invoker.py       # S3イベントからAgentCoreを呼び出すLambda
├── tests/               # テストコード
├── .claude/agents/      # サブエージェント定義
├── Dockerfile           # コンテナイメージ定義
├── Makefile             # 便利なコマンド集
└── pyproject.toml       # Python依存関係
```

## クイックスタート

### 1. 初回デプロイ

```bash
# 依存関係のインストール
make setup

# 初回デプロイ（ECR作成 → イメージビルド&プッシュ → AgentCore作成）
make deploy-init
```

### 2. コード変更後の更新デプロイ

```bash
# インフラ更新 + 新しいイメージをプッシュ
make deploy
```

## よく使うコマンド

### 開発

| コマンド | 説明 |
|---------|------|
| `make setup` | 依存関係のインストール |
| `make build` | Dockerイメージをビルド |
| `make push` | イメージをビルド＆ECRにプッシュ |

### インフラ

| コマンド | 説明 |
|---------|------|
| `make init` | Terraformの初期化 |
| `make plan` | インフラ変更のプレビュー |
| `make apply` | インフラを適用 |
| `make destroy` | すべてのリソースを削除 |

### デプロイ

| コマンド | 説明 |
|---------|------|
| `make deploy-init` | 初回デプロイ（ECR → イメージ → AgentCore） |
| `make deploy` | 通常のデプロイ（インフラ更新 + イメージ更新） |

### AgentCoreエンドポイント管理

| コマンド | 説明 |
|---------|------|
| `make update-endpoint` | DEFAULTエンドポイントを最新バージョンに更新 |
| `make get-runtime-info` | Runtime情報とエンドポイント一覧を表示 |

### テスト

| コマンド | 説明 |
|---------|------|
| `make test` | 全テストを実行 |
| `make test-cov` | カバレッジ付きでテストを実行 |

## 設定

デフォルト設定は`Makefile`で定義されています：

- **プロジェクト名**: `agentcore`
- **リージョン**: `ap-northeast-1`
- **モデル**: `jp.anthropic.claude-sonnet-4-5-20250929-v1:0`（日本リージョン）

設定を変更する場合は、`Makefile`の変数を編集するか、`terraform/variables.tf`を変更してください。

## サブエージェント

このプロジェクトでは、Claude Codeが使用する専門サブエージェントを定義しています。

| エージェント | 専門領域 |
|-------------|---------|
| `terraform-specialist` | Terraform/AWSインフラ構築、IAM設計 |
| `python-developer` | Pythonアプリケーション、Lambda関数実装 |
| `strands-agent-developer` | Strands Agents、AgentCore統合 |
| `integrator` | 統合検証、デプロイ確認 |
| `test-specialist` | TDD、テスト実装、カバレッジ分析 |
| `cloudwatch-investigator` | CloudWatchログ調査、エラー分析 |

詳細は`.claude/agents/`ディレクトリと`CLAUDE.md`を参照してください。

## アーキテクチャ

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   S3 Bucket     │────▶│     Lambda      │────▶│ AgentCore       │
│  (トリガー)      │     │   (Invoker)     │     │  Runtime        │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ Strands Agent   │
                                               │ (Docker/ECR)    │
                                               └────────┬────────┘
                                                         │
                                                         ▼
                                               ┌─────────────────┐
                                               │ AgentCore       │
                                               │   Memory        │
                                               └─────────────────┘
```

## 開発ガイドライン

### Git/ブランチ戦略

すべての作業は別ワークツリーで実施し、マージ前にプルリクエストを作成してください。

```bash
# 新しいワークツリーを作成
git worktree add -b feature/issue-XX ../terraform_agentcore-issue-XX

# 作業完了後、PRを作成
gh pr create --title "Issue #XX対応" --body "変更内容"
```

### テスト方針

- モックはなるべく使用せず、実際の環境でテストすることを優先
- 課金が発生する外部サービスのみモックを許可

詳細は`CLAUDE.md`を参照してください。

## トラブルシューティング

### AWS認証エラー

```bash
# AWS SSOで再認証
aws login
```

### ECRログインエラー

```bash
make login
```

### AgentCore Runtimeの状態確認

```bash
make get-runtime-info
```

### エンドポイント更新が反映されない

```bash
make update-endpoint
```

## ドキュメント

- `CLAUDE.md` - 開発ガイダンス、コーディング規約
- `.claude/agents/` - サブエージェント定義

## ライセンス

このプロジェクトは個人プロジェクトです。
