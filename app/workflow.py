"""
シングルエージェント方式によるワークフロー管理。

このモジュールは、S3ファイルの要約とユーザープロファイル生成のための
ワークフローを定義・実行する機能を提供する。

SessionManager統合により、会話履歴は自動的に永続化され、
Memory Strategyによる自動処理（嗜好抽出・要約等）が有効になる。

シングルエージェント方式では、同一のエージェントインスタンスを使って
3回呼び出しを行い、コンテキストを保持しながら処理を進める。
"""

import logging

from strands import Agent
from strands_tools import use_aws

from .config import MODEL_ID
from .memory import create_memory
from .prompts import load_prompt
from .tools import (
    get_past_preferences,
    retrieve_memory_tool,
)

logger = logging.getLogger(__name__)


def run_workflow(
    s3_info: dict[str, str], actor_id: str, session_id: str, memory_id: str
) -> str:
    """
    S3ファイル要約ワークフローをシングルエージェント方式で実行する。

    3ステップのワークフロー:
    - Step 1: S3ファイル読み取り・要約
    - Step 2: パターン分析
    - Step 3: プロファイル生成

    同一エージェントインスタンスを使用することで、
    コンテキストが各ステップ間で保持される。

    Args:
        s3_info: S3バケットとキー情報を含む辞書
            - bucket: S3バケット名
            - key: S3オブジェクトキー
        actor_id: アクターID（ユーザーID）
        session_id: セッションID
        memory_id: AgentCore MemoryのID

    Returns:
        ワークフロー実行結果（プロファイル）

    Raises:
        ValueError: s3_info、bucket、またはkeyが空の場合
    """
    # s3_infoのバリデーション
    if s3_info is None:
        raise ValueError("s3_info must not be None")

    # bucketのバリデーション
    bucket = s3_info.get("bucket", "")
    if not bucket or not bucket.strip():
        raise ValueError("bucket must not be empty")

    # keyのバリデーション
    key = s3_info.get("key", "")
    if not key or not key.strip():
        raise ValueError("key must not be empty")

    # 過去の嗜好を取得（精度向上のため）
    past_preferences = get_past_preferences(memory_id=memory_id, actor_id=actor_id)
    logger.info(f"Retrieved past preferences: {len(past_preferences)} chars")

    # SessionManagerを作成（会話履歴の自動永続化 + LTMからの情報自動取得）
    session_manager = create_memory(memory_id, session_id, actor_id)

    # プロンプトファイルを読み込む
    system_prompt = load_prompt("workflow/system")
    step1_prompt = load_prompt("workflow/step1")
    step2_prompt = load_prompt("workflow/step2")
    step3_prompt = load_prompt("workflow/step3")

    # ワークフロー用エージェントを作成（SessionManagerにより会話は自動永続化）
    agent = Agent(
        model=MODEL_ID,
        system_prompt=system_prompt,
        tools=[use_aws, retrieve_memory_tool],
        session_manager=session_manager,
    )

    logger.info("Starting single-agent workflow execution")

    # Step 1: S3ファイル読み取り・要約
    logger.info("Step 1: Reading and summarizing S3 file")
    step1_input = step1_prompt.format(bucket=bucket, key=key)
    agent(step1_input)

    # Step 2: パターン分析
    logger.info("Step 2: Analyzing patterns")
    step2_input = step2_prompt.format(
        memory_id=memory_id,
        actor_id=actor_id,
    )
    agent(step2_input)

    # Step 3: プロファイル生成
    logger.info("Step 3: Generating profile")
    step3_input = step3_prompt.format(past_preferences=past_preferences)
    result = agent(step3_input)

    logger.info("Workflow execution completed")
    return str(result) if result else "Workflow completed"
