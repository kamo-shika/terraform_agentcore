import os
import logging
from agent import create_agent
from memory import create_memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """
    Entry point for Bedrock AgentCore Runtime.
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

        # Agentの作成
        agent = create_agent(session_manager=session_manager)

        # Extract input from the event (structure depends on AgentCore invocation)
        user_input = event.get("input", {}).get("text", "Hello")

        # Run the agent
        response = agent(user_input)

        return {
            "statusCode": 200,
            "body": {
                "response": response
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

if __name__ == "__main__":
    # Local testing with interactive mode
    print("=== AgentCore Local Testing Mode ===")
    print("Memory機能が有効な場合、同じSESSION_IDで会話履歴が保持されます")
    print("終了するには 'quit' または 'exit' と入力してください\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("終了します...")
                break

            if not user_input.strip():
                continue

            result = handler({"input": {"text": user_input}}, {})
            response = result.get('body', {}).get('response', 'No response')
            print(f"\nAgent: {response}\n")

        except KeyboardInterrupt:
            print("\n\n終了します...")
            break
        except Exception as e:
            print(f"\nエラー: {e}\n")
            import traceback
            traceback.print_exc()
