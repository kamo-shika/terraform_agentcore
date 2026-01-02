"""
Prompt loading utility for external prompt management.

This module provides functions to load prompts from external text files,
making it easy to modify system prompts without changing code.
"""

import os
from pathlib import Path
from typing import Optional

PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str, **kwargs) -> str:
    """
    Load a prompt file and substitute variables.

    Args:
        name: Prompt file name (without extension)
        **kwargs: Variables to substitute in the prompt using {variable} format

    Returns:
        The prompt text with variables substituted

    Raises:
        FileNotFoundError: If the prompt file doesn't exist

    Example:
        >>> prompt = load_prompt("summarize", bucket="my-bucket", key="file.txt")
    """
    prompt_path = PROMPTS_DIR / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Substitute variables if provided
    if kwargs:
        template = template.format(**kwargs)

    return template


def list_prompts() -> list[str]:
    """
    List all available prompt names.

    Returns:
        List of prompt names (without .txt extension)
    """
    return [f.stem for f in PROMPTS_DIR.glob("*.md")]


def get_prompt_path(name: str) -> Path:
    """
    Get the full path to a prompt file.

    Args:
        name: Prompt file name (without extension)

    Returns:
        Path object for the prompt file
    """
    return PROMPTS_DIR / f"{name}.md"
