"""
app/evaluation/ のテスト。

評価フレームワークの各コンポーネントをテストする。
"""

import pytest


class TestCreateStep1Cases:
    """Step 1テストケース作成のテスト"""

    def test_returns_list(self):
        """テストケースがリストを返すことを確認"""
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        assert isinstance(cases, list)

    def test_cases_have_required_fields(self):
        """各ケースが必須フィールドを持つことを確認（空リストでもパス）"""
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        for case in cases:
            assert case.name, "ケース名が必要"
            assert case.input is not None, "入力が必要"


class TestCreateStep1Evaluators:
    """Step 1評価器作成のテスト"""

    def test_returns_list(self):
        """評価器がリストを返すことを確認"""
        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        assert isinstance(evaluators, list)

    def test_creates_evaluators(self):
        """評価器が1つ以上作成されることを確認"""
        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        assert len(evaluators) >= 1

    def test_includes_output_evaluator(self):
        """OutputEvaluatorが含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        assert any(isinstance(e, OutputEvaluator) for e in evaluators)

    def test_output_evaluator_has_rubric(self):
        """OutputEvaluatorにルブリックが設定されていることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert output_evaluator.rubric, "ルブリックが設定されている必要がある"

    def test_rubric_contains_detection_accuracy(self):
        """ルブリックに検出精度の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "検出" in output_evaluator.rubric or "Detection" in output_evaluator.rubric

    def test_rubric_contains_confidence_criteria(self):
        """ルブリックに確度判定の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "確度" in output_evaluator.rubric or "Confidence" in output_evaluator.rubric

    def test_rubric_contains_evidence_criteria(self):
        """ルブリックに根拠の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step1_evaluators

        evaluators = create_step1_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "根拠" in output_evaluator.rubric or "Evidence" in output_evaluator.rubric


class TestStep1Rubric:
    """Step 1ルブリックのテスト"""

    def test_rubric_constant_exists(self):
        """STEP1_RUBRICが定義されていることを確認"""
        from app.evaluation.evaluators import STEP1_RUBRIC

        assert STEP1_RUBRIC is not None
        assert isinstance(STEP1_RUBRIC, str)
        assert len(STEP1_RUBRIC) > 0


class TestEvaluationRunner:
    """評価実行のテスト"""

    def test_runner_module_exists(self):
        """runner モジュールが存在することを確認"""
        from app.evaluation import runner

        assert runner is not None

    def test_run_step1_evaluation_function_exists(self):
        """run_step1_evaluation 関数が存在することを確認"""
        from app.evaluation.runner import run_step1_evaluation

        assert callable(run_step1_evaluation)


class TestEvaluationPackage:
    """評価パッケージの構造テスト"""

    def test_package_exports(self):
        """パッケージから必要な関数がエクスポートされることを確認"""
        from app.evaluation import (
            create_step1_cases,
            create_step1_evaluators,
            run_step1_evaluation,
        )

        assert callable(create_step1_cases)
        assert callable(create_step1_evaluators)
        assert callable(run_step1_evaluation)


class TestStep1Prompt:
    """Step 1プロンプトのテスト"""

    def test_step1_prompt_exists(self):
        """Step 1プロンプトファイル（step1.md）が存在することを確認"""
        from pathlib import Path

        prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "workflow" / "step1.md"
        assert prompt_path.exists(), "Step 1プロンプトファイル（step1.md）が存在する必要がある"

    def test_prompt_does_not_contain_s3_tool_instruction(self):
        """プロンプトにS3ツール取得指示が含まれないことを確認（S3取得はworkflow.pyで制御）"""
        from pathlib import Path

        prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "workflow" / "step1.md"
        content = prompt_path.read_text(encoding="utf-8")
        # s3からファイルを直接取得する指示が含まれていないことを確認
        assert "s3からファイルを取得" not in content.lower(), "プロンプトにS3取得指示が含まれてはいけない"

    def test_runner_loads_prompt_without_s3_instruction(self):
        """runner.pyが読み込むプロンプトにS3直接取得指示が含まれないことを確認"""
        from app.evaluation.runner import _load_summarize_prompt

        prompt = _load_summarize_prompt()
        # プロンプトにはS3直接取得の指示が含まれない
        assert "s3からファイルを取得" not in prompt.lower(), "プロンプトにS3直接取得指示が含まれてはいけない"


class TestCreateStep2Cases:
    """Step 2テストケース作成のテスト"""

    def test_returns_list(self):
        """テストケースがリストを返すことを確認"""
        from app.evaluation.cases import create_step2_cases

        cases = create_step2_cases()
        assert isinstance(cases, list)

    def test_cases_have_required_fields(self):
        """各ケースが必須フィールドを持つことを確認（空リストでもパス）"""
        from app.evaluation.cases import create_step2_cases

        cases = create_step2_cases()
        for case in cases:
            assert case.name, "ケース名が必要"
            assert case.input is not None, "入力が必要"


class TestCreateStep2Evaluators:
    """Step 2評価器作成のテスト"""

    def test_returns_list(self):
        """評価器がリストを返すことを確認"""
        from app.evaluation.evaluators import create_step2_evaluators

        evaluators = create_step2_evaluators()
        assert isinstance(evaluators, list)

    def test_creates_evaluators(self):
        """評価器が1つ以上作成されることを確認"""
        from app.evaluation.evaluators import create_step2_evaluators

        evaluators = create_step2_evaluators()
        assert len(evaluators) >= 1

    def test_includes_output_evaluator(self):
        """OutputEvaluatorが含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step2_evaluators

        evaluators = create_step2_evaluators()
        assert any(isinstance(e, OutputEvaluator) for e in evaluators)

    def test_output_evaluator_has_rubric(self):
        """OutputEvaluatorにルブリックが設定されていることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step2_evaluators

        evaluators = create_step2_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert output_evaluator.rubric, "ルブリックが設定されている必要がある"

    def test_rubric_contains_history_reference(self):
        """ルブリックに履歴参照の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step2_evaluators

        evaluators = create_step2_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "履歴" in output_evaluator.rubric or "過去" in output_evaluator.rubric

    def test_rubric_contains_pattern_analysis(self):
        """ルブリックにパターン分析の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step2_evaluators

        evaluators = create_step2_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "パターン" in output_evaluator.rubric or "分析" in output_evaluator.rubric


class TestStep2Rubric:
    """Step 2ルブリックのテスト"""

    def test_rubric_constant_exists(self):
        """STEP2_RUBRICが定義されていることを確認"""
        from app.evaluation.evaluators import STEP2_RUBRIC

        assert STEP2_RUBRIC is not None
        assert isinstance(STEP2_RUBRIC, str)
        assert len(STEP2_RUBRIC) > 0


class TestCreateStep3Cases:
    """Step 3テストケース作成のテスト"""

    def test_returns_list(self):
        """テストケースがリストを返すことを確認"""
        from app.evaluation.cases import create_step3_cases

        cases = create_step3_cases()
        assert isinstance(cases, list)

    def test_cases_have_required_fields(self):
        """各ケースが必須フィールドを持つことを確認（空リストでもパス）"""
        from app.evaluation.cases import create_step3_cases

        cases = create_step3_cases()
        for case in cases:
            assert case.name, "ケース名が必要"
            assert case.input is not None, "入力が必要"


class TestCreateStep3Evaluators:
    """Step 3評価器作成のテスト"""

    def test_returns_list(self):
        """評価器がリストを返すことを確認"""
        from app.evaluation.evaluators import create_step3_evaluators

        evaluators = create_step3_evaluators()
        assert isinstance(evaluators, list)

    def test_creates_evaluators(self):
        """評価器が1つ以上作成されることを確認"""
        from app.evaluation.evaluators import create_step3_evaluators

        evaluators = create_step3_evaluators()
        assert len(evaluators) >= 1

    def test_includes_output_evaluator(self):
        """OutputEvaluatorが含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step3_evaluators

        evaluators = create_step3_evaluators()
        assert any(isinstance(e, OutputEvaluator) for e in evaluators)

    def test_output_evaluator_has_rubric(self):
        """OutputEvaluatorにルブリックが設定されていることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step3_evaluators

        evaluators = create_step3_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert output_evaluator.rubric, "ルブリックが設定されている必要がある"

    def test_rubric_contains_recommendation_validity(self):
        """ルブリックにレコメンド妥当性の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step3_evaluators

        evaluators = create_step3_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "レコメンド" in output_evaluator.rubric or "推奨" in output_evaluator.rubric

    def test_rubric_contains_priority_criteria(self):
        """ルブリックに優先度の評価基準が含まれることを確認"""
        from strands_evals.evaluators import OutputEvaluator

        from app.evaluation.evaluators import create_step3_evaluators

        evaluators = create_step3_evaluators()
        output_evaluator = next(e for e in evaluators if isinstance(e, OutputEvaluator))
        assert "優先" in output_evaluator.rubric or "priority" in output_evaluator.rubric.lower()


