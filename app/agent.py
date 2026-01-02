from strands import Agent
from strands_tools import use_aws

def create_agent(session_manager=None, system_prompt=None):
    """
    Create an agent with S3 file reading capabilities.

    Args:
        session_manager: Optional AgentCore Memory session manager
        system_prompt: Custom system prompt (default: generic helpful assistant)

    Returns:
        Configured Agent instance
    """
    default_prompt = "You are a helpful assistant. Answer concisely."

    agent = Agent(
        name="S3FileProcessingAgent",
        model="jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
        system_prompt=system_prompt or default_prompt,
        tools=[use_aws],  # Add AWS tools for S3 operations
        session_manager=session_manager
    )
    return agent
