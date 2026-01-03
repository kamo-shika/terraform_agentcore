"""
app/prompts/loader.py のテスト。

プロンプト読み込みユーティリティをテストする。
"""

import pytest
from pathlib import Path


class TestLoadPrompt:
    """
    load_prompt関数のテスト。
    """

    def test_load_prompt_returns_string(self):
        """
        load_promptが文字列を返すことを確認する。
        """
        from app.prompts import load_prompt, list_prompts

        # 既存のプロンプトがあればテスト
        available_prompts = list_prompts()
        if available_prompts:
            result = load_prompt(available_prompts[0])
            assert isinstance(result, str)
            assert len(result) > 0

    def test_load_prompt_file_not_found(self):
        """
        存在しないプロンプトファイルでFileNotFoundErrorが発生することを確認する。
        """
        from app.prompts import load_prompt

        with pytest.raises(FileNotFoundError) as exc_info:
            load_prompt("nonexistent_prompt_file_12345")

        assert "Prompt file not found" in str(exc_info.value)

    def test_load_prompt_with_variables(self, tmp_path, monkeypatch):
        """
        変数置換が正しく動作することを確認する。
        """
        from app.prompts import loader

        # 一時的なプロンプトファイルを作成
        # 注意: load_promptの第一引数が `name` なので、変数名は別名を使用
        test_prompt_content = "Hello, {user_name}! Welcome to {place}."
        test_prompt_path = tmp_path / "test_template.md"
        test_prompt_path.write_text(test_prompt_content, encoding="utf-8")

        # PROMPTS_DIRを一時ディレクトリに変更
        monkeypatch.setattr(loader, "PROMPTS_DIR", tmp_path)

        from app.prompts.loader import load_prompt
        result = load_prompt("test_template", user_name="Alice", place="Tokyo")

        assert result == "Hello, Alice! Welcome to Tokyo."

    def test_load_prompt_without_variables(self, tmp_path, monkeypatch):
        """
        変数なしでプロンプトを読み込めることを確認する。
        """
        from app.prompts import loader

        # 一時的なプロンプトファイルを作成
        test_prompt_content = "This is a simple prompt without variables."
        test_prompt_path = tmp_path / "simple.md"
        test_prompt_path.write_text(test_prompt_content, encoding="utf-8")

        # PROMPTS_DIRを一時ディレクトリに変更
        monkeypatch.setattr(loader, "PROMPTS_DIR", tmp_path)

        from app.prompts.loader import load_prompt
        result = load_prompt("simple")

        assert result == test_prompt_content


class TestListPrompts:
    """
    list_prompts関数のテスト。
    """

    def test_list_prompts_returns_list(self):
        """
        list_promptsがリストを返すことを確認する。
        """
        from app.prompts import list_prompts

        result = list_prompts()
        assert isinstance(result, list)

    def test_list_prompts_returns_markdown_files(self, tmp_path, monkeypatch):
        """
        .mdファイルのみがリストされることを確認する。
        """
        from app.prompts import loader

        # 一時ディレクトリにテストファイルを作成
        (tmp_path / "prompt1.md").write_text("Prompt 1", encoding="utf-8")
        (tmp_path / "prompt2.md").write_text("Prompt 2", encoding="utf-8")
        (tmp_path / "not_a_prompt.txt").write_text("Not a prompt", encoding="utf-8")

        # PROMPTS_DIRを一時ディレクトリに変更
        monkeypatch.setattr(loader, "PROMPTS_DIR", tmp_path)

        from app.prompts.loader import list_prompts
        result = list_prompts()

        assert "prompt1" in result
        assert "prompt2" in result
        assert "not_a_prompt" not in result

    def test_list_prompts_empty_directory(self, tmp_path, monkeypatch):
        """
        空のディレクトリで空のリストを返すことを確認する。
        """
        from app.prompts import loader

        # 空の一時ディレクトリ
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        monkeypatch.setattr(loader, "PROMPTS_DIR", empty_dir)

        from app.prompts.loader import list_prompts
        result = list_prompts()

        assert result == []


class TestGetPromptPath:
    """
    get_prompt_path関数のテスト。
    """

    def test_get_prompt_path_returns_path(self):
        """
        get_prompt_pathがPathオブジェクトを返すことを確認する。
        """
        from app.prompts import get_prompt_path

        result = get_prompt_path("test_prompt")
        assert isinstance(result, Path)

    def test_get_prompt_path_has_md_extension(self):
        """
        返されるパスが.md拡張子を持つことを確認する。
        """
        from app.prompts import get_prompt_path

        result = get_prompt_path("my_prompt")
        assert result.suffix == ".md"

    def test_get_prompt_path_has_correct_name(self):
        """
        返されるパスが正しいファイル名を持つことを確認する。
        """
        from app.prompts import get_prompt_path

        result = get_prompt_path("system_prompt")
        assert result.stem == "system_prompt"
