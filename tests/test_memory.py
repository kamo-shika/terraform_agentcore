"""
app/memory.py のテスト。

AgentCore Memoryの統合設定をテストする。
"""

import pytest
from unittest.mock import patch, MagicMock


class TestCreateMemory:
    """
    create_memory関数のテスト。
    """

    def test_create_memory_returns_session_manager(self):
        """
        create_memoryがセッションマネージャーを返すことを確認する。
        """
        from app.memory import create_memory

        with patch("app.memory.AgentCoreMemorySessionManager") as mock_manager, \
             patch("app.memory.AgentCoreMemoryConfig") as mock_config:
            mock_manager.return_value = MagicMock()

            result = create_memory(
                mem_id="test-memory",
                session_id="test-session",
                actor_id="test-actor"
            )

            assert result is not None
            mock_config.assert_called_once_with(
                memory_id="test-memory",
                session_id="test-session",
                actor_id="test-actor"
            )
            mock_manager.assert_called_once()

    def test_create_memory_with_different_parameters(self):
        """
        異なるパラメータでcreate_memoryが動作することを確認する。
        """
        from app.memory import create_memory

        with patch("app.memory.AgentCoreMemorySessionManager") as mock_manager, \
             patch("app.memory.AgentCoreMemoryConfig") as mock_config:
            mock_manager.return_value = MagicMock()

            # 別のパラメータで呼び出し
            result = create_memory(
                mem_id="custom-memory-id",
                session_id="custom-session-id",
                actor_id="custom-actor-id"
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

        with patch("app.memory.AgentCoreMemorySessionManager") as mock_manager, \
             patch("app.memory.AgentCoreMemoryConfig"):
            mock_manager.return_value = MagicMock()

            create_memory(
                mem_id="test-memory",
                session_id="test-session",
                actor_id="test-actor"
            )

            manager_call_args = mock_manager.call_args
            assert manager_call_args.kwargs["region_name"] == "ap-northeast-1"

    def test_create_memory_config_passed_to_session_manager(self):
        """
        AgentCoreMemoryConfigがSessionManagerに正しく渡されることを確認する。
        """
        from app.memory import create_memory

        with patch("app.memory.AgentCoreMemorySessionManager") as mock_manager, \
             patch("app.memory.AgentCoreMemoryConfig") as mock_config:
            mock_config_instance = MagicMock()
            mock_config.return_value = mock_config_instance
            mock_manager.return_value = MagicMock()

            create_memory(
                mem_id="test-memory",
                session_id="test-session",
                actor_id="test-actor"
            )

            manager_call_args = mock_manager.call_args
            assert manager_call_args.kwargs["agentcore_memory_config"] == mock_config_instance
