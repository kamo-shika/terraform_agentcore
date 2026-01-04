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

    # ユニークなレコードIDを生成
    record_id = f"memory-{actor_id}-{uuid.uuid4().hex[:8]}"
    timestamp = datetime.now(UTC).isoformat()

    try:
        response = client.batch_create_memory_records(
            memoryId=memory_id,
            memoryRecords=[
                {
                    "memoryRecordId": record_id,
                    "namespace": resolved_namespace,
                    "content": {
                        "text": content,
                    },
                    "metadata": {
                        "actorId": actor_id,
                        "createdAt": timestamp,
                        "type": "memory",
                    },
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
