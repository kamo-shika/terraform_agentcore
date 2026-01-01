from strands import Agent

def create_agent():
    # Simple agent configuration
    agent = Agent(
        name="SimpleAgent",
        model="anthropic.claude-3-sonnet-20240229-v1:0", # Example model ID
        system_prompt="You are a helpful assistant. Answer concisely.",
        tools=[]
    )
    return agent
