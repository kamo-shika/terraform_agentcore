"""
app/agent.pyのテスト。

create_agent関数の動作を検証する。
Agentオブジェクトの作成自体は課金が発生しないためモックなしでテスト可能。
"""

from strands import Agent

from app.agent import create_agent


class TestCreateAgent:
    """create_agent関数のテストクラス。"""

    def test_create_agent_returns_agent_instance(self):
        """
        create_agentがAgentインスタンスを返すことを確認。
        """
        agent = create_agent()

        assert isinstance(agent, Agent)

    def test_create_agent_has_correct_name(self):
        """
        作成されたエージェントが正しい名前を持つことを確認。
        """
        agent = create_agent()

        assert agent.name == "S3FileProcessingAgent"

    def test_create_agent_has_correct_model(self):
        """
        作成されたエージェントが正しいモデルを使用していることを確認。
        """
        agent = create_agent()

        # モデルIDはmodel.configから取得
        model_id = agent.model.config.get("model_id")
        assert model_id == "jp.amazon.nova-2-lite-v1:0"

    def test_create_agent_has_use_aws_tool(self):
        """
        作成されたエージェントがuse_awsツールを持つことを確認。
        """
        agent = create_agent()

        # ツール名のリストでuse_awsが含まれているか確認
        assert "use_aws" in agent.tool_names

    def test_create_agent_with_default_prompt(self):
        """
        デフォルトのシステムプロンプトが設定されることを確認。
        """
        agent = create_agent()

        assert agent.system_prompt == "You are a helpful assistant. Answer concisely."

    def test_create_agent_with_custom_prompt(self):
        """
        カスタムシステムプロンプトが正しく設定されることを確認。
        """
        custom_prompt = "あなたはファイル要約の専門家です。"
        agent = create_agent(system_prompt=custom_prompt)

        assert agent.system_prompt == custom_prompt

    def test_create_agent_without_session_manager(self):
        """
        session_managerなしでエージェントが作成できることを確認。

        注意: session_managerがNoneの場合、Strands AgentはデフォルトのConversationManagerを使用。
        """
        agent = create_agent(session_manager=None)

        # デフォルトのConversationManagerが設定される
        assert agent.conversation_manager is not None

    def test_create_agent_with_session_manager_does_not_raise(self):
        """
        session_managerを渡してもエラーが発生しないことを確認。

        注意: Strands Agentの内部実装により、session_managerの扱いは
        フレームワーク側で管理される。ここではエラーなく動作することを確認。
        """
        from unittest.mock import MagicMock

        mock_session_manager = MagicMock()

        # エラーが発生しないことを確認
        agent = create_agent(session_manager=mock_session_manager)

        assert isinstance(agent, Agent)
        assert agent.conversation_manager is not None

    def test_create_agent_with_all_parameters(self):
        """
        すべてのパラメータを指定してエージェントが作成できることを確認。
        """
        from unittest.mock import MagicMock

        custom_prompt = "カスタムプロンプト"
        mock_session_manager = MagicMock()

        agent = create_agent(session_manager=mock_session_manager, system_prompt=custom_prompt)

        assert agent.system_prompt == custom_prompt
        assert agent.name == "S3FileProcessingAgent"
        assert agent.conversation_manager is not None
