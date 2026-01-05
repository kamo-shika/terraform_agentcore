"""
Strands Agentsで使用可能なカスタムツール。

このモジュールは、AgentCore Memoryと連携する以下のツールを提供する：
- retrieve_memory_tool: 過去の要約データをセマンティック検索で取得
- save_memory_tool: メモリにデータを保存
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from botocore.exceptions import ClientError
from strands.tools import tool

from .config import (
    ACTOR_STATE_NAMESPACE,
    ACTOR_STATE_TOP_K,
    LTM_ENABLED,
    LTM_NAMESPACE,
    LTM_SUMMARY_TOP_K,
)
from .memory import _get_agentcore_client, _resolve_namespace

logger = logging.getLogger(__name__)


@tool
def retrieve_memory_tool(
    memory_id: str,
    actor_id: str,
    query: str,
    top_k: int = LTM_SUMMARY_TOP_K,
) -> list[dict[str, Any]]:
    """
    過去の要約データをAgentCore Memoryからセマンティック検索で取得する。

    このツールは、RetrieveMemoryRecords APIを使用して、クエリに関連する
    過去のメモリレコードを検索・取得する。

    Args:
        memory_id: AgentCore MemoryのID
        actor_id: アクターID（ユーザーID）
        query: 検索クエリ（ファイル内容やファイル名など）
        top_k: 取得する最大件数（デフォルト: LTM_SUMMARY_TOP_K）

    Returns:
        メモリレコードのリスト。各レコードは以下のキーを含む:
        - memoryRecordId: レコードID
        - content: 要約内容（テキスト）
        - relevanceScore: 関連度スコア
    """
    # LTMが無効の場合は空リストを返す
    if not LTM_ENABLED:
        logger.info("LTM is disabled, returning empty list")
        return []

    # memory_idが空の場合は空リストを返す
    if not memory_id or not memory_id.strip():
        logger.warning("Empty memory_id, returning empty list")
        return []

    # actor_idが空の場合は空リストを返す
    if not actor_id or not actor_id.strip():
        logger.warning("Empty actor_id, returning empty list")
        return []

    # クエリが空の場合は空リストを返す
    if not query or not query.strip():
        logger.warning("Empty query, returning empty list")
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
        logger.info(f"Retrieved {len(records)} memory records for actor={actor_id}")

        # テストが期待する形式に変換
        return [
            {
                "memoryRecordId": record.get("memoryRecordId"),
                "content": record.get("content", {}).get("text", ""),
                "relevanceScore": record.get("relevanceScore", 0.0),
            }
            for record in records
        ]

    except ClientError as e:
        logger.error(f"Failed to retrieve memory records: {e}")
        # エラー時は空リストを返す
        return []


@tool
def save_memory_tool(
    namespace: str,
    memory_id: str,
    actor_id: str,
    content: str,
) -> str | None:
    """
    メモリにデータを保存する。

    このツールは、BatchCreateMemoryRecords APIを使用して、
    新しいメモリレコードを長期メモリに保存する。

    Args:
        namespace: メモリレコードを保存するNamespace（{actorId}は自動置換される）
        memory_id: AgentCore MemoryのID
        actor_id: アクターID（ユーザーID）
        content: 保存するコンテンツ（テキスト）

    Returns:
        作成されたメモリレコードのID、失敗時はNone
    """
    # LTMが無効の場合はNoneを返す
    if not LTM_ENABLED:
        logger.info("LTM is disabled, skipping save")
        return None

    # contentが空の場合はNoneを返す
    if not content or not content.strip():
        logger.warning("Empty content, skipping save")
        return None

    # memory_idが空の場合はNoneを返す
    if not memory_id or not memory_id.strip():
        logger.warning("Empty memory_id, skipping save")
        return None

    # actor_idが空の場合はNoneを返す
    if not actor_id or not actor_id.strip():
        logger.warning("Empty actor_id, skipping save")
        return None

    # namespaceが空の場合はNoneを返す
    if not namespace or not namespace.strip():
        logger.warning("Empty namespace, skipping save")
        return None

    client = _get_agentcore_client()
    resolved_namespace = _resolve_namespace(namespace, actor_id)

    # ユニークなリクエストIDを生成
    request_id = f"memory-{actor_id}-{uuid.uuid4().hex[:8]}"
    # UNIXタイムスタンプ（秒）を整数で取得
    timestamp = int(datetime.now(UTC).timestamp())

    try:
        response = client.batch_create_memory_records(
            memoryId=memory_id,
            records=[
                {
                    "requestIdentifier": request_id,
                    "namespaces": [resolved_namespace],
                    "content": {
                        "text": content,
                    },
                    "timestamp": timestamp,
                }
            ],
        )

        # 成功したレコードIDを確認
        successful = response.get("successfulRecords", [])
        if successful:
            created_id = successful[0].get("memoryRecordId")
            logger.info(f"Saved memory record: {created_id}")
            return created_id

        # 失敗したレコードを確認
        failed = response.get("failedRecords", [])
        if failed:
            error_msg = failed[0].get("failureReason", "Unknown error")
            logger.error(f"Failed to save memory record: {error_msg}")
            return None

        return None

    except ClientError as e:
        logger.error(f"Failed to save memory record: {e}")
        # エラー時はNoneを返す
        return None


@tool
def save_to_memory_via_event(
    memory_id: str,
    session_id: str,
    actor_id: str,
    user_content: str,
    assistant_content: str,
) -> dict[str, Any] | None:
    """
    create_event APIを使用してメモリに会話形式で保存する。

    この関数は、batch_create_memory_recordsとは異なり、
    Memory Strategyによる自動処理（Extraction/Consolidation）を有効にする。
    これにより、USER_PREFERENCE戦略でユーザーの嗜好が自動抽出される。

    Args:
        memory_id: AgentCore MemoryのID
        session_id: セッションID
        actor_id: アクターID（ユーザーID）
        user_content: ユーザーメッセージ（ファイル内容など）
        assistant_content: アシスタントメッセージ（分析結果など）

    Returns:
        create_event APIのレスポンス、失敗時はNone
    """
    # LTMが無効の場合はNoneを返す
    if not LTM_ENABLED:
        logger.info("LTM is disabled, skipping save via event")
        return None

    # memory_idが空の場合はNoneを返す
    if not memory_id or not memory_id.strip():
        logger.warning("Empty memory_id, skipping save via event")
        return None

    # session_idが空の場合はNoneを返す
    if not session_id or not session_id.strip():
        logger.warning("Empty session_id, skipping save via event")
        return None

    # actor_idが空の場合はNoneを返す
    if not actor_id or not actor_id.strip():
        logger.warning("Empty actor_id, skipping save via event")
        return None

    # user_contentが空の場合はNoneを返す
    if not user_content or not user_content.strip():
        logger.warning("Empty user_content, skipping save via event")
        return None

    # assistant_contentが空の場合はNoneを返す
    if not assistant_content or not assistant_content.strip():
        logger.warning("Empty assistant_content, skipping save via event")
        return None

    client = _get_agentcore_client()

    try:
        response = client.create_event(
            memoryId=memory_id,
            sessionId=session_id,
            actorId=actor_id,
            event={
                "conversationEvent": {
                    "messages": [
                        {"role": "USER", "content": {"text": user_content}},
                        {"role": "ASSISTANT", "content": {"text": assistant_content}},
                    ]
                }
            },
        )

        logger.info(f"Created event for actor={actor_id}, session={session_id}")
        return response

    except ClientError as e:
        logger.error(f"Failed to create event: {e}")
        return None


@tool
def get_past_preferences(memory_id: str, actor_id: str) -> str:
    """
    過去の嗜好・傾向データを取得する。

    /actor-state/{actorId}名前空間から、ユーザーの過去の嗜好や傾向を
    セマンティック検索で取得する。エージェントが分析時にこのデータを
    参照することで、より精度の高い分析が可能になる。

    Args:
        memory_id: AgentCore MemoryのID
        actor_id: アクターID（ユーザーID）

    Returns:
        過去の嗜好データをテキストとして結合した文字列。
        データがない場合やエラー時は空文字列を返す。
    """
    # LTMが無効の場合は空文字列を返す
    if not LTM_ENABLED:
        logger.info("LTM is disabled, returning empty preferences")
        return ""

    # memory_idが空の場合は空文字列を返す
    if not memory_id or not memory_id.strip():
        logger.warning("Empty memory_id, returning empty preferences")
        return ""

    # actor_idが空の場合は空文字列を返す
    if not actor_id or not actor_id.strip():
        logger.warning("Empty actor_id, returning empty preferences")
        return ""

    client = _get_agentcore_client()
    namespace = _resolve_namespace(ACTOR_STATE_NAMESPACE, actor_id)

    try:
        response = client.retrieve_memory_records(
            memoryId=memory_id,
            namespace=namespace,
            searchCriteria={
                "searchQuery": "ユーザーの嗜好、好み、傾向、スタイル、preference",
                "topK": ACTOR_STATE_TOP_K,
            },
        )

        records = response.get("memoryRecordSummaries", [])
        logger.info(f"Retrieved {len(records)} preference records for actor={actor_id}")

        if not records:
            return ""

        # 嗜好データをテキストとして結合
        preferences = [
            record.get("content", {}).get("text", "")
            for record in records
            if record.get("content", {}).get("text")
        ]

        return "\n".join(preferences)

    except ClientError as e:
        logger.error(f"Failed to retrieve preferences: {e}")
        return ""
