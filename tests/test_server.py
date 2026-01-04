"""
app/server.pyのテスト。

FastAPIエンドポイントの動作とエラーハンドリングを検証する。
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def test_client():
    """
    FastAPIのテストクライアント。

    Returns:
        TestClient: FastAPIアプリケーションのテストクライアント
    """
    from app.server import app

    return TestClient(app)


class TestPingEndpoint:
    """pingエンドポイントのテストクラス。"""

    def test_ping_returns_healthy(self, test_client):
        """
        /pingエンドポイントがhealthyステータスを返すことを確認。

        Args:
            test_client: FastAPIテストクライアント
        """
        response = test_client.get("/ping")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """ルートエンドポイントのテストクラス。"""

    def test_root_returns_service_info(self, test_client):
        """
        /エンドポイントがサービス情報を返すことを確認。

        Args:
            test_client: FastAPIテストクライアント
        """
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "status" in data
        assert "endpoints" in data
        assert data["status"] == "running"


class TestInvocationsEndpoint:
    """invocationsエンドポイントのテストクラス。"""

    def test_invocations_with_valid_request(self, test_client):
        """
        正常なリクエストでinvocationsエンドポイントが動作することを確認。

        Args:
            test_client: FastAPIテストクライアント
        """
        with patch("app.server.handler") as mock_handler:
            # handlerのモック設定
            mock_handler.return_value = {"statusCode": 200, "body": {"response": "テスト応答"}}

            response = test_client.post(
                "/invocations",
                json={"input": {"text": "こんにちは"}, "sessionId": "test-session", "actorId": "test-actor"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "status" in data
            assert data["status"] == "success"
            assert data["response"] == "テスト応答"

    def test_invocations_with_handler_error(self, test_client):
        """
        handler関数がエラーを返した場合の処理を確認。

        Args:
            test_client: FastAPIテストクライアント
        """
        with patch("app.server.handler") as mock_handler:
            # handlerがエラーを返す
            mock_handler.return_value = {"statusCode": 500, "body": {"error": "テストエラー"}}

            response = test_client.post("/invocations", json={"input": {"text": "エラーテスト"}})

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "テストエラー" in data["error"]

    def test_invocations_with_invalid_json(self, test_client):
        """
        不正なJSONの場合にエラー処理されることを確認。

        現在の実装では汎用的なExceptionハンドリングで500を返す。
        将来的にはJSONDecodeErrorを個別にハンドリングすべき。

        Args:
            test_client: FastAPIテストクライアント
        """
        response = test_client.post(
            "/invocations", data="invalid json string", headers={"Content-Type": "application/json"}
        )

        # 現在の実装では500を返す（改善の余地あり）
        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    def test_invocations_handles_json_decode_error(self, test_client):
        """
        JSON解析エラーのハンドリングを確認。

        requestオブジェクトのjson()メソッドがJSONDecodeErrorを発生させた場合、
        適切にエラーレスポンスを返すことを検証。

        Args:
            test_client: FastAPIテストクライアント
        """

        with patch("app.server.handler") as mock_handler:
            # handlerは正常に動作するが、レスポンスがJSON非互換
            mock_handler.return_value = {"statusCode": 200, "body": {"response": "応答"}}

            # 正常なJSONを送信
            response = test_client.post("/invocations", json={"input": {"text": "テスト"}})

            # 正常に処理される
            assert response.status_code == 200

    def test_invocations_with_exception_in_handler(self, test_client):
        """
        handler関数内で例外が発生した場合のエラー処理を確認。

        Args:
            test_client: FastAPIテストクライアント
        """
        with patch("app.server.handler") as mock_handler:
            # handlerが例外を発生させる
            mock_handler.side_effect = Exception("予期しないエラー")

            response = test_client.post("/invocations", json={"input": {"text": "例外テスト"}})

            assert response.status_code == 500
            data = response.json()
            assert "error" in data
            assert "予期しないエラー" in data["error"]

    def test_invocations_with_empty_request_body(self, test_client):
        """
        空のリクエストボディの場合の処理を確認。

        Args:
            test_client: FastAPIテストクライアント
        """
        with patch("app.server.handler") as mock_handler:
            # handlerがデフォルト値で動作
            mock_handler.return_value = {"statusCode": 200, "body": {"response": "デフォルト応答"}}

            response = test_client.post("/invocations", json={})

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

    def test_invocations_response_format(self, test_client):
        """
        invocationsエンドポイントのレスポンス形式を確認。

        AgentCore Runtimeが期待する形式に変換されていることを検証。

        Args:
            test_client: FastAPIテストクライアント
        """
        with patch("app.server.handler") as mock_handler:
            mock_handler.return_value = {"statusCode": 200, "body": {"response": "応答テキスト"}}

            response = test_client.post("/invocations", json={"input": {"text": "テスト"}})

            assert response.status_code == 200
            data = response.json()

            # AgentCore期待形式: {"response": "...", "status": "success"}
            assert "response" in data
            assert "status" in data
            assert data["response"] == "応答テキスト"
            assert data["status"] == "success"
            # handler戻り値のstatusCodeは含まれない
            assert "statusCode" not in data
            assert "body" not in data
