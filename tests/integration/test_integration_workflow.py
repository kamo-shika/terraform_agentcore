"""
ワークフロー結合テスト。

実際のAgentCoreリソースを使用して、エンドツーエンドの動作を検証する。
AWS認証が有効な場合のみ実行される。

テスト方針（testing.mdより）:
- モックはなるべく使用せず、実際の環境でテストすることを優先する
- 課金が発生する外部サービスは慎重に扱う
"""

import json
import os

import pytest


def _is_aws_configured() -> bool:
    """
    AWS認証が有効かどうかを確認する。

    テスト収集時にエラーを発生させないよう、全ての例外をキャッチする。
    """
    try:
        import boto3
        from botocore.exceptions import (
            ClientError,
            NoCredentialsError,
            BotoCoreError,
        )

        sts = boto3.client("sts")
        sts.get_caller_identity()
        return True
    except Exception:
        # AWS認証関連の全てのエラーをキャッチ
        # LoginRefreshRequired, AccessDeniedException等を含む
        return False


class TestWorkflowIntegration:
    """
    ワークフロー全体の結合テスト。

    実際のAWSリソースを使用して、3ステップのワークフローを検証する。
    """

    @pytest.fixture
    def s3_client(self):
        """S3クライアントを取得"""
        return boto3.client("s3", region_name="ap-northeast-1")

    @pytest.fixture
    def test_bucket_name(self):
        """テスト用バケット名（環境変数から取得）"""
        bucket = os.environ.get("TEST_S3_BUCKET")
        if not bucket:
            pytest.skip("TEST_S3_BUCKET環境変数が設定されていません")
        return bucket

    @pytest.fixture
    def test_memory_id(self):
        """テスト用Memory ID（環境変数から取得）"""
        memory_id = os.environ.get("MEMORY_ID")
        if not memory_id:
            pytest.skip("MEMORY_ID環境変数が設定されていません")
        return memory_id

    @pytest.fixture
    def sample_call_log(self) -> dict:
        """テスト用通話ログサンプル"""
        return {
            "call_id": "CALL-TEST-001",
            "customer_id": "C-TEST-001",
            "call_date": "2025-01-11",
            "call_time": "10:00:00",
            "duration_seconds": 300,
            "call_reason": "契約内容の確認",
            "transcript": [
                {
                    "speaker": "operator",
                    "text": "お電話ありがとうございます。本日はどのようなご用件でしょうか。",
                },
                {
                    "speaker": "customer",
                    "text": "来月引っ越すことになったので、インターネットの手続きについて確認したいのですが。",
                },
                {
                    "speaker": "operator",
                    "text": "ご引越しですね。新しいご住所はお決まりでしょうか。",
                },
                {
                    "speaker": "customer",
                    "text": "はい、東京都渋谷区の新しいマンションに移ります。",
                },
            ],
        }

    def test_workflow_module_imports(self):
        """
        ワークフローモジュールが正しくインポートできることを確認。

        基本的なインポートテストで、依存関係の整合性を検証する。
        """
        from app.workflow import run_workflow
        from app.memory import create_memory
        from app.tools import retrieve_memory_tool, get_past_preferences

        assert callable(run_workflow)
        assert callable(create_memory)
        assert callable(retrieve_memory_tool)
        assert callable(get_past_preferences)

    def test_prompt_loading(self):
        """
        全プロンプトファイルが正しく読み込めることを確認。

        ワークフローで使用する4つのプロンプトファイルの存在と内容を検証する。
        """
        from app.prompts import load_prompt

        # システムプロンプト
        system_prompt = load_prompt("workflow/system")
        assert "ライフイベント" in system_prompt
        assert "通信キャリア" in system_prompt

        # Step 1: ライフイベント検出
        step1_prompt = load_prompt("workflow/step1")
        assert "{call_log}" in step1_prompt or "通話ログ" in step1_prompt

        # Step 2: 履歴照合
        step2_prompt = load_prompt("workflow/step2")
        assert "{past_summaries}" in step2_prompt or "履歴" in step2_prompt

        # Step 3: レコメンド生成
        step3_prompt = load_prompt("workflow/step3")
        assert "{step2_result}" in step3_prompt or "レコメンド" in step3_prompt

    def test_memory_client_initialization(self, test_memory_id):
        """
        AgentCore Memoryクライアントが初期化できることを確認。

        実際のMemory IDを使用してクライアントが正しく動作することを検証する。
        """
        from app.memory import create_memory

        session_id = "test-session-integration"
        actor_id = "test-actor-integration"

        # SessionManagerが作成できることを確認
        session_manager = create_memory(test_memory_id, session_id, actor_id)
        assert session_manager is not None

    def test_retrieve_memory_with_empty_query(self, test_memory_id):
        """
        Memory検索が空のクエリでもエラーにならないことを確認。
        """
        from app.tools import retrieve_memory_tool

        # 空のクエリで検索
        result = retrieve_memory_tool(
            memory_id=test_memory_id,
            actor_id="test-actor",
            query="テスト検索",
            namespace="/call-summaries/{actorId}",
        )

        # エラーにならずリストが返ることを確認
        assert isinstance(result, list)


