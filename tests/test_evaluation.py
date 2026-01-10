"""
app/evaluation/ のテスト。

評価フレームワークの各コンポーネントをテストする。
（新ユースケース向けに実装予定）
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
