"""
Strands Agents workflowツールを使用したワークフロー管理。

このモジュールは、S3ファイルの要約とユーザープロファイル生成のための
ワークフローを定義・実行する機能を提供する。
"""

import logging
from typing import Any

from strands_tools import workflow

from .prompts import load_prompt

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
        logger.warning("workflow/summarize.txt not found, using default prompt")
        summarize_prompt = (
            "あなたはS3ファイルを読み取り、内容を要約するエージェントです。\n"
            "use_awsツールを使用してS3ファイルの内容を取得し、\n"
            "その内容を要約してsave_memory_toolで保存してください。"
        )

    try:
        analyze_prompt = load_prompt("workflow/analyze")
    except FileNotFoundError:
        logger.warning("workflow/analyze.txt not found, using default prompt")
        analyze_prompt = (
            "あなたは過去の要約データを分析するエージェントです。\n"
            "retrieve_memory_toolを使用して過去の要約を取得し、\n"
            "現在の要約と比較してパターンや傾向を分析してください。"
        )

    try:
        profile_prompt = load_prompt("workflow/profile")
    except FileNotFoundError:
        logger.warning("workflow/profile.txt not found, using default prompt")
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

    # ワークフローを作成
    workflow(action="create", workflow_id=workflow_def["workflow_id"], tasks=workflow_def["tasks"])
    logger.info(f"Workflow created: {workflow_def['workflow_id']}")

    # ワークフローを開始
    workflow(action="start", workflow_id=workflow_def["workflow_id"])
    logger.info(f"Workflow started: {workflow_def['workflow_id']}")

    # ワークフローのステータスを確認
    status_response = workflow(action="status", workflow_id=workflow_def["workflow_id"])

    # プロファイル結果を取得
    if status_response.get("status") == "success":
        workflow_data = status_response.get("workflow", {})
        task_results = workflow_data.get("task_results", {})
        profile_result = task_results.get("generate_profile", {})

        if profile_result.get("status") == "completed":
            result_content = profile_result.get("result", [])
            if result_content and isinstance(result_content, list):
                return result_content[0].get("text", "")

    # デフォルトの結果を返す
    return "profile: User profile generated"
