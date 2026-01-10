"""
app/evaluation/ のテスト。

評価フレームワークの各コンポーネントをテストする。
TDD: Red -> Green -> Refactor
"""

import pytest


class TestCreateStep1Cases:
    """Step 1テストケース作成のテスト"""

    def test_creates_non_empty_list(self):
        """テストケースが空でないリストを返すことを確認"""
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        assert len(cases) > 0

    def test_cases_have_required_fields(self):
        """各ケースが必須フィールドを持つことを確認"""
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        for case in cases:
            assert case.name, "ケース名が必要"
            assert case.input is not None, "入力が必要"
            assert "s3_info" in case.input, "s3_infoが入力に含まれる必要がある"

    def test_cases_have_s3_bucket_and_key(self):
        """各ケースのs3_infoにbucketとkeyが含まれることを確認"""
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        for case in cases:
            s3_info = case.input["s3_info"]
            assert "bucket" in s3_info, "bucketが必要"
            assert "key" in s3_info, "keyが必要"

    def test_cases_have_metadata(self):
        """各ケースにメタデータが含まれることを確認"""
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        for case in cases:
            assert case.metadata is not None, "メタデータが必要"
            assert "category" in case.metadata, "categoryがメタデータに含まれる必要がある"


class TestCreateStep1Evaluators:
    """Step 1評価器作成のテスト"""

    def test_creates_evaluators(self):
        """評価器が作成されることを確認"""
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
        # ルブリックに評価基準が含まれていることを確認
        assert "正確性" in output_evaluator.rubric or "Accuracy" in output_evaluator.rubric


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


class TestSummarizePrompt:
    """要約プロンプトのテスト（評価・本番共通）"""

    def test_summarize_prompt_exists(self):
        """要約プロンプトファイル（step1.md）が存在することを確認"""
        from pathlib import Path

        prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "workflow" / "step1.md"
        assert prompt_path.exists(), "要約プロンプトファイル（step1.md）が存在する必要がある"

    def test_prompt_does_not_contain_s3_tool_instruction(self):
        """プロンプトにS3ツール取得指示が含まれないことを確認（S3取得はworkflow.pyで制御）"""
        from pathlib import Path

        prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "workflow" / "step1.md"
        content = prompt_path.read_text(encoding="utf-8")
        # s3からファイルを直接取得する指示が含まれていないことを確認
        # (use_awsツールの使用は許可されている)
        assert "s3からファイルを取得" not in content.lower(), "プロンプトにS3取得指示が含まれてはいけない"

    def test_prompt_contains_summarization_instructions(self):
        """プロンプトに要約の基本指示が含まれることを確認"""
        from pathlib import Path

        prompt_path = Path(__file__).parent.parent / "app" / "prompts" / "workflow" / "step1.md"
        content = prompt_path.read_text(encoding="utf-8")
        # 基本的な要約指示が含まれていることを確認
        assert "要約" in content or "分析" in content, "要約または分析の指示が必要"
        assert "500文字" in content or "簡潔" in content, "長さ制限または簡潔さの指示が必要"

    def test_runner_loads_prompt_without_s3_instruction(self):
        """runner.pyが読み込むプロンプトにS3直接取得指示が含まれないことを確認"""
        from app.evaluation.runner import _load_summarize_prompt

        prompt = _load_summarize_prompt()
        # プロンプトにはS3直接取得の指示が含まれない
        assert "s3からファイルを取得" not in prompt.lower(), "プロンプトにS3直接取得指示が含まれてはいけない"
