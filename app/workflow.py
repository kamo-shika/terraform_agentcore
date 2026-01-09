"""
Strands Agents workflowツールを使用したワークフロー管理。

このモジュールは、S3ファイルの要約とユーザープロファイル生成のための
ワークフローを定義・実行する機能を提供する。

Workflow Tool APIを使用したマルチエージェント実行により、
各タスクは専用のサブエージェントによって実行される。

SessionManager統合により、会話履歴は自動的に永続化され、
Memory Strategyによる自動処理（嗜好抽出・要約等）が有効になる。
"""

import logging
import os
from typing import Any

from strands import Agent
from strands_tools import use_aws, workflow

from .config import MODEL_ID
from .memory import create_memory
from .prompts import load_prompt
from .tools import (
    get_past_preferences,
    retrieve_memory_tool,
)

logger = logging.getLogger(__name__)


def create_s3_summarize_workflow(
    bucket: str = "",
    key: str = "",
    memory_id: str = "",
    actor_id: str = "",
    past_preferences: str = "",
) -> dict[str, Any]:
    """
    S3ファイル要約→パターン分析→プロファイル生成のワークフロー定義を作成する。

    Args:
        bucket: S3バケット名
        key: S3オブジェクトキー
        memory_id: AgentCore MemoryのID
        actor_id: アクターID（ユーザーID）
        past_preferences: 過去の嗜好データ

    Returns:
        ワークフロー定義の辞書。以下のキーを含む:
        - workflow_id: ワークフローID ("s3_summarize")
        - tasks: タスク定義のリスト
    """
    # プロンプトファイルから読み込む（見つからない場合はデフォルト値を使用）
    # SessionManager統合により、保存は自動的に行われる
    try:
        summarize_prompt = load_prompt("workflow/summarize")
    except FileNotFoundError:
        logger.warning("workflow/summarize.md not found, using default prompt")
        summarize_prompt = (
            "あなたはS3ファイルを読み取り、内容を要約するエージェントです。\n"
            "use_awsツールを使用してS3ファイルの内容を取得し、\n"
            "その内容を要約してください。会話履歴は自動的に保存されます。"
        )

    try:
        analyze_prompt = load_prompt("workflow/analyze")
    except FileNotFoundError:
        logger.warning("workflow/analyze.md not found, using default prompt")
        analyze_prompt = (
            "あなたは過去の要約データを分析するエージェントです。\n"
            "retrieve_memory_toolを使用して過去の要約を取得し、\n"
            "現在の要約と比較してパターンや傾向を分析してください。"
        )

    try:
        profile_prompt = load_prompt("workflow/profile")
    except FileNotFoundError:
        logger.warning("workflow/profile.md not found, using default prompt")
        profile_prompt = (
            "あなたはユーザープロファイルを生成するエージェントです。\n"
            "分析結果に基づいてユーザーの特性や傾向をまとめてください。\n"
            "会話履歴は自動的に保存され、Memory Strategyにより嗜好が抽出されます。"
        )

    # 嗜好情報のセクションを構築
    if past_preferences:
        preferences_section = f"\n\n過去の嗜好:\n{past_preferences}"
    else:
        preferences_section = ""

    # 注: save_memory_toolは不要（SessionManagerが会話履歴を自動永続化）
    return {
        "workflow_id": "s3_summarize",
        "tasks": [
            {
                "task_id": "summarize_s3_file",
                "description": f"S3ファイルを読み取り、内容を要約\nバケット: {bucket}\nキー: {key}",
                "system_prompt": summarize_prompt,
                "tools": ["use_aws"],
                "dependencies": [],
            },
            {
                "task_id": "analyze_patterns",
                "description": f"過去の要約と比較してパターンを分析\nMemory ID: {memory_id}\nActor ID: {actor_id}",
                "system_prompt": analyze_prompt,
                "tools": ["retrieve_memory_tool"],
                "dependencies": ["summarize_s3_file"],
            },
            {
                "task_id": "generate_profile",
                "description": f"ユーザー特性をまとめてプロファイルを生成{preferences_section}",
                "system_prompt": profile_prompt,
                "tools": [],
                "dependencies": ["analyze_patterns"],
            },
        ],
    }


def run_workflow(s3_info: dict[str, str], actor_id: str, session_id: str, memory_id: str) -> str:
    """
    S3ファイル要約ワークフローを実行する。

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

    # ワークフロー用エージェントを作成（SessionManagerにより会話は自動永続化）
    # workflowツールによりマルチエージェント実行が可能
    agent = Agent(
        model=MODEL_ID,
        system_prompt="あなたはワークフローを管理するエージェントです。",
        tools=[use_aws, retrieve_memory_tool, get_past_preferences, workflow],
        session_manager=session_manager,  # SessionManagerを渡す
    )

    # パラメータを渡してワークフロー定義を作成
    workflow_def = create_s3_summarize_workflow(
        bucket=bucket,
        key=key,
        memory_id=memory_id,
        actor_id=actor_id,
        past_preferences=past_preferences,
    )

    logger.info(f"Creating workflow: {workflow_def['workflow_id']}")

    # Workflow Tool APIを使用してワークフローを作成・実行
    # 各タスクは専用のサブエージェントによって実行される
    agent.tool.workflow(
        action="create",
        workflow_id=workflow_def["workflow_id"],
        tasks=workflow_def["tasks"],
    )

    # ワークフローを開始
    result = agent.tool.workflow(
        action="start",
        workflow_id=workflow_def["workflow_id"],
    )

    logger.info("Workflow execution completed")
    return str(result) if result else "Workflow completed"
