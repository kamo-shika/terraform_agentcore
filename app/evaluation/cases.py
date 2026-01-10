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


def create_step2_cases() -> list[Case[dict, str]]:
    """
    Step 2（パターン分析）のテストケースを作成する。

    Returns:
        テストケースのリスト
    """
    return [
        Case[dict, str](
            name="pattern-analysis-tech-trend",
            input={
                "current_summary": """API仕様書の要約:
- RESTful APIエンドポイント（GET/POST /users）
- Bearer認証
- レート制限あり（100req/min）""",
                "past_summaries": [
                    "過去の技術文書: マイクロサービス設計パターンに関する議論",
                    "過去の技術文書: OAuth2認証の実装ガイド",
                    "過去の技術文書: APIゲートウェイの設定方法",
                ],
            },
            expected_output="技術文書のパターン分析（API設計への関心、認証への注目）",
            metadata={
                "category": "technical",
                "difficulty": "medium",
                "expected_patterns": ["API設計", "認証", "セキュリティ"],
            },
        ),
        Case[dict, str](
            name="pattern-analysis-business-focus",
            input={
                "current_summary": """会議メモの要約:
- Q1プロジェクト80%完了
- 予算消化率65%
- 次回会議1/16""",
                "past_summaries": [
                    "過去の会議: 予算超過の懸念が議論された",
                    "過去の会議: プロジェクト遅延リスクの検討",
                    "過去の会議: 新メンバーの追加承認",
                ],
            },
            expected_output="ビジネス文書のパターン分析（進捗管理、予算管理への関心）",
            metadata={
                "category": "business",
                "difficulty": "easy",
                "expected_patterns": ["進捗管理", "予算", "リソース"],
            },
        ),
        Case[dict, str](
            name="pattern-analysis-research",
            input={
                "current_summary": """市場分析レポート要約:
- AI市場35%成長予測
- 生成AI最成長分野
- アジア太平洋が最大市場""",
                "past_summaries": [
                    "過去のレポート: クラウド市場の成長分析",
                    "過去のレポート: DX推進の事例研究",
                    "過去のレポート: リモートワーク関連技術の動向",
                ],
            },
            expected_output="市場調査のパターン分析（テクノロジートレンド、成長市場への関心）",
            metadata={
                "category": "research",
                "difficulty": "hard",
                "expected_patterns": ["テクノロジートレンド", "市場成長", "DX"],
            },
        ),
    ]


def create_step3_cases() -> list[Case[dict, str]]:
    """
    Step 3（プロファイル生成）のテストケースを作成する。

    Returns:
        テストケースのリスト
    """
    return [
        Case[dict, str](
            name="profile-tech-professional",
            input={
                "pattern_analysis": """パターン分析結果:
- API設計・開発に強い関心
- セキュリティ（認証・認可）への注目
- マイクロサービスアーキテクチャへの傾向
- 定期的な技術文書の参照パターン""",
                "past_preferences": "過去の嗜好: Python、クラウドネイティブ技術",
            },
            expected_output="技術者プロファイル（バックエンド開発者、セキュリティ意識が高い）",
            metadata={
                "category": "technical",
                "difficulty": "medium",
                "expected_traits": ["技術志向", "セキュリティ意識", "アーキテクチャ設計"],
            },
        ),
        Case[dict, str](
            name="profile-business-manager",
            input={
                "pattern_analysis": """パターン分析結果:
- プロジェクト進捗管理への関心
- 予算・コスト管理の重視
- チームリソースの最適化傾向
- 定例会議での意思決定パターン""",
                "past_preferences": "過去の嗜好: KPI管理、ガントチャート",
            },
            expected_output="マネージャープロファイル（進捗重視、予算管理型）",
            metadata={
                "category": "business",
                "difficulty": "easy",
                "expected_traits": ["管理志向", "数値重視", "計画的"],
            },
        ),
        Case[dict, str](
            name="profile-strategic-analyst",
            input={
                "pattern_analysis": """パターン分析結果:
- 市場トレンド分析への強い関心
- 新技術の事業インパクト評価
- 競合分析・ポジショニング志向
- 長期的視点での投資判断パターン""",
                "past_preferences": "過去の嗜好: 戦略フレームワーク、データドリブン意思決定",
            },
            expected_output="アナリストプロファイル（戦略思考、市場分析型）",
            metadata={
                "category": "research",
                "difficulty": "hard",
                "expected_traits": ["戦略志向", "分析的", "長期視点"],
            },
        ),
    ]
