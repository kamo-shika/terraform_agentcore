from strands import Agent
from strands_tools import use_aws
from .config import MODEL_ID


def create_agent(session_manager=None, system_prompt=None):
    """
    S3ファイル読み取り機能を持つエージェントを作成します。

    Args:
        session_manager: オプショナルなAgentCore Memoryセッションマネージャー
        system_prompt: カスタムシステムプロンプト（デフォルト：汎用的なアシスタント）

    Returns:
        設定済みのAgentインスタンス
    """
    default_prompt = "You are a helpful assistant. Answer concisely."

    agent = Agent(
        name="S3FileProcessingAgent",
        model=MODEL_ID,
        system_prompt=system_prompt or default_prompt,
        tools=[use_aws],  # S3操作用のAWSツールを追加
        session_manager=session_manager,
    )
    return agent
