"""
評価用テストケースの定義。

各ワークフローステップの評価に使用するテストケースを提供する。
"""

from strands_evals import Case


def create_step1_cases() -> list[Case[dict, str]]:
    """
    Step 1（S3ファイル要約）のテストケースを作成する。

    Returns:
        テストケースのリスト
    """
    return [
        Case[dict, str](
            name="technical-document-summary",
            input={
                "s3_info": {"bucket": "test-bucket", "key": "docs/api-spec.md"},
                "file_content": """# API仕様書

## エンドポイント

### GET /users
ユーザー一覧を取得します。

### POST /users
新しいユーザーを作成します。

## 認証
Bearer トークンを使用した認証が必要です。

## レート制限
1分あたり100リクエストまで。
""",
            },
            expected_output="API仕様書の要約（エンドポイント、認証、レート制限を含む）",
            metadata={
                "category": "technical",
                "difficulty": "medium",
                "expected_topics": ["API", "エンドポイント", "認証"],
            },
        ),
        Case[dict, str](
            name="meeting-notes-summary",
            input={
                "s3_info": {"bucket": "test-bucket", "key": "notes/meeting-2025-01.txt"},
                "file_content": """会議メモ 2025年1月9日

参加者: 田中、佐藤、鈴木

議題:
1. Q1プロジェクト進捗
   - 開発フェーズは80%完了
   - テストは来週開始予定

2. 予算確認
   - 現在の消化率: 65%
   - 追加予算の申請検討

3. 次回会議
   - 1月16日 14:00

アクションアイテム:
- 田中: テスト計画書作成
- 佐藤: 予算申請書作成
""",
            },
            expected_output="会議メモの要約（進捗、予算、アクションアイテムを含む）",
            metadata={
                "category": "business",
                "difficulty": "easy",
                "expected_topics": ["プロジェクト進捗", "予算", "アクションアイテム"],
            },
        ),
        Case[dict, str](
            name="research-report-summary",
            input={
                "s3_info": {"bucket": "test-bucket", "key": "reports/market-analysis.pdf"},
                "file_content": """市場分析レポート

エグゼクティブサマリー:
AI市場は2025年に前年比35%成長が予測される。

主要な発見:
1. 生成AI分野が最も急成長（+50%）
2. エンタープライズ導入が加速
3. アジア太平洋地域が最大の成長市場

推奨事項:
- 生成AI製品への投資強化
- アジア市場への展開加速
- パートナーシップ戦略の見直し

リスク要因:
- 規制環境の不確実性
- 技術人材の不足
""",
            },
            expected_output="市場分析レポートの要約（成長予測、主要発見、推奨事項を含む）",
            metadata={
                "category": "research",
                "difficulty": "hard",
                "expected_topics": ["市場成長", "生成AI", "推奨事項"],
            },
        ),
    ]
