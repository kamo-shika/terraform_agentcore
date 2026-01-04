import logging
from typing import Any

from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager

from .agent import create_agent
from .config import REGION, get_actor_id, get_input_text, get_memory_id, get_session_id
from .memory import (
    create_memory,
    retrieve_actor_state,
    retrieve_past_summaries,
)
from .workflow import run_workflow

# ロギング設定はconfig.pyで一元管理されている
logger = logging.getLogger(__name__)

# アプリケーションバージョン（デプロイ追跡用）
APP_VERSION = "1.1.0"


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


def initialize_memory(memory_id: str, session_id: str, actor_id: str) -> AgentCoreMemorySessionManager | None:
    """
    メモリを初期化する。

    Args:
        memory_id: メモリID（Noneまたは空文字列の場合はNoneを返す）
        session_id: セッションID
        actor_id: アクターID

    Returns:
        AgentCoreMemorySessionManagerオブジェクト、またはNone（メモリIDがない場合やエラー時）

    Raises:
        Exception: メモリ初期化時の例外（catchされてNoneが返される）
    """
    if not memory_id:
        return None

    try:
        session_manager = create_memory(memory_id, session_id, actor_id)
        logger.info(f"Memory enabled: memory_id={memory_id}, session_id={session_id}, actor_id={actor_id}")
        return session_manager
    except Exception as e:
        logger.warning(f"Failed to initialize memory: {e}")
        return None


def build_s3_instruction(bucket: str, key: str) -> str:
    """
    S3ファイル処理用の命令文字列を生成する。

    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー

    Returns:
        S3ファイル処理用の命令文字列（エージェントへの指示を含む）

    Raises:
        ValueError: bucketまたはkeyがNoneまたは空文字列の場合
    """
    if not bucket:
        raise ValueError("bucket is required and cannot be None or empty")
    if not key:
        raise ValueError("key is required and cannot be None or empty")

    return (
        f"S3バケット '{bucket}' のファイル '{key}' を読み取り、内容を要約してください。\n"
        f"use_awsツールを使用して以下のパラメータでファイルを取得してください:\n"
        f"- service_name: 's3'\n"
        f"- operation_name: 'get_object'\n"
        f"- parameters: {{'Bucket': '{bucket}', 'Key': '{key}'}}\n"
        f"- region: '{REGION}'"
    )


def run_agent(
    user_input: str,
    session_manager: AgentCoreMemorySessionManager | None = None,
    system_prompt: str | None = None,
) -> Any:
    """
    エージェントを実行する。

    Args:
        user_input: ユーザー入力テキスト
        session_manager: セッションマネージャー（オプション）
        system_prompt: システムプロンプト（オプション）

    Returns:
        エージェントの応答（Strandsエージェントからの戻り値）
    """
    agent = create_agent(session_manager=session_manager, system_prompt=system_prompt)
    response = agent(user_input)
    return response


def fetch_memory_context(
    memory_id: str,
    actor_id: str,
    query: str,
) -> dict[str, Any]:
    """
    メモリから過去の要約とActor状態を取得する。

    Args:
        memory_id: メモリID
        actor_id: アクターID
        query: 検索クエリ（ファイル内容やファイル名など）

    Returns:
        以下のキーを含む辞書:
        - past_summaries: 過去のファイル要約リスト
        - actor_state: Actor状態リスト
    """
    context = {
        "past_summaries": [],
        "actor_state": [],
    }

    try:
        # 過去のファイル要約を取得
        past_summaries = retrieve_past_summaries(memory_id, actor_id, query)
        context["past_summaries"] = past_summaries
        logger.info(f"Retrieved {len(past_summaries)} past summaries")
    except Exception as e:
        logger.warning(f"Failed to retrieve past summaries: {e}")

    try:
        # Actor状態を取得
        actor_state = retrieve_actor_state(memory_id, actor_id)
        context["actor_state"] = actor_state
        logger.info(f"Retrieved {len(actor_state)} actor state records")
    except Exception as e:
        logger.warning(f"Failed to retrieve actor state: {e}")

    return context


