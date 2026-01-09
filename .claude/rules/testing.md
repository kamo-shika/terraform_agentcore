# テスト方針

このルールは、テストコードの作成・実行時に適用されます。

## 重要原則

**モックはなるべく使用せず、実際の環境でテストすることを優先する。**

## テスト方針

- **実際のコードで動作確認**: 可能な限り実装されたコードそのものをテスト
- **インテグレーションテスト**: コンポーネント間の統合も実際に動作確認
- **エンドツーエンドテスト**: 実際のユースケースに沿った動作確認

## モック使用の判断基準

### モックを使用してよい場合（最小限）

- 課金が発生する外部サービス（EC2起動、S3への大量書き込みなど）
- 制御できない外部依存（サードパーティAPIなど）
- 時間がかかりすぎる処理（数分以上）

### 避けるべきモックの使用

- 自分たちのコード内の関数をモック化する
- boto3クライアントを安易にモック化する
- テストの簡便さのためだけにモックを使用する

## テストコマンド

```bash
# 全テストを実行
make test

# カバレッジ付きでテストを実行
make test-cov

# 特定のテストファイルを実行
uv run pytest tests/test_xxx.py -v

# 特定のテスト関数を実行
uv run pytest tests/test_xxx.py::TestClass::test_method -v
```

## フィクスチャの活用

`tests/conftest.py`に定義された共通フィクスチャを活用すること：

| フィクスチャ | 用途 |
|-------------|------|
| `sample_event` | 標準的なAgentCoreイベント |
| `sample_event_with_session` | セッション情報付きイベント |
| `sample_s3_event` | S3ファイル処理用イベント |
| `empty_event` / `invalid_event` | エラーハンドリングテスト用 |
| `clean_env` | 環境変数をクリーンにする |
| `set_memory_env` | Memory関連環境変数を設定 |

## テストディレクトリ構造

```
tests/
├── __init__.py              # テストパッケージ
├── conftest.py              # 共通フィクスチャとpytest設定
├── test_main.py             # app/main.pyのテスト
├── test_agent.py            # app/agent.pyのテスト
├── test_memory.py           # app/memory.pyのテスト
├── test_tools.py            # app/tools.pyのテスト
├── test_workflow.py         # app/workflow.pyのテスト
├── test_config.py           # app/config.pyのテスト
├── test_prompts.py          # app/prompts/のテスト
├── test_server.py           # app/server.pyのテスト
└── fixtures/                # テストデータとヘルパー
    └── __init__.py
```
