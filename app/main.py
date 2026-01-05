import logging
from typing import Any

from .config import get_actor_id, get_input_text, get_memory_id, get_session_id
from .workflow import run_workflow

# ロギング設定はconfig.pyで一元管理されている
logger = logging.getLogger(__name__)

# アプリケーションバージョン（デプロイ追跡用）
APP_VERSION = "1.2.0"


def parse_event(event: dict[str, Any]) -> dict[str, Any]:
    """
    イベントから必要な情報を抽出する。

    Args:
        event: AgentCoreから渡されるイベント辞書

    Returns:
        以下のキーを含む辞書:
            - session_id (str): セッションID
            - actor_id (str): アクターID
            - user_input (str): ユーザー入力テキスト
            - s3_info (Optional[Dict[str, str]]): S3情報（存在する場合）またはNone
    """
    return {
        "session_id": get_session_id(event),
        "actor_id": get_actor_id(event),
        "user_input": get_input_text(event),
        "s3_info": event.get("s3_info"),
    }


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Bedrock AgentCore Runtimeのエントリーポイント。

    S3ファイル処理のみに対応する。

    Args:
        event: AgentCoreから渡されるイベント辞書
        context: 実行コンテキスト

    Returns:
        以下の形式の辞書:
            - statusCode (int): HTTPステータスコード（200または500）
            - body (Dict[str, str]): レスポンスボディ（responseまたはerrorキーを含む）

    Raises:
        Exception: ワークフロー実行時の例外（catchされて500エラーとして返される）
    """
    logger.info("App version: %s - Received event: %s", APP_VERSION, event)

    try:
        # イベント解析
        parsed = parse_event(event)
        actor_id = parsed["actor_id"]
        session_id = parsed["session_id"]
        s3_info = parsed["s3_info"]

        # メモリID取得
        memory_id = get_memory_id()

        # S3情報が必須
        if not s3_info:
            raise ValueError("s3_info is required. This handler only supports S3 workflow mode.")

        bucket = s3_info.get("bucket")
        key = s3_info.get("key")
        logger.info(f"S3 file processing request: s3://{bucket}/{key}")

        # メモリIDが必要
        if not memory_id:
            raise ValueError("Memory ID is required for S3 workflow processing")

        # ワークフロー実行
        profile_result = run_workflow(s3_info, actor_id, session_id, memory_id)
        logger.info("Workflow completed successfully")

        return {"statusCode": 200, "body": {"response": profile_result}}
    except Exception as e:
        # エラーのコンテキスト情報をログに出力
        logger.error("Error running workflow: %s", e, exc_info=True)

        return {"statusCode": 500, "body": {"error": str(e)}}
