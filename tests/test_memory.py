"""
app/memory.py のテスト。

AgentCore Memoryの統合設定をテストする。
"""

from unittest.mock import MagicMock, patch


class TestCreateRetrievalConfig:
    """
    create_retrieval_config関数のテスト。
    """

    def test_returns_config_when_ltm_enabled(self):
        """
        LTM有効時にRetrievalConfigが返されることを確認する。

        SessionManager統合後、複数のNamespaceを含むRetrievalConfigが
        返されることを検証する。
        """
        with (
            patch("app.memory.LTM_ENABLED", True),
            patch("app.memory.LTM_SUMMARY_TOP_K", 10),
            patch("app.memory.LTM_SUMMARY_SCORE", 0.3),
            patch("app.memory.LTM_NAMESPACE", "/file-summaries/{actorId}"),
            patch("app.memory.ACTOR_STATE_NAMESPACE", "/actor-state/{actorId}"),
            patch("app.memory.ACTOR_STATE_TOP_K", 5),
        ):
            from app.memory import create_retrieval_config

            result = create_retrieval_config()

            assert result is not None
            # ファイル要約のNamespaceを含む
            assert "/file-summaries/{actorId}" in result
            assert result["/file-summaries/{actorId}"]["top_k"] == 10
            assert result["/file-summaries/{actorId}"]["relevance_score"] == 0.3
            # Actor状態のNamespaceも含む
            assert "/actor-state/{actorId}" in result
            assert result["/actor-state/{actorId}"]["top_k"] == 5

    def test_returns_none_when_ltm_disabled(self):
        """
        LTM無効時にNoneが返されることを確認する。
        """
        with patch("app.memory.LTM_ENABLED", False):
            from app.memory import create_retrieval_config

            result = create_retrieval_config()

            assert result is None

    def test_uses_custom_top_k_value(self):
        """
        カスタムのtop_k値が使用されることを確認する。
        """
        with (
            patch("app.memory.LTM_ENABLED", True),
            patch("app.memory.LTM_SUMMARY_TOP_K", 20),
            patch("app.memory.LTM_SUMMARY_SCORE", 0.5),
            patch("app.memory.LTM_NAMESPACE", "/file-summaries/{actorId}"),
        ):
            from app.memory import create_retrieval_config

            result = create_retrieval_config()

            assert result["/file-summaries/{actorId}"]["top_k"] == 20
            assert result["/file-summaries/{actorId}"]["relevance_score"] == 0.5


class TestCreateMemory:
    """
    create_memory関数のテスト。
    """

    def test_create_memory_returns_session_manager(self):
        """
        create_memoryがセッションマネージャーを返すことを確認する。
        """
        from app.memory import create_memory

        with (
            patch("app.memory.AgentCoreMemorySessionManager") as mock_manager,
            patch("app.memory.AgentCoreMemoryConfig") as mock_config,
            patch("app.memory.create_retrieval_config") as mock_retrieval,
        ):
            mock_manager.return_value = MagicMock()
            mock_retrieval.return_value = None

            result = create_memory(mem_id="test-memory", session_id="test-session", actor_id="test-actor")

            assert result is not None
            mock_config.assert_called_once_with(
                memory_id="test-memory", session_id="test-session", actor_id="test-actor", retrieval_config=None
            )
            mock_manager.assert_called_once()

    def test_create_memory_with_different_parameters(self):
        """
        異なるパラメータでcreate_memoryが動作することを確認する。
        """
        from app.memory import create_memory

        with (
            patch("app.memory.AgentCoreMemorySessionManager") as mock_manager,
            patch("app.memory.AgentCoreMemoryConfig") as mock_config,
            patch("app.memory.create_retrieval_config") as mock_retrieval,
        ):
            mock_manager.return_value = MagicMock()
            mock_retrieval.return_value = None

            # 別のパラメータで呼び出し
            result = create_memory(
                mem_id="custom-memory-id", session_id="custom-session-id", actor_id="custom-actor-id"
            )

            assert result is not None
            config_call_args = mock_config.call_args
            assert config_call_args.kwargs["memory_id"] == "custom-memory-id"
            assert config_call_args.kwargs["session_id"] == "custom-session-id"
            assert config_call_args.kwargs["actor_id"] == "custom-actor-id"

    def test_create_memory_uses_correct_region(self):
        """
        正しいリージョンが設定されることを確認する。
        """
        from app.memory import create_memory

        with (
            patch("app.memory.AgentCoreMemorySessionManager") as mock_manager,
            patch("app.memory.AgentCoreMemoryConfig"),
            patch("app.memory.create_retrieval_config") as mock_retrieval,
        ):
            mock_manager.return_value = MagicMock()
            mock_retrieval.return_value = None

            create_memory(mem_id="test-memory", session_id="test-session", actor_id="test-actor")

            manager_call_args = mock_manager.call_args
            assert manager_call_args.kwargs["region_name"] == "ap-northeast-1"

    def test_create_memory_config_passed_to_session_manager(self):
        """
        AgentCoreMemoryConfigがSessionManagerに正しく渡されることを確認する。
        """
        from app.memory import create_memory

        with (
            patch("app.memory.AgentCoreMemorySessionManager") as mock_manager,
            patch("app.memory.AgentCoreMemoryConfig") as mock_config,
            patch("app.memory.create_retrieval_config") as mock_retrieval,
        ):
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_manager.return_value = MagicMock()
            mock_retrieval.return_value = None

            create_memory(mem_id="test-memory", session_id="test-session", actor_id="test-actor")

            manager_call_args = mock_manager.call_args
            assert manager_call_args.kwargs["agentcore_memory_config"] == mock_config_instance

    def test_create_memory_with_ltm_enabled(self):
        """
        LTM有効時にRetrievalConfigがセッションマネージャーに渡されることを確認する。
        """
        from app.memory import create_memory

        mock_retrieval_config = {"/file-summaries/{actorId}": {"top_k": 10, "relevance_score": 0.3}}

        with (
            patch("app.memory.AgentCoreMemorySessionManager") as mock_manager,
            patch("app.memory.AgentCoreMemoryConfig") as mock_config,
            patch("app.memory.create_retrieval_config") as mock_retrieval,
        ):
            mock_manager.return_value = MagicMock()
            mock_retrieval.return_value = mock_retrieval_config

            create_memory(mem_id="test-memory", session_id="test-session", actor_id="test-actor")

            # RetrievalConfigがAgentCoreMemoryConfigに渡されていることを確認
            config_call_args = mock_config.call_args
            assert config_call_args.kwargs["retrieval_config"] == mock_retrieval_config
