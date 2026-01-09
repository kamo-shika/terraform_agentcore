# デプロイメントワークフロー

このルールは、デプロイメント作業時に適用されます。

## AWS認証

デプロイメントやAWSリソース操作を行う前に、AWS認証が必要です。

```bash
aws login                    # AWS SSOで認証を取得
```

**注意事項：**
- `make push`、`make deploy`などのコマンド実行前に認証が必要
- セッションは一定時間で期限切れになるため、定期的に再認証が必要
- 認証エラー（"Your session has expired"）が発生した場合は`aws login`を実行

## デプロイメントコマンド

### 初回デプロイメント

ECRリポジトリ → イメージ → AgentCore Runtime/Memory の順で作成：

```bash
make deploy-init             # 1. ECRリポジトリを作成
                            # 2. イメージをビルド＆プッシュ
                            # 3. AgentCore runtimeとmemoryを作成
```

### 通常のデプロイメント（コード変更時）

```bash
make deploy                  # 1. 新しいイメージをビルド＆プッシュ
                            # 2. Terraformを適用（in-place更新）
```

## バージョン管理

### イメージタグ

- ECRイメージには`latest`タグとGit commit hashタグ（例: `abc1234`）の両方が付与される
- `container_uri`の変更時は`UpdateAgentRuntime` APIでin-place更新される
- 更新のたびにAgentCore Runtimeの新しいバージョン（V1, V2, V3...）が自動作成される

### エンドポイント管理

```bash
make get-runtime-info        # Runtime情報とエンドポイント状態を表示
make list-versions           # Runtime全バージョン一覧を表示
make list-endpoints          # 全エンドポイント一覧を表示
make update-endpoint         # DEFAULTエンドポイントを最新バージョンに更新
make rollback VERSION=V1     # PRODエンドポイントを指定バージョンにロールバック
```

### PRODエンドポイントの有効化

本番環境で手動バージョン管理が必要な場合：

```bash
make apply -- -var="enable_prod_endpoint=true"
```

PRODエンドポイントはDEFAULTと異なり、明示的に`make rollback`を実行しない限りバージョンが変更されません。

## Terraformコマンド

```bash
make init                    # Terraformの初期化
make plan                    # 変更をプレビュー
make apply                   # リソースをデプロイ/更新
make destroy                 # リソースを削除
```

## Dockerコマンド

```bash
make build                   # Dockerイメージをビルド
make login                   # ECRにログイン
make push                    # ECRにビルドしてプッシュ
```
