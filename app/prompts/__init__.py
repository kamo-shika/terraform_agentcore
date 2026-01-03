"""
Prompt management module for external prompt files.
"""

from .loader import get_prompt_path, list_prompts, load_prompt

__all__ = ["load_prompt", "list_prompts", "get_prompt_path"]
