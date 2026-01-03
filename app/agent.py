import logging
from typing import Optional
from strands import Agent
from strands_tools import use_aws
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from .config import MODEL_ID

logger = logging.getLogger(__name__)


def create_agent(
    session_manager: Optional[AgentCoreMemorySessionManager] = None,
    system_prompt: Optional[str] = None
) -> Agent:
    """
    S3ファイル読み取り機能を持つエージェントを作成する。

    Args:
        session_manager: AgentCore Memoryセッションマネージャー（オプション）
        system_prompt: カスタムシステムプロンプト（オプション、デフォルト：汎用的なアシスタント）

    Returns:
        設定済みのStrandsエージェントインスタンス
    """
    default_prompt = "You are a helpful assistant. Answer concisely."

    agent = Agent(
        name="S3FileProcessingAgent",
        model=MODEL_ID,
        system_prompt=system_prompt or default_prompt,
        tools=[use_aws],  # S3操作用のAWSツールを追加
        session_manager=session_manager,
    )
    return agent
