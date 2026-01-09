"""
評価器の設定。

各ワークフローステップの評価に使用する評価器とルブリックを定義する。
"""

from strands_evals.evaluators import OutputEvaluator

# Step 1（要約）の評価ルブリック
STEP1_RUBRIC = """
## 要約品質の評価基準

以下の観点で評価してください:

### 1. 正確性 (Accuracy)
- 元のファイル内容を正確に反映しているか
- 事実誤認や誤解がないか
- Score 1.0: 完全に正確
- Score 0.5: 軽微な誤りあり
- Score 0.0: 重大な誤り

### 2. 完全性 (Completeness)
- 主要なトピックが網羅されているか
- 重要な数値やデータが含まれているか
- 結論や提案事項が含まれているか
- Score 1.0: 全ての重要ポイントを網羅
- Score 0.5: 一部欠落
- Score 0.0: 主要なポイントが欠落

### 3. 簡潔さ (Conciseness)
- 500文字以内の適切な長さか
- 冗長な表現がないか
- 構造化された読みやすい形式か
- Score 1.0: 簡潔で読みやすい
- Score 0.5: やや冗長
- Score 0.0: 非常に冗長または構造が不明瞭

### 総合スコア計算
- 1.0: 3つの基準全てで優秀
- 0.7: 2つの基準で優秀、1つで普通
- 0.5: 1つの基準で優秀、または全て普通
- 0.3: 一部の基準で問題あり
- 0.0: 複数の基準で不合格
"""


def create_step1_evaluators() -> list:
    """
    Step 1（要約）の評価器を作成する。

    評価基準:
    - 正確性: 元の内容を正しく反映しているか
    - 完全性: 重要なポイントが網羅されているか
    - 簡潔さ: 冗長でなく、要約として適切か

    Returns:
        評価器のリスト
    """
    output_evaluator = OutputEvaluator(
        rubric=STEP1_RUBRIC,
        include_inputs=True,
    )

    return [output_evaluator]
