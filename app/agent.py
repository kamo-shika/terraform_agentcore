from strands_agents import Agent
from strands_agents_tools import Tool

def create_agent():
    # Simple agent configuration
    agent = Agent(
        name="SimpleAgent",
        model="anthropic.claude-3-sonnet-20240229-v1:0", # Example model ID
        instructions="You are a helpful assistant. Answer concisely.",
        tools=[]
    )
    return agent
