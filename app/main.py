import os
import logging
from .agent import create_agent
from .memory import create_memory
from .prompts import load_prompt

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """
    Entry point for Bedrock AgentCore Runtime.
    Handles both regular invocations and S3 file processing.
    """
    logger.info("Received event: %s", event)

    try:
        # Memory設定の読み取り（環境変数から）
        memory_id = os.getenv("AGENTCORE_MEMORY_ID")
        session_id = event.get("sessionId") or os.getenv("SESSION_ID", "local-session-001")
        actor_id = event.get("actorId") or os.getenv("ACTOR_ID", "local-user")

        # session_managerの作成（memory_idがある場合のみ）
        session_manager = None
        if memory_id:
            try:
                session_manager = create_memory(memory_id, session_id, actor_id)
                logger.info(f"Memory enabled: memory_id={memory_id}, session_id={session_id}, actor_id={actor_id}")
            except Exception as e:
                logger.warning(f"Failed to initialize memory: {e}")
        else:
            logger.info("Memory disabled (no AGENTCORE_MEMORY_ID)")

        # Check if this is an S3 file processing request
        s3_info = event.get("s3_info")
        system_prompt = None
        user_input = event.get("input", {}).get("text", "Hello")

        if s3_info:
            # S3 file processing mode
            bucket = s3_info.get("bucket")
            key = s3_info.get("key")
            logger.info(f"S3 file processing request: s3://{bucket}/{key}")

            # Load the summarization prompt with S3 context
            try:
                system_prompt = load_prompt(
                    "summarize",
                    bucket=bucket,
                    key=key,
                    user_id=actor_id
                )
                logger.info("Loaded summarization prompt")
            except FileNotFoundError:
                logger.warning("summarize.txt prompt not found, using default")
            except Exception as e:
                logger.warning(f"Failed to load prompt: {e}")

            # Create specific instruction for S3 file processing
            user_input = (
                f"S3バケット '{bucket}' のファイル '{key}' を読み取り、内容を要約してください。\n"
                f"use_awsツールを使用して以下のパラメータでファイルを取得してください:\n"
                f"- service_name: 's3'\n"
                f"- operation_name: 'get_object'\n"
                f"- parameters: {{'Bucket': '{bucket}', 'Key': '{key}'}}\n"
                f"- region: 'ap-northeast-1'"
            )

        # Agentの作成
        agent = create_agent(session_manager=session_manager, system_prompt=system_prompt)

        # Run the agent
        response = agent(user_input)

        # AgentResultオブジェクトを文字列に変換（JSON serializable化）
        response_text = str(response) if response else ""

        return {
            "statusCode": 200,
            "body": {
                "response": response_text
            }
        }
    except Exception as e:
        logger.error("Error running agent: %s", e)
        return {
            "statusCode": 500,
            "body": {
                "error": str(e)
            }
        }
