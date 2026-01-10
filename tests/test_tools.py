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
            patch("app.tools.LTM_NAMESPACE", "/call-summaries/{actorId}"),
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
            patch("app.tools.LTM_NAMESPACE", "/call-summaries/{actorId}"),
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
            patch("app.tools.LTM_NAMESPACE", "/call-summaries/{actorId}"),
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
            patch("app.tools.LTM_NAMESPACE", "/call-summaries/{actorId}"),
        ):
            # Act
            retrieve_memory_tool(memory_id="test-memory-id", actor_id="user-123", query="クエリ")

            # Assert
            call_args = mock_client.retrieve_memory_records.call_args
            assert call_args.kwargs["namespace"] == "/call-summaries/user-123"


class TestGetPastPreferences:
    """
    get_past_preferences関数のテスト。

    このツールは、過去の嗜好データを/life-events/{actorId}から取得し、
    エージェントが分析時に参照できるようにする。
    """

    def test_get_past_preferences_with_valid_parameters(self):
        """
        正常なパラメータで過去の嗜好を取得できることを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        mock_client = MagicMock()
        mock_response = {
            "memoryRecordSummaries": [
                {
                    "memoryRecordId": "pref-001",
                    "content": {"text": "ユーザーはPythonを好む傾向がある"},
                    "relevanceScore": 0.9,
                },
                {
                    "memoryRecordId": "pref-002",
                    "content": {"text": "効率を重視する傾向がある"},
                    "relevanceScore": 0.85,
                },
            ]
        }
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            result = get_past_preferences(memory_id="test-memory-id", actor_id="test-actor")

            # Assert
            assert "Pythonを好む" in result
            assert "効率を重視" in result

    def test_get_past_preferences_uses_actor_state_namespace(self):
        """
        /life-events/{actorId}名前空間を使用することを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        mock_client = MagicMock()
        mock_response = {"memoryRecordSummaries": []}
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            get_past_preferences(memory_id="test-memory-id", actor_id="user-123")

            # Assert
            call_kwargs = mock_client.retrieve_memory_records.call_args.kwargs
            assert call_kwargs["namespace"] == "/life-events/user-123"

    def test_get_past_preferences_returns_empty_string_when_no_data(self):
        """
        過去の嗜好がない場合は空文字列を返すことを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        mock_client = MagicMock()
        mock_response = {"memoryRecordSummaries": []}
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            result = get_past_preferences(memory_id="test-memory-id", actor_id="test-actor")

            # Assert
            assert result == ""

    def test_get_past_preferences_when_ltm_disabled_returns_empty_string(self):
        """
        LTM_ENABLEDがFalseの場合は空文字列を返すことを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        with patch("app.tools.LTM_ENABLED", False):
            # Act
            result = get_past_preferences(memory_id="test-memory-id", actor_id="test-actor")

            # Assert
            assert result == ""

    def test_get_past_preferences_with_empty_memory_id_returns_empty_string(self):
        """
        memory_idが空の場合は空文字列を返すことを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = get_past_preferences(memory_id="", actor_id="test-actor")

            # Assert
            assert result == ""

    def test_get_past_preferences_with_empty_actor_id_returns_empty_string(self):
        """
        actor_idが空の場合は空文字列を返すことを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = get_past_preferences(memory_id="test-memory-id", actor_id="")

            # Assert
            assert result == ""

    def test_get_past_preferences_handles_client_error(self):
        """
        AWS APIエラー時に空文字列を返すことを確認する。
        """
        from botocore.exceptions import ClientError

        from app.tools import get_past_preferences

        # Arrange
        mock_client = MagicMock()
        mock_client.retrieve_memory_records.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "Memory not found"}},
            "RetrieveMemoryRecords",
        )

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            result = get_past_preferences(memory_id="test-memory-id", actor_id="test-actor")

            # Assert
            assert result == ""

    def test_get_past_preferences_uses_correct_search_query(self):
        """
        嗜好検索に適切なクエリを使用することを確認する。
        """
        from app.tools import get_past_preferences

        # Arrange
        mock_client = MagicMock()
        mock_response = {"memoryRecordSummaries": []}
        mock_client.retrieve_memory_records.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            get_past_preferences(memory_id="test-memory-id", actor_id="test-actor")

            # Assert
            call_kwargs = mock_client.retrieve_memory_records.call_args.kwargs
            search_criteria = call_kwargs["searchCriteria"]
            # 嗜好に関連するクエリが使用されることを確認
            assert "searchQuery" in search_criteria
            query = search_criteria["searchQuery"]
            assert "嗜好" in query or "傾向" in query or "好み" in query or "preference" in query.lower()
