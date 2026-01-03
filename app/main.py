import logging
from typing import Optional
from .agent import create_agent
from .memory import create_memory
from .prompts import load_prompt
from .config import get_memory_id, get_session_id, get_actor_id, get_input_text, REGION

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_event(event: dict) -> dict:
    """
    イベントから必要な情報を抽出する。

    Args:
        event: AgentCoreから渡されるイベント辞書

    Returns:
        dict: 以下のキーを含む辞書
            - session_id: セッションID
            - actor_id: アクターID
            - user_input: ユーザー入力テキスト
            - s3_info: S3情報（存在する場合）またはNone
    """
    return {
        "session_id": get_session_id(event),
        "actor_id": get_actor_id(event),
        "user_input": get_input_text(event),
        "s3_info": event.get("s3_info")
    }


def initialize_memory(memory_id: str, session_id: str, actor_id: str) -> Optional[object]:
    """
    メモリを初期化する。

    Args:
        memory_id: メモリID（Noneまたは空文字列の場合はNoneを返す）
        session_id: セッションID
        actor_id: アクターID

    Returns:
        SessionManagerオブジェクト、またはNone（メモリIDがない場合やエラー時）
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
        S3ファイル処理用の命令文字列
    """
    return (
        f"S3バケット '{bucket}' のファイル '{key}' を読み取り、内容を要約してください。\n"
        f"use_awsツールを使用して以下のパラメータでファイルを取得してください:\n"
        f"- service_name: 's3'\n"
        f"- operation_name: 'get_object'\n"
        f"- parameters: {{'Bucket': '{bucket}', 'Key': '{key}'}}\n"
        f"- region: '{REGION}'"
    )


def run_agent(user_input: str, session_manager=None, system_prompt=None) -> str:
    """
    エージェントを実行する。

    Args:
        user_input: ユーザー入力テキスト
        session_manager: セッションマネージャー（オプション）
        system_prompt: システムプロンプト（オプション）

    Returns:
        エージェントの応答文字列（Noneの場合は空文字列ではなくNoneを返す）
    """
    agent = create_agent(session_manager=session_manager, system_prompt=system_prompt)
    response = agent(user_input)
    return response


def handler(event, context):
    """
    Bedrock AgentCore Runtimeのエントリーポイント。

    通常の呼び出しとS3ファイル処理の両方に対応する。

    Args:
        event: AgentCoreから渡されるイベント辞書
        context: 実行コンテキスト

    Returns:
        dict: ステータスコードとレスポンスボディを含む辞書
    """
    logger.info("Received event: %s", event)

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

        # S3ファイル処理モード
        system_prompt = None
        if s3_info:
            bucket = s3_info.get("bucket")
            key = s3_info.get("key")
            logger.info(f"S3 file processing request: s3://{bucket}/{key}")

            # 要約プロンプトの読み込み
            try:
                system_prompt = load_prompt("summarize", bucket=bucket, key=key, user_id=actor_id)
                logger.info("Loaded summarization prompt")
            except FileNotFoundError:
                logger.warning("summarize.txt prompt not found, using default")
            except Exception as e:
                logger.warning(f"Failed to load prompt: {e}")

            # S3用の命令文字列を生成
            user_input = build_s3_instruction(bucket, key)

        # エージェント実行
        response = run_agent(user_input, session_manager, system_prompt)

        # レスポンスを文字列に変換（JSON serializable化）
        response_text = str(response) if response else ""

        return {"statusCode": 200, "body": {"response": response_text}}
    except Exception as e:
        logger.error("Error running agent: %s", e)
        return {"statusCode": 500, "body": {"error": str(e)}}
