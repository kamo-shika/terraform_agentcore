"""
app/tools.py のテスト。

Strands Agentsで使用可能なカスタムツールをテストする。
"""

from unittest.mock import MagicMock, patch


class TestRetrieveMemoryTool:
    """
    retrieve_memory_tool関数のテスト。

    このツールは、AgentCore Memoryから過去の要約をセマンティック検索で取得する。
    """

    def test_retrieve_with_valid_parameters(self):
        """
        正常なパラメータで過去の要約を取得できることを確認する。

        memory_id、actor_id、queryを渡して、メモリレコードのリストが
        返されることを検証する。
        """
        from app.tools import retrieve_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {
            "memoryRecordSummaries": [
                {
                    "memoryRecordId": "record-001",
                    "content": {"text": "ファイル1の要約"},
                    "relevanceScore": 0.85,
                },
                {
                    "memoryRecordId": "record-002",
                    "content": {"text": "ファイル2の要約"},
                    "relevanceScore": 0.75,
                },
            ]
        }
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
            patch("app.tools.LTM_NAMESPACE", "/file-summaries/{actorId}"),
            patch("app.tools.LTM_SUMMARY_TOP_K", 10),
        ):
            # Act
            result = retrieve_memory_tool(memory_id="test-memory-id", actor_id="test-actor", query="テストクエリ")

            # Assert
            assert len(result) == 2
            assert result[0]["memoryRecordId"] == "record-001"
            assert result[0]["content"] == "ファイル1の要約"
            assert result[0]["relevanceScore"] == 0.85
            assert result[1]["memoryRecordId"] == "record-002"
            assert result[1]["content"] == "ファイル2の要約"
            assert result[1]["relevanceScore"] == 0.75

    def test_retrieve_with_custom_top_k(self):
        """
        top_kパラメータで取得件数を制限できることを確認する。

        デフォルトの取得件数ではなく、カスタムのtop_k値が
        API呼び出しに使用されることを検証する。
        """
        from app.tools import retrieve_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {
            "memoryRecordSummaries": [
                {
                    "memoryRecordId": "record-001",
                    "content": {"text": "要約1"},
                    "relevanceScore": 0.9,
                }
            ]
        }
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
            patch("app.tools.LTM_NAMESPACE", "/file-summaries/{actorId}"),
        ):
            # Act
            result = retrieve_memory_tool(memory_id="test-memory-id", actor_id="test-actor", query="クエリ", top_k=3)

            # Assert
            assert len(result) == 1
            # API呼び出し時にtop_k=3が使用されたことを確認
            call_args = mock_client.retrieve_memory_records.call_args
            assert call_args.kwargs["searchCriteria"]["topK"] == 3

    def test_retrieve_with_empty_memory_id_returns_empty_list(self):
        """
        memory_idが空の場合は空リストを返すことを確認する。

        エラーハンドリングの一環として、不正なパラメータに対して
        適切に空リストを返すことを検証する。
        """
        from app.tools import retrieve_memory_tool

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = retrieve_memory_tool(memory_id="", actor_id="test-actor", query="クエリ")

            # Assert
            assert result == []

    def test_retrieve_when_ltm_disabled_returns_empty_list(self):
        """
        LTM_ENABLEDがFalseの場合は空リストを返すことを確認する。

        LTM機能が無効化されている場合、メモリ検索を実行せず
        空リストを返すことを検証する。
        """
        from app.tools import retrieve_memory_tool

        # Arrange
        with patch("app.tools.LTM_ENABLED", False):
            # Act
            result = retrieve_memory_tool(memory_id="test-memory-id", actor_id="test-actor", query="クエリ")

            # Assert
            assert result == []

    def test_retrieve_with_no_results(self):
        """
        検索結果が0件の場合に空リストを返すことを確認する。

        クエリに一致するレコードがない場合の動作を検証する。
        """
        from app.tools import retrieve_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {"memoryRecordSummaries": []}
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
            patch("app.tools.LTM_NAMESPACE", "/file-summaries/{actorId}"),
        ):
            # Act
            result = retrieve_memory_tool(memory_id="test-memory-id", actor_id="test-actor", query="存在しないクエリ")

            # Assert
            assert result == []

    def test_retrieve_resolves_actor_id_in_namespace(self):
        """
        Namespace内の{actorId}がactor_idに置換されることを確認する。

        Namespaceテンプレートが正しく解決されてAPI呼び出しに
        使用されることを検証する。
        """
        from app.tools import retrieve_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {"memoryRecordSummaries": []}
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
            patch("app.tools.LTM_NAMESPACE", "/file-summaries/{actorId}"),
        ):
            # Act
            retrieve_memory_tool(memory_id="test-memory-id", actor_id="user-123", query="クエリ")

            # Assert
            call_args = mock_client.retrieve_memory_records.call_args
            assert call_args.kwargs["namespace"] == "/file-summaries/user-123"


