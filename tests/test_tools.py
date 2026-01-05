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
            records = call_args.kwargs["records"]
            assert len(records) == 1
            record = records[0]

            # Namespace内の{actorId}が解決されている（配列として渡される）
            assert record["namespaces"] == ["/custom-namespace/user-456"]

            # コンテンツが設定されている
            assert record["content"]["text"] == "テストコンテンツ"

            # requestIdentifierが設定されている
            assert "requestIdentifier" in record
            assert record["requestIdentifier"].startswith("memory-")

            # timestampが設定されている
            assert "timestamp" in record
            assert isinstance(record["timestamp"], int)

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

    def test_save_generates_unique_request_identifier(self):
        """
        保存時にユニークなリクエストIDが生成されることを確認する。

        各保存操作で異なるrequestIdentifierが生成されることを検証する。
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

            # Assert - 2回の呼び出しで異なるrequestIdentifierが使用されている
            calls = mock_client.batch_create_memory_records.call_args_list
            assert len(calls) == 2

            request_id_1 = calls[0].kwargs["records"][0]["requestIdentifier"]
            request_id_2 = calls[1].kwargs["records"][0]["requestIdentifier"]

            assert request_id_1 != request_id_2


class TestSaveToMemoryViaEvent:
    """
    save_to_memory_via_event関数のテスト。

    このツールは、create_event APIを使用してメモリに会話形式で保存し、
    Memory Strategyによる自動処理（Extraction/Consolidation）を有効にする。
    """

    def test_save_via_event_with_valid_parameters(self):
        """
        正常なパラメータでcreate_eventが呼び出されることを確認する。

        memory_id、session_id、actor_id、user_content、assistant_contentを渡して、
        create_event APIが正しく呼び出されることを検証する。
        """
        from app.tools import save_to_memory_via_event

        # Arrange
        mock_client = MagicMock()
        mock_response = {"eventId": "event-001"}
        mock_client.create_event.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            result = save_to_memory_via_event(
                memory_id="test-memory-id",
                session_id="test-session-id",
                actor_id="test-actor",
                user_content="ユーザーからのファイル内容",
                assistant_content="AIによる分析結果",
            )

            # Assert
            assert result == {"eventId": "event-001"}
            mock_client.create_event.assert_called_once()

    def test_save_via_event_creates_correct_message_structure(self):
        """
        create_event呼び出し時に正しいメッセージ構造が使用されることを確認する。

        USER役割とASSISTANT役割の2つのメッセージが正しい順序と形式で
        渡されることを検証する。
        """
        from app.tools import save_to_memory_via_event

        # Arrange
        mock_client = MagicMock()
        mock_response = {"eventId": "event-001"}
        mock_client.create_event.return_value = mock_response

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            save_to_memory_via_event(
                memory_id="test-memory-id",
                session_id="session-123",
                actor_id="actor-456",
                user_content="ファイル内容です",
                assistant_content="分析結果です",
            )

            # Assert
            call_kwargs = mock_client.create_event.call_args.kwargs
            assert call_kwargs["memoryId"] == "test-memory-id"
            assert call_kwargs["sessionId"] == "session-123"
            assert call_kwargs["actorId"] == "actor-456"

            # メッセージ構造の検証
            event = call_kwargs["event"]
            assert "conversationEvent" in event
            messages = event["conversationEvent"]["messages"]
            assert len(messages) == 2
            assert messages[0]["role"] == "USER"
            assert messages[0]["content"]["text"] == "ファイル内容です"
            assert messages[1]["role"] == "ASSISTANT"
            assert messages[1]["content"]["text"] == "分析結果です"

    def test_save_via_event_when_ltm_disabled_returns_none(self):
        """
        LTM_ENABLEDがFalseの場合はNoneを返すことを確認する。

        LTM機能が無効化されている場合、create_eventを実行せず
        Noneを返すことを検証する。
        """
        from app.tools import save_to_memory_via_event

        # Arrange
        with patch("app.tools.LTM_ENABLED", False):
            # Act
            result = save_to_memory_via_event(
                memory_id="test-memory-id",
                session_id="test-session",
                actor_id="test-actor",
                user_content="ユーザーコンテンツ",
                assistant_content="アシスタントコンテンツ",
            )

            # Assert
            assert result is None

    def test_save_via_event_with_empty_memory_id_returns_none(self):
        """
        memory_idが空の場合はNoneを返すことを確認する。
        """
        from app.tools import save_to_memory_via_event

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_to_memory_via_event(
                memory_id="",
                session_id="test-session",
                actor_id="test-actor",
                user_content="ユーザーコンテンツ",
                assistant_content="アシスタントコンテンツ",
            )

            # Assert
            assert result is None

    def test_save_via_event_with_empty_user_content_returns_none(self):
        """
        user_contentが空の場合はNoneを返すことを確認する。
        """
        from app.tools import save_to_memory_via_event

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_to_memory_via_event(
                memory_id="test-memory-id",
                session_id="test-session",
                actor_id="test-actor",
                user_content="",
                assistant_content="アシスタントコンテンツ",
            )

            # Assert
            assert result is None

    def test_save_via_event_with_empty_assistant_content_returns_none(self):
        """
        assistant_contentが空の場合はNoneを返すことを確認する。
        """
        from app.tools import save_to_memory_via_event

        # Arrange
        with patch("app.tools.LTM_ENABLED", True):
            # Act
            result = save_to_memory_via_event(
                memory_id="test-memory-id",
                session_id="test-session",
                actor_id="test-actor",
                user_content="ユーザーコンテンツ",
                assistant_content="",
            )

            # Assert
            assert result is None

    def test_save_via_event_handles_client_error(self):
        """
        AWS APIエラー時にNoneを返すことを確認する。
        """
        from botocore.exceptions import ClientError

        from app.tools import save_to_memory_via_event

        # Arrange
        mock_client = MagicMock()
        mock_client.create_event.side_effect = ClientError(
            {"Error": {"Code": "ValidationException", "Message": "Invalid request"}},
            "CreateEvent",
        )

        with (
            patch("app.tools._get_agentcore_client", return_value=mock_client),
            patch("app.tools.LTM_ENABLED", True),
        ):
            # Act
            result = save_to_memory_via_event(
                memory_id="test-memory-id",
                session_id="test-session",
                actor_id="test-actor",
                user_content="ユーザーコンテンツ",
                assistant_content="アシスタントコンテンツ",
            )

            # Assert
            assert result is None


class TestGetPastPreferences:
    """
    get_past_preferences関数のテスト。

    このツールは、過去の嗜好データを/actor-state/{actorId}から取得し、
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
        /actor-state/{actorId}名前空間を使用することを確認する。
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
            assert call_kwargs["namespace"] == "/actor-state/user-123"

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
