from strands import Agent

def create_agent():
    # Simple agent configuration
    agent = Agent(
        name="SimpleAgent",
        model="jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
        system_prompt="You are a helpful assistant. Answer concisely.",
        tools=[]
    )
    return agent
