"""
外部プロンプト管理のためのプロンプト読み込みユーティリティ。

このモジュールは、外部テキストファイルからプロンプトを読み込む関数を提供し、
コードを変更せずにシステムプロンプトを簡単に修正できるようにします。
"""

import os
from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """
    プロンプトファイルを読み込み、変数を置換します。

    Args:
        name: プロンプトファイル名（拡張子なし）
        **kwargs: {変数名}形式でプロンプト内に置換する変数

    Returns:
        変数が置換されたプロンプトテキスト

    Raises:
        FileNotFoundError: プロンプトファイルが存在しない場合

    Example:
        >>> prompt = load_prompt("summarize", bucket="my-bucket", key="file.txt")
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # 変数が提供されている場合は置換
    if kwargs:
        template = template.format(**kwargs)

    return template


def list_prompts() -> list[str]:
    """
    利用可能なすべてのプロンプト名をリストします。

    Returns:
        プロンプト名のリスト（.md拡張子なし）
    """
    return [f.stem for f in PROMPTS_DIR.glob("*.md")]


def get_prompt_path(name: str) -> Path:
    """
    プロンプトファイルのフルパスを取得します。

    Args:
        name: プロンプトファイル名（拡張子なし）

    Returns:
        プロンプトファイルのPathオブジェクト
    """
    return PROMPTS_DIR / f"{name}.md"
