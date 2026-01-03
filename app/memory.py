from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from .config import REGION


def create_memory(mem_id: str, session_id: str, actor_id: str) -> AgentCoreMemorySessionManager:
    """
    Strandsエージェント用のAgentCore Memoryセッションマネージャーを作成する。

    Args:
        mem_id: AgentCore MemoryのID
        session_id: セッションID
        actor_id: アクターID（ユーザーID）

    Returns:
        設定済みのAgentCoreMemorySessionManagerインスタンス

    Raises:
        ValueError: mem_id、session_id、actor_idのいずれかが空の場合
        Exception: AgentCore Memory初期化時の例外
    """
    agentcore_memory_config = AgentCoreMemoryConfig(memory_id=mem_id, session_id=session_id, actor_id=actor_id)

    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config, region_name=REGION
    )
    return session_manager
