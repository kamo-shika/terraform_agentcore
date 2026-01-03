# Bedrock AgentCore デプロイメントプロジェクト

AWS Bedrock AgentCoreを使用して、コンテナ化されたAIエージェントをAWSにデプロイするためのプロジェクトです。

## 技術スタック

- **Strands Agents framework** - エージェント実装
- **Bedrock AgentCore** - マネージドエージェントホスティング
- **Terraform** - インフラストラクチャ管理
- **Docker + ECR** - コンテナイメージ管理
- **uv** - Python依存関係管理

## 前提条件

- AWS CLI（設定済み）
- Docker
- Terraform
- Python 3.12+
- uv

## クイックスタート

```bash
# 依存関係のインストール
make setup

# 初回デプロイ
make deploy-init

# コード変更後の更新デプロイ
make deploy
```

## コマンド一覧

### 開発

| コマンド | 説明 |
|---------|------|
| `make setup` | 依存関係のインストール |
| `make build` | Dockerイメージをビルド |
| `make push` | イメージをビルド＆ECRにプッシュ |
| `make test` | テストを実行 |
| `make test-cov` | カバレッジ付きでテスト |

### デプロイ

| コマンド | 説明 |
|---------|------|
| `make deploy-init` | 初回デプロイ |
| `make deploy` | 通常のデプロイ |
| `make plan` | インフラ変更のプレビュー |
| `make apply` | インフラを適用 |

### バージョン管理

| コマンド | 説明 |
|---------|------|
| `make get-runtime-info` | Runtime情報を表示 |
| `make list-versions` | バージョン一覧を表示 |
| `make list-endpoints` | エンドポイント一覧を表示 |
| `make update-endpoint` | DEFAULTエンドポイントを更新 |
| `make rollback VERSION=V1` | 指定バージョンにロールバック |

## 設定

| 項目 | デフォルト値 |
|-----|-------------|
| プロジェクト名 | `agentcore` |
| リージョン | `ap-northeast-1` |
| モデル | `jp.anthropic.claude-sonnet-4-5-20250929-v1:0` |

設定変更は `Makefile` または `terraform/variables.tf` を編集してください。

## ドキュメント

| ドキュメント | 内容 |
|-------------|------|
| [デプロイメントガイド](docs/deployment.md) | デプロイ手順、イメージ更新の仕組み |
| [バージョン管理ガイド](docs/version-management.md) | バージョン管理、ロールバック手順 |
| [アーキテクチャ](docs/architecture.md) | システム構成、コンポーネント説明 |
| [開発ガイド](docs/development.md) | 開発環境、テスト方針、Git戦略 |
| [CLAUDE.md](CLAUDE.md) | Claude Code向け開発ガイダンス |

## トラブルシューティング

```bash
# AWS認証エラー
aws login

# ECRログインエラー
make login

# Runtime状態確認
make get-runtime-info
```

## ライセンス

このプロジェクトは個人プロジェクトです。
