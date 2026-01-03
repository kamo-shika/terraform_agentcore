from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager


def create_memory(mem_id: str, session_id: str, actor_id: str):
    """
    StrandsAgents の AgentCoreMemorySessionManagerを使って、
    AgentCore の Memory を管理する
    """
    agentcore_memory_config = AgentCoreMemoryConfig(memory_id=mem_id, session_id=session_id, actor_id=actor_id)

    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config, region_name="ap-northeast-1"
    )
    return session_manager
