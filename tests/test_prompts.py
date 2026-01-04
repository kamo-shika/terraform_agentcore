"""
app/prompts/loader.py のテスト。

プロンプト読み込みユーティリティをテストする。
"""

import pytest


class TestLoadPrompt:
    """
    load_prompt関数のテスト。
    """

    def test_load_prompt_returns_string(self, tmp_path, monkeypatch):
        """
        load_promptが文字列を返すことを確認する。
        """
        from app.prompts import loader

        # 一時的なプロンプトファイルを作成
        test_prompt_content = "This is a test prompt."
        test_prompt_path = tmp_path / "test_prompt.md"
        test_prompt_path.write_text(test_prompt_content, encoding="utf-8")

        # PROMPTS_DIRを一時ディレクトリに変更
        monkeypatch.setattr(loader, "PROMPTS_DIR", tmp_path)

        from app.prompts.loader import load_prompt

        result = load_prompt("test_prompt")
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
