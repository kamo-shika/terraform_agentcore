"""
app/main.pyのテスト。

handler関数の動作を検証する。S3ワークフローモードのみをサポート。
"""

import os
from unittest.mock import patch

import pytest


class TestHandler:
    """handler関数のテストクラス。"""

    def test_handler_with_s3_event(self, sample_s3_event, mock_context, clean_env):
        """
        S3イベントでhandlerが正しく動作することを確認。

        Args:
            sample_s3_event: S3情報を含むイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        # S3ワークフロー処理にはMemory IDが必要
        os.environ["AGENTCORE_MEMORY_ID"] = "test-memory-id"

        with patch("app.main.run_workflow") as mock_run_workflow:
            mock_run_workflow.return_value = "User profile generated"

            from app.main import handler

            result = handler(sample_s3_event, mock_context)

            assert result["statusCode"] == 200
            assert "profile" in result["body"]["response"].lower() or "generated" in result["body"]["response"].lower()

            # run_workflowが正しいパラメータで呼ばれたか確認
            # run_workflow(s3_info, actor_id, session_id, memory_id)
            mock_run_workflow.assert_called_once()
            call_args = mock_run_workflow.call_args
            assert call_args[0][0] == sample_s3_event["s3_info"]  # s3_info
            assert call_args[0][3] == "test-memory-id"  # memory_id（位置3）

    def test_handler_without_s3_info(self, sample_event, mock_context, clean_env):
        """
        S3情報がないイベントではエラーが返されることを確認。

        Args:
            sample_event: S3情報を含まないイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        from app.main import handler

        result = handler(sample_event, mock_context)

        # S3情報がない場合は500を返す
        assert result["statusCode"] == 500
        assert "error" in result["body"]
        assert "s3_info is required" in result["body"]["error"]

    def test_handler_without_memory_id(self, sample_s3_event, mock_context, clean_env):
        """
        メモリIDがないS3イベントではエラーが返されることを確認。

        Args:
            sample_s3_event: S3情報を含むイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        # AGENTCORE_MEMORY_IDが設定されていない状態
        from app.main import handler

        result = handler(sample_s3_event, mock_context)

        # メモリIDがない場合は500を返す
        assert result["statusCode"] == 500
        assert "error" in result["body"]
        assert "Memory ID is required" in result["body"]["error"]

    def test_handler_with_invalid_s3_info(self, mock_context, clean_env):
        """
        s3_info.bucket/keyがNoneの場合のエラー処理を確認。

        S3情報が不完全な場合、適切にエラーハンドリングされることを検証。

        Args:
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        os.environ["AGENTCORE_MEMORY_ID"] = "test-memory-id"

        from app.main import handler

        # bucketがNoneのケース
        event_none_bucket = {"input": {"text": ""}, "s3_info": {"bucket": None, "key": "test-key"}}

        with patch("app.main.run_workflow") as mock_run_workflow:
            mock_run_workflow.side_effect = ValueError("bucket is required")

            result = handler(event_none_bucket, mock_context)

            # エラー時は500を返す
            assert result["statusCode"] == 500
            assert "error" in result["body"]

    def test_handler_workflow_error(self, sample_s3_event, mock_context, clean_env):
        """
        ワークフロー実行時のエラーが適切にハンドリングされることを確認。

        Args:
            sample_s3_event: S3情報を含むイベント
            mock_context: モックコンテキスト
            clean_env: 環境変数をクリーンにするフィクスチャ
        """
        os.environ["AGENTCORE_MEMORY_ID"] = "test-memory-id"

        with patch("app.main.run_workflow") as mock_run_workflow:
            mock_run_workflow.side_effect = Exception("ワークフローエラー")

            from app.main import handler

            result = handler(sample_s3_event, mock_context)

            # エラー時は500を返す
            assert result["statusCode"] == 500
            assert "body" in result
            assert "error" in result["body"]
            assert "ワークフローエラー" in result["body"]["error"]


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