class TestSaveMemoryTool:
    """
    save_memory_tool関数のテスト。

    このツールは、AgentCore Memoryにコンテンツを保存する。
    """

    def test_save_with_valid_parameters(self):
        """
        正常なパラメータでメモリに保存できることを確認する。

        namespace、memory_id、actor_id、contentを渡して、
        保存成功時にレコードIDが返されることを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {"successfulRecords": [{"memoryRecordId": "saved-record-001"}], "failedRecords": []}
        mock_client.batch_create_memory_records.return_value = mock_response

        with patch("app.tools._get_agentcore_client", return_value=mock_client), patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_memory_tool(
                namespace="/test-namespace",
                memory_id="test-memory-id",
                actor_id="test-actor",
                content="保存するコンテンツ",
            )

            # Assert
            assert result == "saved-record-001"

    def test_save_creates_record_with_correct_structure(self):
        """
        保存時に正しい構造のレコードが作成されることを確認する。

        API呼び出し時に、namespace、content、metadataが
        適切に設定されることを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {"successfulRecords": [{"memoryRecordId": "record-001"}], "failedRecords": []}
        mock_client.batch_create_memory_records.return_value = mock_response

        with patch("app.tools._get_agentcore_client", return_value=mock_client), patch("app.tools.LTM_ENABLED", True):
            # Act
            save_memory_tool(
                namespace="/custom-namespace/{actorId}",
                memory_id="test-memory-id",
                actor_id="user-456",
                content="テストコンテンツ",
            )

            # Assert
            call_args = mock_client.batch_create_memory_records.call_args
            records = call_args.kwargs["memoryRecords"]
            assert len(records) == 1
            record = records[0]

            # Namespace内の{actorId}が解決されている
            assert record["namespace"] == "/custom-namespace/user-456"

            # コンテンツが設定されている
            assert record["content"]["text"] == "テストコンテンツ"

            # メタデータにactorIdが含まれている
            assert record["metadata"]["actorId"] == "user-456"
            assert record["metadata"]["type"] == "memory"

    def test_save_with_empty_content_returns_none(self):
        """
        contentが空の場合はNoneを返すことを確認する。

        エラーハンドリングの一環として、空のコンテンツに対して
        保存を実行せずNoneを返すことを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_memory_tool(
                namespace="/test-namespace", memory_id="test-memory-id", actor_id="test-actor", content=""
            )

            # Assert
            assert result is None

    def test_save_when_ltm_disabled_returns_none(self):
        """
        LTM_ENABLEDがFalseの場合はNoneを返すことを確認する。

        LTM機能が無効化されている場合、メモリ保存を実行せず
        Noneを返すことを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        with patch("app.tools.LTM_ENABLED", False):
            # Act
            result = save_memory_tool(
                namespace="/test-namespace", memory_id="test-memory-id", actor_id="test-actor", content="コンテンツ"
            )

            # Assert
            assert result is None

    def test_save_with_whitespace_only_content_returns_none(self):
        """
        contentが空白のみの場合はNoneを返すことを確認する。

        空白文字のみのコンテンツは無効とみなされ、
        Noneを返すことを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_memory_tool(
                namespace="/test-namespace", memory_id="test-memory-id", actor_id="test-actor", content="   \n\t  "
            )

            # Assert
            assert result is None

    def test_save_handles_failed_records(self):
        """
        保存失敗時にNoneを返すことを確認する。

        AWS APIがfailedRecordsを返した場合、
        適切にエラーハンドリングされることを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {
            "successfulRecords": [],
            "failedRecords": [{"memoryRecordId": "failed-record-001", "failureReason": "Validation error"}],
        }
        mock_client.batch_create_memory_records.return_value = mock_response

        with patch("app.tools._get_agentcore_client", return_value=mock_client), patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_memory_tool(
                namespace="/test-namespace", memory_id="test-memory-id", actor_id="test-actor", content="コンテンツ"
            )

            # Assert
            assert result is None

    def test_save_generates_unique_record_id(self):
        """
        保存時にユニークなレコードIDが生成されることを確認する。

        各保存操作で異なるmemoryRecordIdが生成されることを検証する。
        """
        from app.tools import save_memory_tool

        # Arrange
        mock_client = MagicMock()
        mock_response = {"successfulRecords": [{"memoryRecordId": "record-001"}], "failedRecords": []}
        mock_client.batch_create_memory_records.return_value = mock_response

        with patch("app.tools._get_agentcore_client", return_value=mock_client), patch("app.tools.LTM_ENABLED", True):
            # Act - 複数回保存
            save_memory_tool(
                namespace="/test-namespace", memory_id="test-memory-id", actor_id="test-actor", content="コンテンツ1"
            )

            save_memory_tool(
                namespace="/test-namespace", memory_id="test-memory-id", actor_id="test-actor", content="コンテンツ2"
            )

            # Assert - 2回の呼び出しで異なるレコードIDが使用されている
            calls = mock_client.batch_create_memory_records.call_args_list
            assert len(calls) == 2

            record_id_1 = calls[0].kwargs["memoryRecords"][0]["memoryRecordId"]
            record_id_2 = calls[1].kwargs["memoryRecords"][0]["memoryRecordId"]

            assert record_id_1 != record_id_2
