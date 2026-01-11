"""
評価器の設定。

各ワークフローステップの評価に使用する評価器とルブリックを定義する。
CS通話ログ分析によるライフイベント検出システム向け。
"""

from strands_evals.evaluators import OutputEvaluator

# Step 1（ライフイベント検出）の評価ルブリック
STEP1_RUBRIC = """
## ライフイベント検出品質の評価基準

以下の観点で評価してください：

### 1. 検出精度 (Detection Accuracy)
- 正しいライフイベントを検出できているか
- 見落とし（False Negative）がないか
- 誤検出（False Positive）がないか
- Score 1.0: 全て正確に検出（見落とし・誤検出なし）
- Score 0.5: 一部見落としまたは誤検出がある
- Score 0.0: 重大な見落としまたは誤検出がある

### 2. 確度判定の妥当性 (Confidence Appropriateness)
- high/medium/lowの判定が適切か
- 明示的発言（「引っ越しました」など）→ high
- 暗示的発言（「新しい街に慣れてきて」など）→ medium/low
- 推測レベルの発言 → low
- Score 1.0: 全ての確度判定が適切
- Score 0.5: 一部の確度判定が不適切
- Score 0.0: 多くの確度判定が不適切

### 3. 根拠の適切性 (Evidence Quality)
- evidenceフィールドに適切な発言が引用されているか
- 検出根拠として十分な情報が含まれているか
- 引用が正確か（捏造されていないか）
- Score 1.0: 全ての根拠が適切で正確
- Score 0.5: 一部の根拠が不十分または不正確
- Score 0.0: 根拠が欠落または捏造されている

### 総合スコア計算
- 1.0: 3つの基準全てで優秀
- 0.7: 2つの基準で優秀、1つで普通
- 0.5: 1つの基準で優秀、または全て普通
- 0.3: 一部の基準で問題あり
- 0.0: 複数の基準で不合格
"""


# Step 2（履歴照合・パターン分析）の評価ルブリック
STEP2_RUBRIC = """
## 履歴照合・パターン分析品質の評価基準

以下の観点で評価してください：

### 1. 履歴参照の適切性 (History Reference Appropriateness)
- 過去のライフイベントとの関連付けが正しいか
- 関連する過去の通話内容を適切に参照しているか
- 無関係な履歴を誤って関連付けていないか
- Score 1.0: 全ての履歴参照が適切
- Score 0.5: 一部の履歴参照が不適切
- Score 0.0: 履歴参照が欠落または誤っている

### 2. パターン分析の深さ (Pattern Analysis Depth)
- ライフステージの変遷を適切に分析しているか
- 複数のイベント間の因果関係を把握しているか
- 時系列での傾向変化を認識しているか
- Score 1.0: 深い洞察を含むパターン分析
- Score 0.5: 基本的なパターンのみ認識
- Score 0.0: パターン分析が不十分または欠落

### 3. 整合性 (Consistency)
- Step 1の検出結果との整合性があるか
- 履歴データとの矛盾がないか
- 分析結果が論理的に一貫しているか
- Score 1.0: 完全に整合
- Score 0.5: 軽微な不整合あり
- Score 0.0: 重大な矛盾または不整合

### 総合スコア計算
- 1.0: 3つの基準全てで優秀
- 0.7: 2つの基準で優秀、1つで普通
- 0.5: 1つの基準で優秀、または全て普通
- 0.3: 一部の基準で問題あり
- 0.0: 複数の基準で不合格
"""


# Step 3（レコメンド生成）の評価ルブリック
STEP3_RUBRIC = """
## レコメンド生成品質の評価基準

以下の観点で評価してください：

### 1. レコメンドの妥当性 (Recommendation Validity)
- 検出したライフイベントに対して適切なアクションか
- 顧客のニーズに合致しているか
- 実行可能で具体的なレコメンドか
- Score 1.0: 全てのレコメンドが妥当で適切
- Score 0.5: 一部のレコメンドが不適切
- Score 0.0: レコメンドが不適切または無関係

### 2. 優先度付けの妥当性 (Priority Appropriateness)
- high/medium/lowの優先度判定が適切か
- 緊急性の高いイベント（転職、引っ越し等）→ high
- 将来的なイベント（結婚予定、出産予定等）→ medium
- 補足的な情報 → low
- Score 1.0: 全ての優先度判定が適切
- Score 0.5: 一部の優先度判定が不適切
- Score 0.0: 多くの優先度判定が不適切

### 3. 根拠との紐付け (Evidence Linkage)
- レコメンドがStep 1/2の分析結果に基づいているか
- 推奨理由が明確か
- 飛躍や推測が過度に含まれていないか
- Score 1.0: 全てのレコメンドに明確な根拠
- Score 0.5: 一部のレコメンドの根拠が不明確
- Score 0.0: 根拠なくレコメンドが生成されている

### 総合スコア計算
- 1.0: 3つの基準全てで優秀
- 0.7: 2つの基準で優秀、1つで普通
- 0.5: 1つの基準で優秀、または全て普通
- 0.3: 一部の基準で問題あり
- 0.0: 複数の基準で不合格
"""


def create_step1_evaluators() -> list:
    """
    Step 1（ライフイベント検出）の評価器を作成する。

    評価基準:
    - 検出精度: 正しいライフイベントを検出できているか
    - 確度判定の妥当性: high/medium/lowの判定が適切か
    - 根拠の適切性: evidenceフィールドに適切な発言が引用されているか

    Returns:
        評価器のリスト
    """
    output_evaluator = OutputEvaluator(
        rubric=STEP1_RUBRIC,
        include_inputs=True,
    )

    return [output_evaluator]


def create_step2_evaluators() -> list:
    """
    Step 2（履歴照合・パターン分析）の評価器を作成する。

    評価基準:
    - 履歴参照の適切性: 過去のイベントとの関連付けが正しいか
    - パターン分析の深さ: ライフステージの変遷を適切に分析しているか
    - 整合性: Step 1の検出結果との整合性があるか

    Returns:
        評価器のリスト
    """
    output_evaluator = OutputEvaluator(
        rubric=STEP2_RUBRIC,
        include_inputs=True,
    )

    return [output_evaluator]


def create_step3_evaluators() -> list:
    """
    Step 3（レコメンド生成）の評価器を作成する。

    評価基準:
    - レコメンドの妥当性: 検出したライフイベントに対して適切なアクションか
    - 優先度付けの妥当性: high/medium/lowの判定が適切か
    - 根拠との紐付け: レコメンドがStep 1/2の分析結果に基づいているか

    Returns:
        評価器のリスト
    """
    output_evaluator = OutputEvaluator(
        rubric=STEP3_RUBRIC,
        include_inputs=True,
    )

    return [output_evaluator]
