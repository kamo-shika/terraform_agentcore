"""
lambda/invoker.pyのテスト。

boto3クライアントのタイムアウト設定を検証する。
"""

import pytest


class TestBoto3ClientConfig:
    """boto3クライアント設定のテスト。"""

    def test_read_timeout_is_900_seconds(self):
        """read_timeoutが900秒（15分）に設定されていることを確認。"""
        from invoker import AGENTCORE_CLIENT_READ_TIMEOUT

        assert AGENTCORE_CLIENT_READ_TIMEOUT == 900

    def test_connect_timeout_is_10_seconds(self):
        """connect_timeoutが10秒に設定されていることを確認。"""
        from invoker import AGENTCORE_CLIENT_CONNECT_TIMEOUT

        assert AGENTCORE_CLIENT_CONNECT_TIMEOUT == 10

    def test_bedrock_agentcore_client_has_custom_config(self):
        """bedrock_agentcoreクライアントにカスタム設定が適用されていることを確認。"""
        from invoker import bedrock_agentcore

        # クライアントのmeta.configからタイムアウト設定を確認
        config = bedrock_agentcore._client_config

        assert config.read_timeout == 900
        assert config.connect_timeout == 10
