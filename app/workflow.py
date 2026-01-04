"""
Strands Agents workflowツールを使用したワークフロー管理。

このモジュールは、S3ファイルの要約とユーザープロファイル生成のための
ワークフローを定義・実行する機能を提供する。
"""

import logging
from typing import Any

from strands import Agent
from strands_tools import use_aws, workflow

from .config import MODEL_ID
from .prompts import load_prompt
from .tools import retrieve_memory_tool, save_memory_tool

logger = logging.getLogger(__name__)


def create_s3_summarize_workflow() -> dict[str, Any]:
    """
    S3ファイル要約→パターン分析→プロファイル生成のワークフロー定義を作成する。

    Returns:
        ワークフロー定義の辞書。以下のキーを含む:
        - workflow_id: ワークフローID ("s3_summarize")
        - tasks: タスク定義のリスト
    """
    # プロンプトファイルから読み込む（見つからない場合はデフォルト値を使用）
    try:
        summarize_prompt = load_prompt("workflow/summarize")
    except FileNotFoundError:
        logger.warning("workflow/summarize.md not found, using default prompt")
        summarize_prompt = (
            "あなたはS3ファイルを読み取り、内容を要約するエージェントです。\n"
            "use_awsツールを使用してS3ファイルの内容を取得し、\n"
            "その内容を要約してsave_memory_toolで保存してください。"
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
            "分析結果に基づいてユーザーの特性や傾向をまとめ、\n"
            "save_memory_toolを使用してプロファイルを保存してください。"
        )

    return {
        "workflow_id": "s3_summarize",
        "tasks": [
            {
                "task_id": "summarize_s3_file",
                "description": "S3ファイルを読み取り、内容を要約してメモリに保存",
                "system_prompt": summarize_prompt,
                "tools": ["use_aws", "save_memory_tool"],
                "dependencies": [],
            },
            {
                "task_id": "analyze_patterns",
                "description": "過去の要約と比較してパターンを分析",
                "system_prompt": analyze_prompt,
                "tools": ["retrieve_memory_tool"],
                "dependencies": ["summarize_s3_file"],
            },
            {
                "task_id": "generate_profile",
                "description": "ユーザー特性をまとめてプロファイルを生成し保存",
                "system_prompt": profile_prompt,
                "tools": ["save_memory_tool"],
                "dependencies": ["analyze_patterns"],
            },
        ],
    }


def run_workflow(s3_info: dict[str, str], actor_id: str, memory_id: str) -> str:
    """
    S3ファイル要約ワークフローを実行する。

    Args:
        s3_info: S3バケットとキー情報を含む辞書
            - bucket: S3バケット名
            - key: S3オブジェクトキー
        actor_id: アクターID（ユーザーID）
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

    # ワークフロー定義を取得
    workflow_def = create_s3_summarize_workflow()

    # ワークフロー用エージェントを作成
    # workflowツールと、各タスクで使用するツールを含める
    agent = Agent(
        model=MODEL_ID,
        system_prompt="あなたはワークフローを管理するエージェントです。",
        tools=[workflow, use_aws, save_memory_tool, retrieve_memory_tool],
    )

    logger.info(f"Creating workflow: {workflow_def['workflow_id']}")

    # ワークフローを作成・実行
    # agent経由でworkflowツールを使用
    prompt = f"""
以下のワークフローを実行してください。

S3ファイル情報:
- バケット: {bucket}
- キー: {key}

メモリ情報:
- Memory ID: {memory_id}
- Actor ID: {actor_id}

ワークフロー手順:
1. まず、use_awsツールでS3からファイルを読み取り、内容を要約してください
2. 次に、save_memory_toolで要約をメモリに保存してください（namespace: /file-summaries/{actor_id}）
3. retrieve_memory_toolで過去の要約を取得し、パターンを分析してください
4. 最後に、ユーザープロファイルを生成し、save_memory_toolで保存してください（namespace: /actor-state/{actor_id}）

各ステップの結果を報告してください。
"""

    response = agent(prompt)
    result = str(response) if response else "Workflow completed"

    logger.info("Workflow execution completed")
    return result
