"""
app/main.pyのテスト。

handler関数の動作を検証する。エージェント実行は課金が発生するためモックを使用。
"""
import pytest
from unittest.mock import patch, MagicMock, ANY


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


class TestParseEvent:
    """parse_event関数のテストクラス。"""

    def test_parse_event_with_basic_input(self, sample_event):
        """
        基本的な入力のイベントを正しく解析することを確認。

        Args:
            sample_event: 標準的なイベント
        """
        from app.main import parse_event

        result = parse_event(sample_event)

        # 返却値の構造を確認
        assert "session_id" in result
        assert "actor_id" in result
        assert "user_input" in result
        assert "s3_info" in result

        # デフォルト値の確認
        assert result["session_id"] is not None
        assert result["actor_id"] is not None
        assert result["user_input"] == "こんにちは"
        assert result["s3_info"] is None

    def test_parse_event_with_session_info(self, sample_event_with_session):
        """
        セッション情報を含むイベントを正しく解析することを確認。

        Args:
            sample_event_with_session: セッション情報付きイベント
        """
        from app.main import parse_event

        result = parse_event(sample_event_with_session)

        assert result["session_id"] == "test-session-001"
        assert result["actor_id"] == "test-user-001"
        assert result["user_input"] == "テストメッセージです"
        assert result["s3_info"] is None

    def test_parse_event_with_s3_info(self, sample_s3_event):
        """
        S3情報を含むイベントを正しく解析することを確認。

        Args:
            sample_s3_event: S3情報付きイベント
        """
        from app.main import parse_event

        result = parse_event(sample_s3_event)

        assert result["s3_info"] is not None
        assert result["s3_info"]["bucket"] == "test-bucket"
        assert result["s3_info"]["key"] == "test-folder/test-file.txt"

    def test_parse_event_with_empty_input(self, empty_event):
        """
        空の入力のイベントでデフォルト値が使用されることを確認。

        Args:
            empty_event: 空の入力を持つイベント
        """
        from app.main import parse_event

        result = parse_event(empty_event)

        # デフォルト値 "Hello" が使用される
        assert result["user_input"] == "Hello"

    def test_parse_event_with_invalid_event(self, invalid_event):
        """
        不正な形式のイベントでもデフォルト値で動作することを確認。

        Args:
            invalid_event: inputキーがないイベント
        """
        from app.main import parse_event

        result = parse_event(invalid_event)

        # デフォルト値が使用される
        assert result["user_input"] == "Hello"
        assert result["session_id"] is not None
        assert result["actor_id"] is not None


class TestInitializeMemory:
    """initialize_memory関数のテストクラス。"""

    def test_initialize_memory_with_valid_params(self):
        """
        有効なパラメータでメモリ初期化が成功することを確認。

        create_memory関数は実際のAWS呼び出しを行うため、モックを使用。
        """
        from app.main import initialize_memory

        with patch("app.main.create_memory") as mock_create_memory:
            mock_session_manager = MagicMock()
            mock_create_memory.return_value = mock_session_manager

            result = initialize_memory("test-memory-id", "test-session", "test-actor")

            assert result == mock_session_manager
            mock_create_memory.assert_called_once_with(
                "test-memory-id", "test-session", "test-actor"
            )

    def test_initialize_memory_with_none_memory_id(self):
        """
        memory_idがNoneの場合、Noneが返されることを確認。
        """
        from app.main import initialize_memory

        with patch("app.main.create_memory") as mock_create_memory:
            result = initialize_memory(None, "test-session", "test-actor")

            assert result is None
            # create_memoryは呼ばれない
            mock_create_memory.assert_not_called()

    def test_initialize_memory_with_empty_memory_id(self):
        """
        memory_idが空文字列の場合、Noneが返されることを確認。
        """
        from app.main import initialize_memory

        with patch("app.main.create_memory") as mock_create_memory:
            result = initialize_memory("", "test-session", "test-actor")

            assert result is None
            mock_create_memory.assert_not_called()

    def test_initialize_memory_handles_error(self):
        """
        create_memory呼び出し時のエラーが適切にハンドリングされることを確認。
        """
        from app.main import initialize_memory

        with patch("app.main.create_memory") as mock_create_memory:
            mock_create_memory.side_effect = Exception("Memory initialization failed")

            result = initialize_memory("test-memory-id", "test-session", "test-actor")

            # エラー時はNoneを返す
            assert result is None