class TestStep3Rubric:
    """Step 3ルブリックのテスト"""

    def test_rubric_constant_exists(self):
        """STEP3_RUBRICが定義されていることを確認"""
        from app.evaluation.evaluators import STEP3_RUBRIC

        assert STEP3_RUBRIC is not None
        assert isinstance(STEP3_RUBRIC, str)
        assert len(STEP3_RUBRIC) > 0


class TestStep2Step3Runner:
    """Step 2/3評価実行のテスト"""

    def test_run_step2_evaluation_function_exists(self):
        """run_step2_evaluation 関数が存在することを確認"""
        from app.evaluation.runner import run_step2_evaluation

        assert callable(run_step2_evaluation)

    def test_run_step3_evaluation_function_exists(self):
        """run_step3_evaluation 関数が存在することを確認"""
        from app.evaluation.runner import run_step3_evaluation

        assert callable(run_step3_evaluation)


class TestStep2Step3PackageExports:
    """Step 2/3パッケージエクスポートのテスト"""

    def test_step2_exports(self):
        """Step 2関連の関数がエクスポートされることを確認"""
        from app.evaluation import (
            create_step2_cases,
            create_step2_evaluators,
            run_step2_evaluation,
        )

        assert callable(create_step2_cases)
        assert callable(create_step2_evaluators)
        assert callable(run_step2_evaluation)

    def test_step3_exports(self):
        """Step 3関連の関数がエクスポートされることを確認"""
        from app.evaluation import (
            create_step3_cases,
            create_step3_evaluators,
            run_step3_evaluation,
        )

        assert callable(create_step3_cases)
        assert callable(create_step3_evaluators)
        assert callable(run_step3_evaluation)