def format_memory_context(context: dict[str, Any]) -> str:
    """
    メモリコンテキストをプロンプト用の文字列にフォーマットする。

    Args:
        context: fetch_memory_contextの戻り値

    Returns:
        プロンプトに追加するためのフォーマット済み文字列
    """
    lines = []

    # 過去のファイル要約
    past_summaries = context.get("past_summaries", [])
    if past_summaries:
        lines.append("## 過去のファイル要約")
        for i, summary in enumerate(past_summaries, 1):
            content = summary.get("content", "")
            score = summary.get("relevanceScore", 0.0)
            lines.append(f"### 要約 {i} (関連度: {score:.2f})")
            lines.append(content)
            lines.append("")

    # Actor状態
    actor_state = context.get("actor_state", [])
    if actor_state:
        lines.append("## Actorの直近の活動状態")
        for i, state in enumerate(actor_state, 1):
            content = state.get("content", "")
            lines.append(f"### 状態 {i}")
            lines.append(content)
            lines.append("")

    return "\n".join(lines) if lines else ""


def generate_actor_state_summary(
    file_key: str,
    response_text: str,
    past_summaries_count: int,
) -> str:
    """
    エージェントの応答からActor状態サマリーを生成する。

    Args:
        file_key: 処理したファイルのS3キー
        response_text: エージェントの応答テキスト
        past_summaries_count: 参照した過去の要約数

    Returns:
        Actor状態として保存するサマリーテキスト
    """
    # 応答テキストが長すぎる場合は最初の500文字に制限
    summary_excerpt = response_text[:500] if len(response_text) > 500 else response_text

    return f"ファイル処理: {file_key}\n参照した過去の要約数: {past_summaries_count}\n処理結果の概要:\n{summary_excerpt}"


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Bedrock AgentCore Runtimeのエントリーポイント。

    通常の呼び出しとS3ファイル処理の両方に対応する。

    Args:
        event: AgentCoreから渡されるイベント辞書
        context: 実行コンテキスト

    Returns:
        以下の形式の辞書:
            - statusCode (int): HTTPステータスコード（200または500）
            - body (Dict[str, str]): レスポンスボディ（responseまたはerrorキーを含む）

    Raises:
        Exception: エージェント実行時の例外（catchされて500エラーとして返される）
    """
    logger.info("App version: %s - Received event: %s", APP_VERSION, event)

    try:
        # イベント解析
        parsed = parse_event(event)
        session_id = parsed["session_id"]
        actor_id = parsed["actor_id"]
        user_input = parsed["user_input"]
        s3_info = parsed["s3_info"]

        # メモリ初期化
        memory_id = get_memory_id()
        session_manager = None
        if memory_id:
            session_manager = initialize_memory(memory_id, session_id, actor_id)
        else:
            logger.info("Memory disabled (no AGENTCORE_MEMORY_ID)")

        # S3ファイル処理モード - workflowを使用
        if s3_info:
            bucket = s3_info.get("bucket")
            key = s3_info.get("key")
            logger.info(f"S3 file processing request (workflow mode): s3://{bucket}/{key}")

            # メモリIDが必要
            if not memory_id:
                raise ValueError("Memory ID is required for S3 workflow processing")

            # ワークフロー実行
            profile_result = run_workflow(s3_info, actor_id, memory_id)
            logger.info("Workflow completed successfully")

            return {"statusCode": 200, "body": {"response": profile_result}}

        # 通常モード - 既存のエージェント直接呼び出し
        # エージェント実行
        response = run_agent(user_input, session_manager)

        # レスポンスを文字列に変換（JSON serializable化）
        response_text = str(response) if response else ""

        return {"statusCode": 200, "body": {"response": response_text}}
    except Exception as e:
        # エラーのコンテキスト情報をログに出力
        logger.error("Error running agent: %s", e, exc_info=True)

        # エラーの種類に応じたログ出力
        if "bucket" in str(e).lower() or "key" in str(e).lower():
            logger.error("S3 parameter validation failed: %s", e)

        return {"statusCode": 500, "body": {"error": str(e)}}
