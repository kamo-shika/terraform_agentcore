from strands import Agent

def create_agent(session_manager=None):
    # Simple agent configuration
    agent = Agent(
        name="SimpleAgent",
        model="jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
        system_prompt="You are a helpful assistant. Answer concisely.",
        tools=[],
        session_manager=session_manager
    )
    return agent
