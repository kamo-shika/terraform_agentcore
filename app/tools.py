"""
Strands Agentsで使用可能なカスタムツール。

このモジュールは、AgentCore Memoryと連携する以下のツールを提供する：
- retrieve_memory_tool: 過去の要約データをセマンティック検索で取得
- get_past_preferences: 過去の嗜好・傾向データを取得
"""

import logging
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
    # 早期リターン: 必須条件のバリデーション
    if not LTM_ENABLED:
        logger.info("LTM is disabled, returning empty list")
        return []
    if not memory_id or not memory_id.strip():
        logger.warning("Empty memory_id, returning empty list")
        return []
    if not actor_id or not actor_id.strip():
        logger.warning("Empty actor_id, returning empty list")
        return []
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

        # APIレスポンスを統一形式に正規化
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
def get_past_preferences(memory_id: str, actor_id: str) -> str:
    """
    過去の嗜好・傾向データを取得する。

    /life-events/{actorId}名前空間から、顧客の過去のライフイベント検出結果を
    セマンティック検索で取得する。エージェントが分析時にこのデータを
    参照することで、より精度の高い分析が可能になる。

    Args:
        memory_id: AgentCore MemoryのID
        actor_id: アクターID（ユーザーID）

    Returns:
        過去の嗜好データをテキストとして結合した文字列。
        データがない場合やエラー時は空文字列を返す。
    """
    # 早期リターン: 必須条件のバリデーション
    if not LTM_ENABLED:
        logger.info("LTM is disabled, returning empty preferences")
        return ""
    if not memory_id or not memory_id.strip():
        logger.warning("Empty memory_id, returning empty preferences")
        return ""
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
