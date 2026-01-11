"""
シングルエージェント方式によるワークフロー管理。

このモジュールは、CS通話ログからライフイベントを検出し、
レコメンドを生成するワークフローを定義・実行する機能を提供する。

SessionManager統合により、会話履歴は自動的に永続化され、
Memory Strategyによる自動処理（嗜好抽出・要約等）が有効になる。

シングルエージェント方式では、同一のエージェントインスタンスを使って
3回呼び出しを行い、コンテキストを保持しながら処理を進める。
"""

import logging
from datetime import date

import boto3
from strands import Agent
from strands_tools import use_aws

from .config import MODEL_ID, REGION
from .memory import create_memory
from .prompts import load_prompt
from .tools import (
    get_past_preferences,
    retrieve_memory_tool,
)

logger = logging.getLogger(__name__)


def _read_s3_file(bucket: str, key: str) -> str:
    """
    S3からファイルを読み取る。

    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー

    Returns:
        ファイルの内容（UTF-8テキスト）

    Raises:
        botocore.exceptions.ClientError: S3アクセスエラー
    """
    s3_client = boto3.client("s3", region_name=REGION)
    response = s3_client.get_object(Bucket=bucket, Key=key)
    content = response["Body"].read().decode("utf-8")
    logger.info(f"Read S3 file: s3://{bucket}/{key} ({len(content)} chars)")
    return content


def run_workflow(
    s3_info: dict[str, str], actor_id: str, session_id: str, memory_id: str
) -> str:
    """
    CS通話ログ分析ワークフローをシングルエージェント方式で実行する。

    3ステップのワークフロー:
    - Step 1: 通話ログからライフイベントを検出
    - Step 2: 過去の通話要約と照合・パターン分析
    - Step 3: 顧客向けレコメンド生成

    同一エージェントインスタンスを使用することで、
    コンテキストが各ステップ間で保持される。

    Args:
        s3_info: S3バケットとキー情報を含む辞書
            - bucket: S3バケット名（通話ログが保存されている）
            - key: S3オブジェクトキー
        actor_id: アクターID（顧客ID）
        session_id: セッションID
        memory_id: AgentCore MemoryのID

    Returns:
        ワークフロー実行結果（レコメンドJSON）

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

    # S3から通話ログを読み取る
    call_log = _read_s3_file(bucket, key)
    call_date = date.today().isoformat()

    # 過去の検出履歴を取得（パターン分析用）
    past_summaries = get_past_preferences(memory_id=memory_id, actor_id=actor_id)
    logger.info(f"Retrieved past summaries: {len(past_summaries)} chars")

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

    # Step 1: 通話ログからライフイベント検出
    logger.info("Step 1: Detecting life events from call log")
    step1_input = step1_prompt.format(
        call_log=call_log,
        customer_id=actor_id,
        call_date=call_date,
    )
    step1_result = agent(step1_input)

    # Step 2: 過去の履歴と照合・パターン分析
    logger.info("Step 2: Analyzing patterns with history")
    step2_input = step2_prompt.format(
        step1_result=str(step1_result),
        past_summaries=past_summaries if past_summaries else "過去の検出履歴はありません",
    )
    step2_result = agent(step2_input)

    # Step 3: レコメンド生成
    logger.info("Step 3: Generating recommendations")
    step3_input = step3_prompt.format(
        step2_result=str(step2_result),
        customer_id=actor_id,
        call_date=call_date,
    )
    result = agent(step3_input)

    logger.info("Workflow execution completed")
    return str(result) if result else "Workflow completed"