class TestBuildS3Instruction:
    """build_s3_instruction関数のテストクラス。"""

    def test_build_s3_instruction_with_valid_params(self):
        """
        有効なバケットとキーでS3命令が正しく生成されることを確認。
        """
        from app.main import build_s3_instruction

        result = build_s3_instruction("my-bucket", "path/to/file.txt")

        # 命令文字列の内容を確認
        assert "my-bucket" in result
        assert "path/to/file.txt" in result
        assert "use_aws" in result
        assert "get_object" in result
        assert "Bucket" in result
        assert "Key" in result

    def test_build_s3_instruction_with_special_characters(self):
        """
        特殊文字を含むバケット名とキーでも正しく命令が生成されることを確認。
        """
        from app.main import build_s3_instruction

        result = build_s3_instruction(
            "my-bucket-123", "folder-name/sub_folder/file-name_v2.txt"
        )

        assert "my-bucket-123" in result
        assert "folder-name/sub_folder/file-name_v2.txt" in result

    def test_build_s3_instruction_contains_region(self):
        """
        S3命令にREGION情報が含まれることを確認。
        """
        from app.main import build_s3_instruction

        result = build_s3_instruction("test-bucket", "test-key")

        # REGIONはap-northeast-1がデフォルト
        assert "region" in result.lower()


class TestRunAgent:
    """run_agent関数のテストクラス。"""

    def test_run_agent_with_basic_input(self):
        """
        基本的な入力でエージェントが実行されることを確認。

        エージェント実行は課金が発生するため、モックを使用。
        """
        from app.main import run_agent

        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "エージェント応答"
            mock_create_agent.return_value = mock_agent

            result = run_agent("テスト入力", None, None)

            assert result == "エージェント応答"
            mock_create_agent.assert_called_once_with(
                session_manager=None, system_prompt=None
            )
            mock_agent.assert_called_once_with("テスト入力")

    def test_run_agent_with_session_manager(self):
        """
        session_managerを指定してエージェントが実行されることを確認。
        """
        from app.main import run_agent

        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "セッション管理応答"
            mock_create_agent.return_value = mock_agent

            mock_session_manager = MagicMock()
            result = run_agent("入力", mock_session_manager, None)

            assert result == "セッション管理応答"
            mock_create_agent.assert_called_once_with(
                session_manager=mock_session_manager, system_prompt=None
            )

    def test_run_agent_with_system_prompt(self):
        """
        system_promptを指定してエージェントが実行されることを確認。
        """
        from app.main import run_agent

        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "カスタムプロンプト応答"
            mock_create_agent.return_value = mock_agent

            result = run_agent("入力", None, "カスタムシステムプロンプト")

            assert result == "カスタムプロンプト応答"
            mock_create_agent.assert_called_once_with(
                session_manager=None, system_prompt="カスタムシステムプロンプト"
            )

    def test_run_agent_with_all_params(self):
        """
        すべてのパラメータを指定してエージェントが実行されることを確認。
        """
        from app.main import run_agent

        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = "完全な応答"
            mock_create_agent.return_value = mock_agent

            mock_session_manager = MagicMock()
            result = run_agent(
                "完全な入力", mock_session_manager, "完全なシステムプロンプト"
            )

            assert result == "完全な応答"
            mock_create_agent.assert_called_once_with(
                session_manager=mock_session_manager,
                system_prompt="完全なシステムプロンプト",
            )
            mock_agent.assert_called_once_with("完全な入力")

    def test_run_agent_handles_none_response(self):
        """
        エージェントがNoneを返した場合の処理を確認。
        """
        from app.main import run_agent

        with patch("app.main.create_agent") as mock_create_agent:
            mock_agent = MagicMock()
            mock_agent.return_value = None
            mock_create_agent.return_value = mock_agent

            result = run_agent("入力", None, None)

            assert result is None
