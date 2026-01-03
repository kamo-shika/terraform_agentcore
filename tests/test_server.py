"""
app/server.py のテスト。

FastAPIエンドポイントの動作を検証する。
"""

import pytest


class TestPingEndpoint:
    """
    /ping エンドポイントのテスト。
    """

    async def test_ping_returns_healthy(self, async_client):
        """
        GETリクエストで健全なステータスを返すことを確認する。
        """
        response = await async_client.get("/ping")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestRootEndpoint:
    """
    / ルートエンドポイントのテスト。
    """

    async def test_root_returns_service_info(self, async_client):
        """
        サービス情報を含む辞書を返すことを確認する。
        """
        response = await async_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "AgentCore Runtime Server"
        assert data["status"] == "running"
        assert "endpoints" in data


class TestInvocationsEndpoint:
    """
    /invocations エンドポイントのテスト。
    """

    async def test_invocations_with_valid_input(self, async_client, mocker):
        """
        正常な入力でエージェントが実行されることを確認する。
        """
        # handler関数をモック
        mock_handler = mocker.patch("app.server.handler")
        mock_handler.return_value = {
            "statusCode": 200,
            "body": {"response": "テスト応答です"}
        }

        response = await async_client.post(
            "/invocations",
            json={"input": {"text": "テストメッセージ"}}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "テスト応答です"
        assert data["status"] == "success"
        mock_handler.assert_called_once()

    async def test_invocations_with_empty_input(self, async_client, mocker):
        """
        空の入力でも処理されることを確認する。
        """
        mock_handler = mocker.patch("app.server.handler")
        mock_handler.return_value = {
            "statusCode": 200,
            "body": {"response": "入力がありません"}
        }

        response = await async_client.post(
            "/invocations",
            json={"input": {}}
        )

        assert response.status_code == 200

    async def test_invocations_with_error_response(self, async_client, mocker):
        """
        handlerがエラーを返した場合のレスポンスを確認する。
        """
        mock_handler = mocker.patch("app.server.handler")
        mock_handler.return_value = {
            "statusCode": 400,
            "body": {"error": "不正なリクエスト"}
        }

        response = await async_client.post(
            "/invocations",
            json={"input": {"text": "テスト"}}
        )

        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    async def test_invocations_with_exception(self, async_client, mocker):
        """
        handler実行中に例外が発生した場合のエラーハンドリングを確認する。
        """
        mock_handler = mocker.patch("app.server.handler")
        mock_handler.side_effect = Exception("テスト例外")

        response = await async_client.post(
            "/invocations",
            json={"input": {"text": "テスト"}}
        )

        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert "テスト例外" in data["error"]

    async def test_invocations_with_invalid_json(self, async_client):
        """
        不正なJSONが送信された場合のエラーハンドリングを確認する。
        """
        response = await async_client.post(
            "/invocations",
            content="not valid json",
            headers={"Content-Type": "application/json"}
        )

        # 不正なJSONはサーバー側のexceptブロックで捕捉され500を返す
        assert response.status_code == 500
        data = response.json()
        assert "error" in data

    async def test_invocations_with_session_info(self, async_client, mocker):
        """
        セッション情報を含むリクエストを処理できることを確認する。
        """
        mock_handler = mocker.patch("app.server.handler")
        mock_handler.return_value = {
            "statusCode": 200,
            "body": {"response": "セッション応答"}
        }

        response = await async_client.post(
            "/invocations",
            json={
                "input": {"text": "テスト"},
                "sessionId": "session-123",
                "actorId": "user-456"
            }
        )

        assert response.status_code == 200
        # handlerに渡されたイベントを確認
        call_args = mock_handler.call_args[0][0]
        assert call_args["sessionId"] == "session-123"
        assert call_args["actorId"] == "user-456"
