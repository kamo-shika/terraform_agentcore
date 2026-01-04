"""
外部プロンプト管理のためのプロンプト読み込みユーティリティ。

このモジュールは、外部テキストファイルからプロンプトを読み込む関数を提供し、
コードを変更せずにシステムプロンプトを簡単に修正できるようにします。
"""

from pathlib import Path

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """
    プロンプトファイルを読み込み、変数を置換します。

    Args:
        name: プロンプトファイル名（拡張子なし、または"workflow/summarize"のようなパス）
        **kwargs: {変数名}形式でプロンプト内に置換する変数

    Returns:
        変数が置換されたプロンプトテキスト

    Raises:
        FileNotFoundError: プロンプトファイルが存在しない場合

    Example:
        >>> prompt = load_prompt("summarize", bucket="my-bucket", key="file.txt")
        >>> prompt = load_prompt("workflow/summarize")
    """
    # .md と .txt の両方をサポート
    prompt_path_md = PROMPTS_DIR / f"{name}.md"
    prompt_path_txt = PROMPTS_DIR / f"{name}.txt"

    # 存在するファイルを探す
    if prompt_path_md.exists():
        prompt_path = prompt_path_md
    elif prompt_path_txt.exists():
        prompt_path = prompt_path_txt
    else:
        raise FileNotFoundError(f"Prompt file not found: {prompt_path_md} or {prompt_path_txt}")

    with open(prompt_path, encoding="utf-8") as f:
        template = f.read()

    # 変数が提供されている場合は置換
    if kwargs:
        template = template.format(**kwargs)

    return template


