# アーキテクチャ

このドキュメントでは、プロジェクトのアーキテクチャについて説明します。

## システム構成図

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

## コンポーネント

### AgentCore Runtime

AWSが提供するマネージドエージェントホスティングサービス。

- ECRからコンテナイメージを取得して実行
- エンドポイントを通じてエージェントを呼び出し可能
- バージョン管理機能を提供

### Strands Agent（Docker/ECR）

実際のエージェントロジックを実装したコンテナ。

- `app/main.py` - AgentCoreから呼び出される `handler()` 関数
- `app/agent.py` - Strands frameworkを使用したエージェント設定
- `app/memory.py` - AgentCore Memory統合設定

### AgentCore Memory

エージェントの長期記憶を管理するサービス。

- セッション間で情報を永続化
- ログ・トレース配信設定でオブザーバビリティを確保

### Lambda Invoker

S3イベントをトリガーにAgentCoreを呼び出すLambda関数。

- S3にファイルがアップロードされると起動
- AgentCore Runtimeのエンドポイントを呼び出し

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
├── docs/                # ドキュメント
├── .claude/agents/      # サブエージェント定義
├── Dockerfile           # コンテナイメージ定義
├── Makefile             # 便利なコマンド集
└── pyproject.toml       # Python依存関係
```

## Terraformリソース

### agentcore.tf

- `aws_bedrockagentcore_agent_runtime` - AgentCore Runtime
- `aws_bedrockagentcore_memory` - AgentCore Memory
- エンドポイント設定（DEFAULT, PROD）

### ecr.tf

- `aws_ecr_repository` - Dockerイメージ用リポジトリ

### iam.tf

- AgentCore用のIAMロール
- Bedrock、ECR、CloudWatch Logsへのアクセス権限

### lambda.tf / s3.tf

- S3トリガー用のLambda関数
- トリガー用S3バケット

## イベント構造

AgentCoreはエージェントを以下の形式で呼び出します：

```python
{
  "input": {
    "text": "user input here"
  }
}
```

### セッション情報付きイベント

```python
{
  "input": {
    "text": "user input here"
  },
  "session_id": "session-123",
  "memory_id": "memory-456",
  "actor_id": "user-789"
}
```

## Memory統合

### 設定ファイル

`app/memory.py` で AgentCore Memory との統合を設定：

- Memory ID、Session ID、Actor IDを使用
- Strands frameworkのsession_managerと連携

### オブザーバビリティ

AgentCore Memoryはログ・トレース配信設定をサポート：

- CloudWatch Logsへのログ配信
- トレース情報の収集

詳細は `terraform/agentcore.tf` の Memory リソース定義を参照してください。

## ネットワーク設定

現在のネットワークモードは `PUBLIC` に設定されています（`agentcore.tf`）。

プライベートネットワークが必要な場合は、VPC設定を追加してください。
