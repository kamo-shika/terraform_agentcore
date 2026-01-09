"""
app/workflow.pyのテスト。

ワークフロータスク定義と実行機能をテストする。
このファイルはTDD Redフェーズで作成され、実装前に失敗することを確認する。
"""

from unittest.mock import patch

import pytest


class TestCreateS3SummarizeWorkflow:
    """
    create_s3_summarize_workflow関数のテスト。

    S3ファイル要約→パターン分析→プロファイル生成の3タスクワークフローを
    作成する関数の動作を検証する。
    """

    def test_workflow_has_three_tasks(self):
        """
        ワークフローが3つのタスクを持つことを確認。

        summarize_s3_file、analyze_patterns、generate_profileの
        3つのタスクが定義されることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()

        # Assert
        assert len(workflow["tasks"]) == 3

    def test_workflow_has_correct_task_ids(self):
        """
        ワークフローが正しいタスクIDを持つことを確認。

        各タスクのtask_idがsummarize_s3_file、analyze_patterns、
        generate_profileであることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        task_ids = [task["task_id"] for task in workflow["tasks"]]

        # Assert
        assert "summarize_s3_file" in task_ids
        assert "analyze_patterns" in task_ids
        assert "generate_profile" in task_ids

    def test_task_summarize_s3_file_has_no_dependencies(self):
        """
        summarize_s3_fileタスクが依存関係を持たないことを確認。

        最初のタスクであるsummarize_s3_fileは、他のタスクに依存せず
        独立して実行可能であることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        summarize_task = next(task for task in workflow["tasks"] if task["task_id"] == "summarize_s3_file")

        # Assert
        assert summarize_task["dependencies"] == []

    def test_task_analyze_patterns_depends_on_summarize(self):
        """
        analyze_patternsタスクがsummarize_s3_fileに依存することを確認。

        analyze_patternsタスクは、summarize_s3_fileの完了後に実行される
        ことを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        analyze_task = next(task for task in workflow["tasks"] if task["task_id"] == "analyze_patterns")

        # Assert
        assert "summarize_s3_file" in analyze_task["dependencies"]

    def test_task_generate_profile_depends_on_analyze(self):
        """
        generate_profileタスクがanalyze_patternsに依存することを確認。

        generate_profileタスクは、analyze_patternsの完了後に実行される
        ことを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        profile_task = next(task for task in workflow["tasks"] if task["task_id"] == "generate_profile")

        # Assert
        assert "analyze_patterns" in profile_task["dependencies"]

    def test_task_summarize_s3_file_has_correct_tools(self):
        """
        summarize_s3_fileタスクが正しいツールを持つことを確認。

        SessionManager統合後、summarize_s3_fileタスクはuse_awsのみを使用する。
        保存はSessionManagerによって自動的に行われる。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        summarize_task = next(task for task in workflow["tasks"] if task["task_id"] == "summarize_s3_file")

        # Assert
        assert "use_aws" in summarize_task["tools"]
        # SessionManager統合後、save_memory_toolは不要
        assert "save_memory_tool" not in summarize_task["tools"]

    def test_task_analyze_patterns_has_retrieve_memory_tool(self):
        """
        analyze_patternsタスクがretrieve_memory_toolを持つことを確認。

        analyze_patternsタスクは、過去の要約を取得するために
        retrieve_memory_toolを使用することを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        analyze_task = next(task for task in workflow["tasks"] if task["task_id"] == "analyze_patterns")

        # Assert
        assert "retrieve_memory_tool" in analyze_task["tools"]

    def test_task_generate_profile_does_not_have_save_memory_tool(self):
        """
        generate_profileタスクがsave_memory_toolを持たないことを確認。

        SessionManager統合後、保存はSessionManagerによって自動的に行われるため、
        save_memory_toolは不要であることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        profile_task = next(task for task in workflow["tasks"] if task["task_id"] == "generate_profile")

        # Assert
        # SessionManager統合後、save_memory_toolは不要
        assert "save_memory_tool" not in profile_task["tools"]

    def test_all_tasks_have_descriptions(self):
        """
        すべてのタスクが説明（description）を持つことを確認。

        各タスクには、AIが実行すべき内容を示すdescriptionフィールドが
        必要であることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()

        # Assert
        for task in workflow["tasks"]:
            assert "description" in task
            assert isinstance(task["description"], str)
            assert len(task["description"]) > 0

    def test_all_tasks_have_system_prompts(self):
        """
        すべてのタスクがシステムプロンプト（system_prompt）を持つことを確認。

        各タスクには、そのタスク専用のシステムプロンプトが設定されている
        ことを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()

        # Assert
        for task in workflow["tasks"]:
            assert "system_prompt" in task
            assert isinstance(task["system_prompt"], str)
            assert len(task["system_prompt"]) > 0

    def test_workflow_has_workflow_id(self):
        """
        ワークフローがworkflow_idを持つことを確認。

        ワークフローを識別するためのworkflow_idが設定されることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()

        # Assert
        assert "workflow_id" in workflow
        assert isinstance(workflow["workflow_id"], str)
        assert len(workflow["workflow_id"]) > 0

    def test_workflow_id_is_s3_summarize(self):
        """
        ワークフローIDが"s3_summarize"であることを確認。

        ワークフローの目的を示す適切なIDが設定されることを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()

        # Assert
        assert workflow["workflow_id"] == "s3_summarize"

    def test_task_summarize_s3_file_description_mentions_s3(self):
        """
        summarize_s3_fileタスクの説明にS3関連の内容が含まれることを確認。

        タスクの説明が、S3ファイル読み取りに関する指示を含むことを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        summarize_task = next(task for task in workflow["tasks"] if task["task_id"] == "summarize_s3_file")

        # Assert
        description = summarize_task["description"].lower()
        # S3関連のキーワードが含まれることを確認
        assert "s3" in description or "ファイル" in description or "file" in description


class TestRunWorkflow:
    """
    run_workflow関数のテスト。

    ワークフローを実行し、結果を返す関数の動作を検証する。
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

        # Mock the Agent and create_memory
        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success", "result": "Workflow completed successfully"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            # Act
            result = run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            # Workflow Tool APIが呼ばれたことを確認
            assert mock_workflow_tool.called
            assert "success" in result.lower() or "workflow" in result.lower()

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
            run_workflow(s3_info=None, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

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
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

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
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

    def test_run_workflow_returns_profile(self):
        """
        ワークフロー完了後にプロファイルが返却されることを確認。

        ワークフローが正常に完了すると、ユーザープロファイルを含む
        結果が返されることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        # Mock Agent and create_memory
        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {
                "status": "success",
                "result": "User profile: Technical user with data analysis focus"
            }
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            # Act
            result = run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            assert result is not None
            assert "profile" in result.lower() or "user" in result.lower()

    def test_run_workflow_creates_workflow_with_correct_parameters(self):
        """
        ワークフロー作成時に正しいパラメータが渡されることを確認。

        S3情報、memory_id、actor_idがワークフローのタスクdescriptionに
        適切に埋め込まれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "data/file.txt"}
        memory_id = "memory-123"
        actor_id = "user-456"
        session_id = "session-789"

        # Mock Agent, create_memory and get_past_preferences
        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            # Act
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            # Agentが正しいツールで作成されたことを確認
            call_kwargs = mock_agent_class.call_args.kwargs
            assert "tools" in call_kwargs

            # workflow(action="create")が呼ばれ、タスクにパラメータが含まれることを確認
            create_calls = [
                call for call in mock_workflow_tool.call_args_list
                if call.kwargs.get("action") == "create"
            ]
            assert len(create_calls) == 1
            tasks = create_calls[0].kwargs["tasks"]

            # 各タスクのdescriptionにパラメータが含まれることを確認
            all_descriptions = " ".join(task["description"] for task in tasks)
            assert "test-bucket" in all_descriptions
            assert "data/file.txt" in all_descriptions
            assert memory_id in all_descriptions
            assert actor_id in all_descriptions

    def test_run_workflow_uses_agent_with_correct_tools(self):
        """
        ワークフローがAgentを正しいツールで作成することを確認。

        SessionManager統合後は、save_memory_tool、save_to_memory_via_eventは不要。
        use_aws、retrieve_memory_tool、get_past_preferencesのみを使用する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        # Mock Agent, create_memory, and get_past_preferences
        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Workflow completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            # Act
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            # Agentが作成されたことを確認
            assert mock_agent_class.called
            # toolsが渡されたことを確認
            call_kwargs = mock_agent_class.call_args.kwargs
            assert "tools" in call_kwargs
            tools = call_kwargs["tools"]
            # マルチエージェント対応後は4つのツール
            # （use_aws, retrieve_memory_tool, get_past_preferences, workflow）
            assert len(tools) == 4

    def test_run_workflow_retrieves_past_preferences(self):
        """
        ワークフロー実行時に過去の嗜好が取得されることを確認。

        get_past_preferences関数が呼ばれ、過去の嗜好データが
        エージェントのプロンプトに含まれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        # Mock Agent, create_memory and get_past_preferences
        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = "ユーザーはPythonを好む傾向がある"

            # Act
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            # get_past_preferencesが呼ばれたことを確認
            mock_get_prefs.assert_called_once_with(
                memory_id=memory_id, actor_id=actor_id
            )
            # ワークフローのタスクdescriptionに過去の嗜好が含まれることを確認
            create_calls = [
                call for call in mock_workflow_tool.call_args_list
                if call.kwargs.get("action") == "create"
            ]
            assert len(create_calls) == 1
            tasks = create_calls[0].kwargs["tasks"]
            all_descriptions = " ".join(task["description"] for task in tasks)
            assert "Python" in all_descriptions or "嗜好" in all_descriptions

    def test_run_workflow_includes_past_preferences_in_prompt(self):
        """
        過去の嗜好がワークフローのタスクdescriptionに含まれることを確認。

        取得した嗜好データがタスクdescriptionに埋め込まれ、
        サブエージェントが嗜好を考慮した分析を行えることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "data.txt"}
        memory_id = "memory-123"
        actor_id = "user-456"
        session_id = "session-789"
        past_prefs = "効率重視のコーディングスタイルを好む\nドキュメントを丁寧に書く傾向"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = past_prefs

            # Act
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            # ワークフローのタスクdescriptionに嗜好データが含まれることを確認
            create_calls = [
                call for call in mock_workflow_tool.call_args_list
                if call.kwargs.get("action") == "create"
            ]
            assert len(create_calls) == 1
            tasks = create_calls[0].kwargs["tasks"]
            all_descriptions = " ".join(task["description"] for task in tasks)
            assert "効率重視" in all_descriptions or "コーディング" in all_descriptions

    def test_run_workflow_handles_empty_preferences(self):
        """
        過去の嗜好がない場合でもワークフローが正常に動作することを確認。

        初回実行時など嗜好データがない場合でも、
        エラーなくワークフローが完了することを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "new-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "First analysis complete"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""  # 嗜好データなし

            # Act
            result = run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            assert result is not None
            mock_get_prefs.assert_called_once()

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
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Workflow completed"
            mock_session_manager = "mock-session-manager"
            mock_create_memory.return_value = mock_session_manager
            mock_get_prefs.return_value = ""

            # Act
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            # create_memoryが正しいパラメータで呼ばれたことを確認
            mock_create_memory.assert_called_once_with(memory_id, session_id, actor_id)
            # Agentにsession_managerが渡されたことを確認
            call_kwargs = mock_agent_class.call_args.kwargs
            assert "session_manager" in call_kwargs
            assert call_kwargs["session_manager"] == mock_session_manager

    def test_run_workflow_does_not_use_save_tools(self):
        """
        ワークフローが保存系ツールを使用しないことを確認。

        SessionManager統合後は、save_memory_tool、save_to_memory_via_eventは
        不要であり、Agentのツールリストに含まれないことを検証する。
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
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Workflow completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            # Act
            run_workflow(s3_info=s3_info, actor_id=actor_id, session_id=session_id, memory_id=memory_id)

            # Assert
            call_kwargs = mock_agent_class.call_args.kwargs
            tools = call_kwargs.get("tools", [])
            # 保存系ツールが含まれないことを確認
            tool_names = [getattr(t, "__name__", str(t)) for t in tools]
            assert not any("save_memory_tool" in name for name in tool_names)
            assert not any("save_to_memory_via_event" in name for name in tool_names)


class TestMultiAgentWorkflow:
    """
    マルチエージェントワークフローのテスト。

    Workflow Tool APIを使用したマルチエージェント対応の
    ワークフロー実装をテストする。
    """

    def test_run_workflow_uses_workflow_tool(self):
        """
        run_workflowがWorkflow Toolを使用することを確認。
        """
        from app.workflow import run_workflow

        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_agent_instance.return_value = "Workflow completed"
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # Agentがworkflowツールを持っていることを確認
            call_kwargs = mock_agent_class.call_args.kwargs
            tools = call_kwargs.get("tools", [])
            tool_names = [getattr(t, "__name__", str(t)) for t in tools]
            assert any("workflow" in name.lower() for name in tool_names)

    def test_run_workflow_calls_workflow_create(self):
        """
        run_workflowがworkflow(action="create")を呼び出すことを確認。

        ワークフロー定義（タスク、システムプロンプト、依存関係）が
        Workflow Tool APIに正しく渡されることを検証する。
        """
        from app.workflow import run_workflow

        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # workflow(action="create")が呼ばれたことを確認
            create_calls = [
                call for call in mock_workflow_tool.call_args_list
                if call.kwargs.get("action") == "create"
            ]
            assert len(create_calls) == 1

            # タスクが渡されていることを確認
            create_call = create_calls[0]
            assert "tasks" in create_call.kwargs
            tasks = create_call.kwargs["tasks"]
            assert len(tasks) == 3

            # 各タスクにsystem_promptが含まれていることを確認
            for task in tasks:
                assert "system_prompt" in task
                assert len(task["system_prompt"]) > 0

    def test_run_workflow_calls_workflow_start(self):
        """
        run_workflowがworkflow(action="start")を呼び出すことを確認。

        ワークフロー作成後に開始されることを検証する。
        """
        from app.workflow import run_workflow

        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # workflow(action="start")が呼ばれたことを確認
            start_calls = [
                call for call in mock_workflow_tool.call_args_list
                if call.kwargs.get("action") == "start"
            ]
            assert len(start_calls) == 1

    def test_run_workflow_passes_s3_info_in_task_description(self):
        """
        run_workflowがS3情報をタスクのdescriptionに含めることを確認。

        最初のタスク（summarize_s3_file）のdescriptionにS3バケットと
        キー情報が含まれることを検証する。
        """
        from app.workflow import run_workflow

        s3_info = {"bucket": "my-test-bucket", "key": "data/report.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"
        session_id = "test-session"

        with (
            patch("app.workflow.Agent") as mock_agent_class,
            patch("app.workflow.create_memory") as mock_create_memory,
            patch("app.workflow.get_past_preferences") as mock_get_prefs,
        ):
            mock_agent_instance = mock_agent_class.return_value
            mock_workflow_tool = mock_agent_instance.tool.workflow
            mock_workflow_tool.return_value = {"status": "success"}
            mock_create_memory.return_value = "mock-session-manager"
            mock_get_prefs.return_value = ""

            run_workflow(
                s3_info=s3_info,
                actor_id=actor_id,
                session_id=session_id,
                memory_id=memory_id,
            )

            # workflow(action="create")の呼び出しを取得
            create_calls = [
                call for call in mock_workflow_tool.call_args_list
                if call.kwargs.get("action") == "create"
            ]
            assert len(create_calls) == 1

            # 最初のタスクのdescriptionにS3情報が含まれることを確認
            tasks = create_calls[0].kwargs["tasks"]
            summarize_task = next(t for t in tasks if t["task_id"] == "summarize_s3_file")
            assert "my-test-bucket" in summarize_task["description"]
            assert "data/report.txt" in summarize_task["description"]
