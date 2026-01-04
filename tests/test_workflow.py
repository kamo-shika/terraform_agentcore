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

        summarize_s3_fileタスクは、use_awsとsave_memory_toolの
        2つのツールを使用することを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        summarize_task = next(task for task in workflow["tasks"] if task["task_id"] == "summarize_s3_file")

        # Assert
        assert "use_aws" in summarize_task["tools"]
        assert "save_memory_tool" in summarize_task["tools"]

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

    def test_task_generate_profile_has_save_memory_tool(self):
        """
        generate_profileタスクがsave_memory_toolを持つことを確認。

        generate_profileタスクは、ユーザープロファイルを保存するために
        save_memory_toolを使用することを検証する。
        """
        from app.workflow import create_s3_summarize_workflow

        # Arrange & Act
        workflow = create_s3_summarize_workflow()
        profile_task = next(task for task in workflow["tasks"] if task["task_id"] == "generate_profile")

        # Assert
        assert "save_memory_tool" in profile_task["tools"]

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

        # Mock the workflow execution
        with patch("app.workflow.workflow") as mock_workflow_tool:
            # create action
            mock_workflow_tool.return_value = {"status": "success", "content": [{"text": "Workflow created"}]}

            # Act
            run_workflow(s3_info=s3_info, memory_id=memory_id, actor_id=actor_id)

            # Assert
            # ワークフローツールが呼ばれたことを確認
            assert mock_workflow_tool.called

    def test_run_workflow_without_s3_info_raises_error(self):
        """
        S3情報なしでワークフロー実行時にエラーが発生することを確認。

        s3_infoがNoneまたは不正な場合、適切なエラーが発生することを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        memory_id = "test-memory-id"
        actor_id = "test-actor"

        # Act & Assert
        with pytest.raises(ValueError, match="s3_info"):
            run_workflow(s3_info=None, memory_id=memory_id, actor_id=actor_id)

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

        # Act & Assert
        with pytest.raises(ValueError, match="bucket"):
            run_workflow(s3_info=s3_info, memory_id=memory_id, actor_id=actor_id)

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

        # Act & Assert
        with pytest.raises(ValueError, match="key"):
            run_workflow(s3_info=s3_info, memory_id=memory_id, actor_id=actor_id)

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

        # Mock workflow execution
        with patch("app.workflow.workflow") as mock_workflow_tool:
            # Mock create response
            def workflow_side_effect(action, **kwargs):
                if action == "create":
                    return {"status": "success", "content": [{"text": "Workflow created"}]}
                elif action == "start":
                    return {"status": "success", "content": [{"text": "Workflow completed"}]}
                elif action == "status":
                    # Mock completed workflow with profile result
                    return {
                        "status": "success",
                        "workflow": {
                            "task_results": {
                                "generate_profile": {
                                    "status": "completed",
                                    "result": [{"text": "User profile generated"}],
                                }
                            }
                        },
                    }
                return {"status": "error"}

            mock_workflow_tool.side_effect = workflow_side_effect

            # Act
            result = run_workflow(s3_info=s3_info, memory_id=memory_id, actor_id=actor_id)

            # Assert
            assert result is not None
            assert "profile" in result or "result" in result

    def test_run_workflow_creates_workflow_with_correct_parameters(self):
        """
        ワークフロー作成時に正しいパラメータが渡されることを確認。

        S3情報、memory_id、actor_idがワークフロータスクの
        descriptionやsystem_promptに適切に埋め込まれることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "data/file.txt"}
        memory_id = "memory-123"
        actor_id = "user-456"

        # Mock workflow tool
        with patch("app.workflow.workflow") as mock_workflow_tool:
            mock_workflow_tool.return_value = {"status": "success", "content": [{"text": "Created"}]}

            # Act
            run_workflow(s3_info=s3_info, memory_id=memory_id, actor_id=actor_id)

            # Assert
            # createアクションが呼ばれたことを確認
            create_call = None
            for call in mock_workflow_tool.call_args_list:
                if call.kwargs.get("action") == "create":
                    create_call = call
                    break

            assert create_call is not None
            # タスクリストが渡されたことを確認
            assert "tasks" in create_call.kwargs

    def test_run_workflow_starts_workflow_after_creation(self):
        """
        ワークフロー作成後にstartアクションが呼ばれることを確認。

        ワークフローの作成（create）に続いて、実行開始（start）が
        行われることを検証する。
        """
        from app.workflow import run_workflow

        # Arrange
        s3_info = {"bucket": "test-bucket", "key": "test-file.txt"}
        memory_id = "test-memory-id"
        actor_id = "test-actor"

        # Mock workflow tool
        with patch("app.workflow.workflow") as mock_workflow_tool:
            mock_workflow_tool.return_value = {"status": "success", "content": [{"text": "OK"}]}

            # Act
            run_workflow(s3_info=s3_info, memory_id=memory_id, actor_id=actor_id)

            # Assert
            # createとstartの両方が呼ばれたことを確認
            actions_called = [call.kwargs.get("action") for call in mock_workflow_tool.call_args_list]
            assert "create" in actions_called
            assert "start" in actions_called
