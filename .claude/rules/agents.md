# サブエージェント利用ガイド

このルールは、タスク実行時のサブエージェント選択に適用されます。

## エージェント一覧

| エージェント | 専門領域 | 定義ファイル |
|-------------|---------|-------------|
| `terraform-specialist` | Terraform/AWSインフラ構築、IAM設計 | `.claude/agents/terraform-specialist.md` |
| `python-developer` | Pythonアプリケーション、Lambda関数実装 | `.claude/agents/python-developer.md` |
| `strands-agent-developer` | Strands Agents、AgentCore統合 | `.claude/agents/strands-agent-developer.md` |
| `integrator` | 統合検証、デプロイ確認 | `.claude/agents/integrator.md` |
| `test-specialist` | TDD、テスト実装、カバレッジ分析 | `.claude/agents/test-specialist.md` |
| `cloudwatch-investigator` | CloudWatchログ調査、エラー分析 | `.claude/agents/cloudwatch-investigator.md` |

## 使用方法

```python
Task(subagent_type="python-developer", prompt="xxx機能を実装してください")
```

## エージェント選択の指針

### terraform-specialist を使う場合
- Terraform設定の作成・変更
- IAMロール・ポリシーの設計
- AWSリソースのプロビジョニング

### python-developer を使う場合
- `app/`配下のPythonコード実装
- Lambda関数の開発
- ユーティリティモジュールの作成

### strands-agent-developer を使う場合
- Strands Agentsの設定
- AgentCore Memory/Runtime統合
- プロンプト設計

### integrator を使う場合
- 複数コンポーネントの結合テスト
- デプロイ後の動作確認
- エンドツーエンドの検証

### test-specialist を使う場合
- TDDでのテスト作成（Red-Green-Refactor）
- カバレッジ分析
- テストのデバッグ

### cloudwatch-investigator を使う場合
- CloudWatchログの検索・分析
- エラーの特定・原因調査
- Logs Insightsクエリの実行

## 注意事項

- 各エージェントは`worktree.md`のルールに従ってブランチで作業する
- TDDルール（`tdd.md`）はPythonコード実装時に必須
