"""
app/workflow.pyのテスト。

シングルエージェント方式によるワークフロー実行機能をテストする。
エージェントは3回呼び出され、各ステップでコンテキストを保持しながら処理を行う。
"""

from unittest.mock import patch, MagicMock

import pytest


class TestRunWorkflow:
    """
    run_workflow関数のテスト。

    シングルエージェント方式でワークフローを実行し、
    SessionManagerによる会話履歴の自動保存を検証する。
    """

    def test_run_workflow_with_s3_info(self):
        """
        S3情報を渡してワークフローが実行されることを確認。

        正常なS3情報（bucket、key）を渡すと、ワークフローが
        正常に実行されることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-folder/test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""
            # 各プロンプトに適切なプレースホルダーを設定
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            result = run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            assert result is not None
            assert mock_agent_instance.called

    def test_run_workflow_without_s3_info_raises_error(self):
        """
        S3情報なしでワークフロー実行時にエラーが発生することを確認。

        s3_infoがNoneまたは不正な場合、適切なエラーが発生することを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        # Act & Assert
        with pytest.raises(ValueError, match="s3_info"):
            run_workflow(
                s3_info=None,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

    def test_run_workflow_with_empty_bucket_raises_error(self):
        """
        bucketが空の場合にエラーが発生することを確認。

        S3バケット名が空または不正な場合、適切なエラーが発生することを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        # Act & Assert
        with pytest.raises(ValueError, match="bucket"):
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

    def test_run_workflow_with_empty_key_raises_error(self):
        """
        keyが空の場合にエラーが発生することを確認。

        S3オブジェクトキーが空または不正な場合、適切なエラーが発生することを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": ""}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        # Act & Assert
        with pytest.raises(ValueError, match="key"):
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )


class TestSingleAgentWorkflow:
    """
    シングルエージェント方式のワークフローテスト。

    エージェントが3回呼び出され、各ステップでコンテキストを
    保持しながら処理を行うことを検証する。
    """

    def test_run_workflow_calls_agent_three_times(self):
        """
        ワークフローがエージェントを3回呼び出すことを確認。

        Step 1: ライフイベント検出
        Step 2: パターン分析
        Step 3: レコメンド生成
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            # エージェントが3回呼び出されたことを確認
            assert mock_agent_instance.call_count == 3

    def test_run_workflow_loads_prompts_from_files(self):
        """
        各ステップのプロンプトがmdファイルから読み込まれることを確認。

        workflow/system.md, step1.md, step2.md, step3.mdが読み込まれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            # load_promptが呼び出されたファイル名を確認
            call_args_list = [call[0][0] for call in mock_load_prompt.call_args_list]
            assert "workflow/system" in call_args_list
            assert "workflow/step1" in call_args_list
            assert "workflow/step2" in call_args_list
            assert "workflow/step3" in call_args_list

    def test_run_workflow_uses_session_manager(self):
        """
        ワークフローがSessionManagerをAgentに渡すことを確認。

        SessionManagerにより会話履歴が自動永続化され、
        Memory Strategyによる自動処理が有効になることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_session_manager = MagicMock()
            mock_create_memory.return_value = mock_session_manager
            mock_get_prefs.return_value = ""
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            # create_memoryが正しいパラメータで呼ばれたことを確認
            mock_create_memory.assert_called_once_with(memory_id, session_id, actor_id)
            # Agentにsession_managerが渡されたことを確認
            call_kwargs = mock_agent_class.call_args.kwargs
            assert "session_manager" in call_kwargs
            assert call_kwargs["session_manager"] == mock_session_manager

    def test_run_workflow_passes_s3_info_to_first_step(self):
        """
        通話ログが最初のステップに渡されることを確認。

        Step 1のプロンプトに通話ログ内容が含まれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "my-test-bucket", "key": "data/call-log.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"
        mock_call_log = "顧客: 来月引っ越すことになりました"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""
            mock_read_s3.return_value = mock_call_log
            # 各プロンプトに適切なプレースホルダーを設定
            mock_load_prompt.side_effect = [
                "System prompt",
                "Detect events: {call_log} customer={customer_id} date={call_date}",  # step1
                "Analyze patterns: {step1_result} history={past_summaries}",  # step2
                "Generate recommendations: {step2_result} customer={customer_id} date={call_date}",  # step3
            ]

            # Act
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            # 最初のエージェント呼び出しに通話ログが含まれることを確認
            first_call_args = mock_agent_instance.call_args_list[0][0][0]
            assert mock_call_log in first_call_args
            assert actor_id in first_call_args

    def test_run_workflow_returns_final_result(self):
        """
        ワークフローが最終ステップの結果を返すことを確認。

        Step 3（レコメンド生成）の結果が返されることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            # 各ステップの返り値を設定
            mock_agent_instance.side_effect = [
                "Step 1: Life event detected",
                "Step 2: Patterns analyzed",
                "Step 3: Recommendations generated",
            ]
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            result = run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            # 最終ステップの結果が返されることを確認
            assert "Step 3" in result or "recommendation" in result.lower()

    def test_run_workflow_retrieves_past_preferences(self):
        """
        ワークフロー実行時に過去の検出履歴が取得されることを確認。

        get_past_preferences関数が呼ばれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = "過去に結婚イベントを検出"
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            mock_get_prefs.assert_called_once_with(
                memory_id=memory_id, actor_id=actor_id
            )

    def test_run_workflow_uses_correct_tools(self):
        """
        ワークフローが正しいツールを使用することを確認。

        use_aws、retrieve_memory_toolが含まれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
            patch("app.workflow.load_prompt") as mock_load_prompt,
            patch("app.workflow._read_s3_file") as mock_read_s3,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Step completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""
            mock_load_prompt.side_effect = [
                "System prompt",
                "Step1: {call_log} {customer_id} {call_date}",
                "Step2: {step1_result} {past_summaries}",
                "Step3: {step2_result} {customer_id} {call_date}",
            ]
            mock_read_s3.return_value = "テスト通話ログ"

            # Act
            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Assert
            call_kwargs = mock_agent_class.call_args.kwargs
            assert "tools" in call_kwargs
            tools = call_kwargs["tools"]
            tool_names = [getattr(t, "__name__", str(t)) for t in tools]
            assert any("use_aws" in name for name in tool_names)
            assert any("retrieve_memory_tool" in name for name in tool_names)
