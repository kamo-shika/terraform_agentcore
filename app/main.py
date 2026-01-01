import os
import logging
from agent import create_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(event, context):
    """
    Entry point for Bedrock AgentCore Runtime.
    """
    logger.info("Received event: %s", event)
    
    try:
        agent = create_agent()
        
        # Extract input from the event (structure depends on AgentCore invocation)
        user_input = event.get("input", {}).get("text", "Hello")
        
        # Run the agent
        response = agent.run(user_input)
        
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
    # Local testing
    print(handler({"input": {"text": "Hello, Agent!"}}, {}))