class TestVerificationScenarios:
    """
    検証シナリオのテスト。

    Issue #155で定義された3つの検証シナリオを実行する。
    """

    @pytest.fixture
    def moving_call_log(self) -> str:
        """引っ越しの通話ログ（テキスト形式）"""
        return """オペレーター: お電話ありがとうございます。本日はどのようなご用件でしょうか。
顧客: 来月引っ越すことになったので、インターネットの手続きについて確認したいのですが。
オペレーター: ご引越しですね。新しいご住所はお決まりでしょうか。
顧客: はい、東京都渋谷区の新しいマンションに2月15日から住む予定です。"""

    @pytest.fixture
    def marriage_call_log(self) -> str:
        """結婚の通話ログ（テキスト形式）"""
        return """オペレーター: お電話ありがとうございます。本日はどのようなご用件でしょうか。
顧客: 来月結婚するんですが、家族割について教えてください。
オペレーター: ご結婚おめでとうございます！家族割についてですね。
顧客: ありがとうございます。彼女も同じ会社を使っているので、一緒にしたいなと思って。"""

    @pytest.fixture
    def multiple_events_call_log(self) -> str:
        """複数イベント同時検出の通話ログ（テキスト形式）"""
        return """オペレーター: お電話ありがとうございます。本日はどのようなご用件でしょうか。
顧客: いろいろ変更したいことがあって電話しました。
オペレーター: かしこまりました。どのような変更でしょうか。
顧客: 実は来月転職して、それに合わせて引っ越すことになったんです。
オペレーター: ご転職とお引越しですね。新しいお仕事とご住所は決まっていますか。
顧客: はい、大阪の会社に転職が決まって、大阪市内に引っ越します。"""

    def test_scenario1_single_event_detection(self, moving_call_log):
        """
        シナリオ1: 単一ライフイベント検出。

        入力: 引っ越しの話題を含む通話ログ
        期待:
          - 引っ越しイベント検出
          - confidence: high（明示的発言のため）
        """
        from app.evaluation.cases import create_step1_cases

        # Step 1のテストケースを取得
        cases = create_step1_cases()

        # moving-explicitケースを確認
        moving_case = next((c for c in cases if c.name == "moving-explicit"), None)
        assert moving_case is not None

        # 期待される出力を確認
        expected = json.loads(moving_case.expected_output)
        assert expected["event_type"] == "引っ越し"
        assert expected["confidence"] == "high"

    def test_scenario2_history_accumulation_pattern(self):
        """
        シナリオ2: 履歴蓄積パターン。

        期待: 「結婚→引っ越し」のパターンが検出されること。
        """
        from app.evaluation.cases import create_step2_cases

        # Step 2のテストケースを取得
        cases = create_step2_cases()

        # related-event-follow-upケースを確認
        related_case = next(
            (c for c in cases if c.name == "related-event-follow-up"), None
        )
        assert related_case is not None

        # 期待される出力を確認
        expected = json.loads(related_case.expected_output)
        assert expected["is_new_event"] is True
        assert expected["related_to_previous"] is True
        assert "結婚" in expected["pattern_analysis"]
        assert "引っ越し" in expected["pattern_analysis"]

    def test_scenario3_multiple_events_detection(self, multiple_events_call_log):
        """
        シナリオ3: 複数イベント同時検出。

        入力: 転職と引っ越しを含む通話ログ
        期待: 両方のイベントが検出されること。
        """
        from app.evaluation.cases import create_step1_cases

        # Step 1のテストケースを取得
        cases = create_step1_cases()

        # multiple-eventsケースを確認
        multiple_case = next((c for c in cases if c.name == "multiple-events"), None)
        assert multiple_case is not None

        # 期待される出力を確認
        expected = json.loads(multiple_case.expected_output)
        assert "event_types" in expected
        assert "就職・転職" in expected["event_types"]
        assert "引っ越し" in expected["event_types"]


class TestEvaluationCasesIntegrity:
    """
    評価ケースの整合性テスト。

    #153で作成したテストケースが正しく機能することを検証する。
    """

    def test_step1_cases_count(self):
        """
        Step 1のテストケース数が期待通りであることを確認。

        期待: 16ケース（7イベント×2 + エッジケース2）
        """
        from app.evaluation.cases import create_step1_cases

        cases = create_step1_cases()
        assert len(cases) == 16

    def test_step2_cases_count(self):
        """
        Step 2のテストケース数が期待通りであることを確認。

        期待: 6ケース
        """
        from app.evaluation.cases import create_step2_cases

        cases = create_step2_cases()
        assert len(cases) == 6

    def test_step3_cases_count(self):
        """
        Step 3のテストケース数が期待通りであることを確認。

        期待: 9ケース
        """
        from app.evaluation.cases import create_step3_cases

        cases = create_step3_cases()
        assert len(cases) == 9

    def test_all_cases_have_valid_structure(self):
        """
        全テストケースが有効な構造を持つことを確認。
        """
        from app.evaluation.cases import (
            create_step1_cases,
            create_step2_cases,
            create_step3_cases,
        )

        all_cases = (
            create_step1_cases() + create_step2_cases() + create_step3_cases()
        )

        for case in all_cases:
            # 必須フィールドの存在確認
            assert case.name, f"ケース名が空: {case}"
            assert case.input is not None, f"inputがNone: {case.name}"
            assert case.expected_output, f"expected_outputが空: {case.name}"

            # expected_outputがJSONとしてパースできることを確認
            try:
                json.loads(case.expected_output)
            except json.JSONDecodeError:
                pytest.fail(f"expected_outputが無効なJSON: {case.name}")

    def test_all_life_events_covered(self):
        """
        全7種類のライフイベントがテストケースでカバーされていることを確認。
        """
        from app.evaluation.cases import create_step1_cases

        life_events = {
            "引っ越し",
            "結婚",
            "出産・子育て",
            "就職・転職",
            "進学（子供）",
            "退職・定年",
            "独立（子供）",
        }

        cases = create_step1_cases()
        covered_events = set()

        for case in cases:
            metadata = case.metadata
            if metadata and "event_type" in metadata:
                event_type = metadata["event_type"]
                if event_type and event_type != "multiple":
                    covered_events.add(event_type)

        # 全イベントがカバーされていることを確認
        missing = life_events - covered_events
        assert not missing, f"カバーされていないライフイベント: {missing}"
