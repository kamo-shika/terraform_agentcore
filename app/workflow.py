"""
Strands Agents workflowツールを使用したワークフロー管理。

このモジュールは、S3ファイルの要約とユーザープロファイル生成のための
ワークフローを定義・実行する機能を提供する。

SessionManager統合により、会話履歴は自動的に永続化され、
Memory Strategyによる自動処理（嗜好抽出・要約等）が有効になる。
"""

import logging
from typing import Any

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


def create_s3_summarize_workflow() -> dict[str, Any]:
    """
    S3ファイル要約→パターン分析→プロファイル生成のワークフロー定義を作成する。

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

    # SessionManager統合後、save_memory_toolは不要
    # 保存はSessionManagerが自動的に行い、Memory Strategyで嗜好抽出される
    return {
        "workflow_id": "s3_summarize",
        "tasks": [
            {
                "task_id": "summarize_s3_file",
                "description": "S3ファイルを読み取り、内容を要約",
                "system_prompt": summarize_prompt,
                "tools": ["use_aws"],  # SessionManagerが自動保存
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
                "description": "ユーザー特性をまとめてプロファイルを生成",
                "system_prompt": profile_prompt,
                "tools": [],  # SessionManagerが自動保存
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

    # ワークフロー定義を取得
    workflow_def = create_s3_summarize_workflow()

    # 過去の嗜好を取得（精度向上のため）
    past_preferences = get_past_preferences(memory_id=memory_id, actor_id=actor_id)
    logger.info(f"Retrieved past preferences: {len(past_preferences)} chars")

    # 嗜好セクションを構築
    if past_preferences:
        preferences_section = f"""
## ユーザーの過去の嗜好・傾向
以下は過去の分析から抽出されたユーザーの嗜好データです。
分析時にこれらの傾向を考慮してください。

{past_preferences}
"""
    else:
        preferences_section = """
## ユーザーの過去の嗜好・傾向
過去の嗜好データはありません（初回分析）。
"""

    # SessionManagerを作成（会話履歴の自動永続化 + LTMからの情報自動取得）
    session_manager = create_memory(memory_id, session_id, actor_id)

    # ワークフロー用エージェントを作成
    # SessionManager統合により、保存系ツールは不要
    # 会話履歴は自動的に永続化され、Memory Strategyにより嗜好抽出される
    agent = Agent(
        model=MODEL_ID,
        system_prompt="あなたはワークフローを管理するエージェントです。",
        tools=[use_aws, retrieve_memory_tool, get_past_preferences],
        session_manager=session_manager,  # SessionManagerを渡す
    )

    logger.info(f"Creating workflow: {workflow_def['workflow_id']}")

    # ワークフローを作成・実行
    # SessionManagerにより会話は自動保存され、Memory Strategyで嗜好抽出
    prompt = f"""
以下のワークフローを実行してください。

S3ファイル情報:
- バケット: {bucket}
- キー: {key}

メモリ情報:
- Memory ID: {memory_id}
- Session ID: {session_id}
- Actor ID: {actor_id}

{preferences_section}

ワークフロー手順:
1. まず、use_awsツールでS3からファイルを読み取り、内容を要約してください
2. retrieve_memory_toolで過去の要約を取得し、パターンを分析してください
3. 上記の「ユーザーの過去の嗜好・傾向」を考慮して、ユーザープロファイルを生成してください

**重要**: 分析時は過去の嗜好を考慮し、より個別化された分析を行ってください。
各ステップの結果を報告してください。

注意: 会話履歴は自動的にメモリに保存され、Memory Strategyにより嗜好抽出が行われます。
手動でsave_memory_toolを呼び出す必要はありません。
"""

    response = agent(prompt)
    result = str(response) if response else "Workflow completed"

    logger.info("Workflow execution completed")
    return result
