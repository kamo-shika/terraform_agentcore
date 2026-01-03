import logging
from typing import Optional, Dict, Any
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from .config import (
    REGION,
    LTM_ENABLED,
    LTM_SUMMARY_TOP_K,
    LTM_SUMMARY_SCORE,
    LTM_NAMESPACE,
)

logger = logging.getLogger(__name__)


def create_retrieval_config() -> Optional[Dict[str, Any]]:
    """
    LTM用のRetrievalConfigを作成する。

    LTM_ENABLEDがtrueの場合、過去のファイル要約を取得するための
    RetrievalConfig設定を返す。

    Returns:
        LTM有効時: Namespace -> RetrievalConfig設定の辞書
        LTM無効時: None
    """
    if not LTM_ENABLED:
        return None

    # 過去のファイル要約を取得するための設定
    # RetrievalConfigの形式はSDKに依存するため、辞書形式で定義
    return {
        LTM_NAMESPACE: {
            "top_k": LTM_SUMMARY_TOP_K,
            "relevance_score": LTM_SUMMARY_SCORE,
        }
    }


def create_memory(mem_id: str, session_id: str, actor_id: str) -> AgentCoreMemorySessionManager:
    """
    Strandsエージェント用のAgentCore Memoryセッションマネージャーを作成する。

    LTM_ENABLEDがtrueの場合、過去のファイル要約を取得するための
    RetrievalConfigも設定される。

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
    retrieval_config = create_retrieval_config()

    agentcore_memory_config = AgentCoreMemoryConfig(
        memory_id=mem_id,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config=retrieval_config,
    )

    session_manager = AgentCoreMemorySessionManager(
        agentcore_memory_config=agentcore_memory_config, region_name=REGION
    )
    return session_manager
