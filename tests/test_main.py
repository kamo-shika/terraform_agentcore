"""
app/main.pyのテスト。

handler関数の動作を検証する。エージェント実行は課金が発生するためモックを使用。
"""
import pytest
from unittest.mock import patch, MagicMock


class TestHandler:
    """handler関数のテストクラス。"""

    def test_handler_with_valid_input(self, sample_event, mock_context, clean_env):
        """
        正常な入力でhandlerが動作することを確認。

        Args:
            sample_event: conftest.pyで定義されたフィクスチャ
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            # エージェントのモック設定
            mock_agent = MagicMock()
            mock_agent.return_value = "テスト応答です"
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(sample_event, mock_context)

            # レスポンス形式の検証
            assert result["statusCode"] == 200
            assert "body" in result
            assert "response" in result["body"]
            assert result["body"]["response"] == "テスト応答です"

            # エージェントが正しく呼び出されたか
            mock_create_agent.assert_called_once()
            mock_agent.assert_called_once_with("こんにちは")

    def test_handler_with_session_info(self, sample_event_with_session, mock_context, clean_env):
        """
        セッション情報を含むイベントでhandlerが動作することを確認。

        Args:
            sample_event_with_session: セッション情報を含むイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "セッション付き応答"
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(sample_event_with_session, mock_context)

            assert result["statusCode"] == 200
            assert result["body"]["response"] == "セッション付き応答"

    def test_handler_with_empty_input(self, empty_event, mock_context, clean_env):
        """
        入力が空の場合、デフォルト値が使用されることを確認。

        Args:
            empty_event: 空の入力を持つイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "Hello応答"
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(empty_event, mock_context)

            assert result["statusCode"] == 200
            # デフォルト値 "Hello" が使用される
            mock_agent.assert_called_once_with("Hello")

    def test_handler_with_invalid_event(self, invalid_event, mock_context, clean_env):
        """
        不正な形式のイベントでもデフォルト値で動作することを確認。

        Args:
            invalid_event: inputキーがないイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "デフォルト応答"
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(invalid_event, mock_context)

            assert result["statusCode"] == 200
            # デフォルト値 "Hello" が使用される
            mock_agent.assert_called_once_with("Hello")

    def test_handler_with_s3_event(self, sample_s3_event, mock_context, clean_env):
        """
        S3イベントでhandlerが正しく動作することを確認。

        Args:
            sample_s3_event: S3情報を含むイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "S3ファイル要約結果"
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(sample_s3_event, mock_context)

            assert result["statusCode"] == 200
            assert "S3ファイル要約結果" in result["body"]["response"]

            # S3処理用の入力が生成されているか確認
            call_args = mock_agent.call_args[0][0]
            assert "test-bucket" in call_args
            assert "test-folder/test-file.txt" in call_args

    def test_handler_error_handling(self, sample_event, mock_context, clean_env):
        """
        エージェント実行時のエラーが適切にハンドリングされることを確認。

        Args:
            sample_event: 標準イベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.side_effect = Exception("テストエラー")
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(sample_event, mock_context)

            # エラー時は500を返す
            assert result["statusCode"] == 500
            assert "body" in result
            assert "error" in result["body"]
            assert "テストエラー" in result["body"]["error"]

    def test_handler_with_none_response(self, sample_event, mock_context, clean_env):
        """
        エージェントがNoneを返した場合の処理を確認。

        Args:
            sample_event: 標準イベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = None
            mock_create_agent.return_value = mock_agent

            from app.main import handler

            result = handler(sample_event, mock_context)

            assert result["statusCode"] == 200
            # Noneの場合は空文字列になる
            assert result["body"]["response"] == ""
