# バージョン管理ガイド

このドキュメントでは、AgentCore Runtimeのバージョン管理とエンドポイント操作について説明します。

## 概要

AgentCore Runtimeは、デプロイのたびに新しいバージョンが作成されます。これにより：

- 過去のバージョン履歴が保持される
- 問題発生時にロールバックが可能
- 複数のエンドポイントで異なるバージョンを指定可能

## エンドポイントの種類

### DEFAULTエンドポイント

- 自動的に最新バージョンを指す
- `make deploy` 実行後、即座に新バージョンに切り替わる
- 開発・テスト環境向け

### PRODエンドポイント（オプション）

- 明示的にバージョンを指定する必要がある
- `make rollback` を実行しない限りバージョンは変更されない
- 本番環境での安定運用向け

#### PRODエンドポイントの有効化

```bash
make apply -- -var="enable_prod_endpoint=true"
```

## コマンド一覧

### 情報取得

```bash
# Runtime情報とエンドポイント状態を表示
make get-runtime-info

# Runtime全バージョン一覧を表示
make list-versions

# 全エンドポイント一覧を表示
make list-endpoints
```

### エンドポイント操作

```bash
# DEFAULTエンドポイントを最新バージョンに更新
make update-endpoint

# PRODエンドポイントを指定バージョンにロールバック
make rollback VERSION=V1
```

## バージョン管理の仕組み

### バージョン番号

デプロイのたびに新しいバージョンが自動的に作成されます：

```
V1 → V2 → V3 → ...
```

### バージョン履歴の確認

```bash
make list-versions
```

出力例：

```
Version  Status   Created
V1       ACTIVE   2024-01-01T00:00:00Z
V2       ACTIVE   2024-01-02T00:00:00Z
V3       ACTIVE   2024-01-03T00:00:00Z  ← 最新
```

## ロールバック手順

### 1. 現在の状態を確認

```bash
make get-runtime-info
make list-versions
```

### 2. ロールバック先のバージョンを決定

過去のバージョン一覧から、戻したいバージョンを選択します。

### 3. ロールバックを実行

```bash
make rollback VERSION=V1
```

### 4. 動作確認

ロールバック後、エージェントが正常に動作することを確認してください。

## ベストプラクティス

### 開発環境

- DEFAULTエンドポイントを使用
- `make deploy` で自動的に最新バージョンに更新

### 本番環境

1. PRODエンドポイントを有効化
2. 開発環境でテスト完了後、明示的に `make rollback` でバージョンを更新
3. 問題発生時は即座に前バージョンにロールバック

### リリースフロー例

```bash
# 1. 開発環境にデプロイ（DEFAULTエンドポイント）
make deploy

# 2. 新バージョンを確認
make list-versions

# 3. テスト完了後、PRODエンドポイントを更新
make rollback VERSION=V5

# 4. 問題発生時はロールバック
make rollback VERSION=V4
```
