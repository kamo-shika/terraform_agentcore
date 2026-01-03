import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import boto3
from botocore.exceptions import ClientError
from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
from .config import (
    REGION,
    LTM_ENABLED,
    LTM_SUMMARY_TOP_K,
    LTM_SUMMARY_SCORE,
    LTM_NAMESPACE,
    ACTOR_STATE_NAMESPACE,
    ACTOR_STATE_TOP_K,
)

logger = logging.getLogger(__name__)

# boto3クライアントの初期化（モジュールレベルで再利用）
_agentcore_client = None


def _get_agentcore_client():
    """
    AgentCoreデータプレーンクライアントを取得する（シングルトン）。

    Returns:
        boto3のbedrock-agentcoreクライアント
    """
    global _agentcore_client
    if _agentcore_client is None:
        _agentcore_client = boto3.client("bedrock-agentcore", region_name=REGION)
    return _agentcore_client


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


def _resolve_namespace(namespace_template: str, actor_id: str) -> str:
    """
    Namespaceテンプレート内の{actorId}を実際の値に置換する。

    Args:
        namespace_template: Namespaceテンプレート（例: "/file-summaries/{actorId}"）
        actor_id: 置換するアクターID

    Returns:
        解決済みのNamespace文字列
    """
    return namespace_template.replace("{actorId}", actor_id)


def retrieve_past_summaries(
    memory_id: str,
    actor_id: str,
    query: str,
    top_k: int = LTM_SUMMARY_TOP_K,
) -> List[Dict[str, Any]]:
    """
    過去のファイル要約をセマンティック検索で取得する。

    RetrieveMemoryRecords APIを使用して、クエリに関連する
    過去のファイル要約を検索・取得する。

    Args:
        memory_id: AgentCore MemoryのID
        actor_id: アクターID
        query: 検索クエリ（ファイル内容やファイル名など）
        top_k: 取得する最大件数（デフォルト: LTM_SUMMARY_TOP_K）

    Returns:
        メモリレコードのリスト。各レコードは以下のキーを含む:
        - memoryRecordId: レコードID
        - content: 要約内容
        - relevanceScore: 関連度スコア

    Raises:
        ClientError: AWS API呼び出しに失敗した場合
    """
    if not LTM_ENABLED:
        logger.info("LTM is disabled, skipping past summaries retrieval")
        return []

    client = _get_agentcore_client()
    namespace = _resolve_namespace(LTM_NAMESPACE, actor_id)

    try:
        response = client.retrieve_memory_records(
            memoryId=memory_id,
            namespace=namespace,
            searchCriteria={
                "searchQuery": query,
                "topK": top_k,
            },
        )

        records = response.get("memoryRecordSummaries", [])
        logger.info(f"Retrieved {len(records)} past summaries for actor={actor_id}")

        return [
            {
                "memoryRecordId": record.get("memoryRecordId"),
                "content": record.get("content", {}).get("text", ""),
                "relevanceScore": record.get("relevanceScore", 0.0),
            }
            for record in records
        ]

    except ClientError as e:
        logger.error(f"Failed to retrieve past summaries: {e}")
        raise


def retrieve_actor_state(
    memory_id: str,
    actor_id: str,
    query: str = "直近の活動状態",
    top_k: int = ACTOR_STATE_TOP_K,
) -> List[Dict[str, Any]]:
    """
    Actorの活動状態をセマンティック検索で取得する。

    RetrieveMemoryRecords APIを使用して、Actor状態Namespaceから
    過去の活動状態を検索・取得する。

    Args:
        memory_id: AgentCore MemoryのID
        actor_id: アクターID
        query: 検索クエリ（デフォルト: "直近の活動状態"）
        top_k: 取得する最大件数（デフォルト: ACTOR_STATE_TOP_K）

    Returns:
        メモリレコードのリスト。各レコードは以下のキーを含む:
        - memoryRecordId: レコードID
        - content: 状態内容
        - relevanceScore: 関連度スコア

    Raises:
        ClientError: AWS API呼び出しに失敗した場合
    """
    if not LTM_ENABLED:
        logger.info("LTM is disabled, skipping actor state retrieval")
        return []

    client = _get_agentcore_client()
    namespace = _resolve_namespace(ACTOR_STATE_NAMESPACE, actor_id)

    try:
        response = client.retrieve_memory_records(
            memoryId=memory_id,
            namespace=namespace,
            searchCriteria={
                "searchQuery": query,
                "topK": top_k,
            },
        )

        records = response.get("memoryRecordSummaries", [])
        logger.info(f"Retrieved {len(records)} actor state records for actor={actor_id}")

        return [
            {
                "memoryRecordId": record.get("memoryRecordId"),
                "content": record.get("content", {}).get("text", ""),
                "relevanceScore": record.get("relevanceScore", 0.0),
            }
            for record in records
        ]

    except ClientError as e:
        logger.error(f"Failed to retrieve actor state: {e}")
        raise


def save_actor_state(
    memory_id: str,
    actor_id: str,
    state_text: str,
) -> Optional[str]:
    """
    Actorの活動状態をメモリに保存する。

    BatchCreateMemoryRecords APIを使用して、新しいActor状態を
    長期メモリに保存する。

    Args:
        memory_id: AgentCore MemoryのID
        actor_id: アクターID
        state_text: 保存する状態テキスト

    Returns:
        作成されたメモリレコードのID、失敗時はNone

    Raises:
        ClientError: AWS API呼び出しに失敗した場合
    """
    if not LTM_ENABLED:
        logger.info("LTM is disabled, skipping actor state save")
        return None

    if not state_text or not state_text.strip():
        logger.warning("Empty state text, skipping actor state save")
        return None

    client = _get_agentcore_client()
    namespace = _resolve_namespace(ACTOR_STATE_NAMESPACE, actor_id)

    # ユニークなレコードIDを生成
    record_id = f"actor-state-{actor_id}-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(timezone.utc).isoformat()

    try:
        response = client.batch_create_memory_records(
            memoryId=memory_id,
            memoryRecords=[
                {
                    "memoryRecordId": record_id,
                    "namespace": namespace,
                    "content": {
                        "text": state_text,
                    },
                    "metadata": {
                        "actorId": actor_id,
                        "createdAt": timestamp,
                        "type": "actor_state",
                    },
                }
            ],
        )

        # 成功したレコードIDを確認
        successful = response.get("successfulRecords", [])
        if successful:
            created_id = successful[0].get("memoryRecordId")
            logger.info(f"Saved actor state: {created_id}")
            return created_id

        # 失敗したレコードを確認
        failed = response.get("failedRecords", [])
        if failed:
            error_msg = failed[0].get("failureReason", "Unknown error")
            logger.error(f"Failed to save actor state: {error_msg}")
            return None

        return None

    except ClientError as e:
        logger.error(f"Failed to save actor state: {e}")
        raise
