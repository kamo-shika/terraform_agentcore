# デプロイメントガイド

このドキュメントでは、AgentCoreのデプロイメントワークフローについて説明します。

## 前提条件

デプロイを実行する前に、以下を確認してください：

- AWS CLIがインストール・設定済み
- Dockerがインストール済み
- Terraformがインストール済み
- AWS認証が有効（期限切れの場合は `aws login` を実行）

## デプロイメントワークフロー

### 初回デプロイ

初めてプロジェクトをデプロイする場合は、以下のコマンドを実行します：

```bash
make deploy-init
```

このコマンドは以下の順序で実行されます：

1. **ECRリポジトリの作成** - Dockerイメージを保存するリポジトリを作成
2. **イメージのビルド＆プッシュ** - エージェントのDockerイメージをビルドしてECRにプッシュ
3. **AgentCore RuntimeとMemoryの作成** - Terraformですべてのリソースをプロビジョニング

### 通常のデプロイ（コード変更時）

エージェントのコードを変更した後は、以下のコマンドでデプロイします：

```bash
make deploy
```

このコマンドは以下を実行します：

1. **新しいイメージをビルド＆プッシュ**
   - `latest` タグと Git commit hash タグ（例: `abc1234`）の両方を付与
2. **Terraformを適用**
   - `container_uri` の変更を検知
   - `UpdateAgentRuntime` APIでin-place更新（destroy→createではない）

## イメージ変更検知の仕組み

### タグ付け戦略

ECRにプッシュされるイメージには2つのタグが付与されます：

| タグ | 用途 |
|-----|------|
| `latest` | 常に最新のイメージを指す |
| Git commit hash | 特定のコミットに紐づくイメージを識別 |

### In-Place更新

Terraformは `container_uri` の変更を検知すると、AgentCore Runtimeをin-place更新します：

- リソースの再作成（destroy→create）は発生しない
- `UpdateAgentRuntime` APIが呼び出される
- 新しいバージョン（V1, V2, V3...）が自動的に作成される
- 既存のバージョン履歴は保持される

## 個別コマンド

### Dockerイメージ操作

```bash
# イメージをビルドのみ
make build

# ECRにログイン
make login

# ビルド＆プッシュ
make push
```

### Terraform操作

```bash
# 初期化
make init

# 変更のプレビュー
make plan

# 適用
make apply

# 破棄
make destroy
```

## トラブルシューティング

### AWS認証エラー

セッションが期限切れの場合：

```bash
aws login
```

### ECRログインエラー

Docker認証が必要な場合：

```bash
make login
```

### デプロイが反映されない

1. `make get-runtime-info` でRuntimeの状態を確認
2. 必要に応じて `make update-endpoint` でエンドポイントを更新

詳細なバージョン管理については [version-management.md](./version-management.md) を参照してください。
