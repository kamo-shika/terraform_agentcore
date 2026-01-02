"""
pytestの共通設定とフィクスチャ。

このファイルでは、テスト全体で使用する共通のフィクスチャと設定を定義する。
"""
import os
import pytest


@pytest.fixture
def sample_event():
    """
    AgentCoreから送られる標準的なイベントのサンプル。

    Returns:
        dict: 基本的なテキスト入力を含むイベント
    """
    return {
        "input": {
            "text": "こんにちは"
        }
    }


@pytest.fixture
def sample_event_with_session():
    """
    セッション情報を含むイベントのサンプル。

    Returns:
        dict: sessionIdとactorIdを含むイベント
    """
    return {
        "input": {
            "text": "テストメッセージです"
        },
        "sessionId": "test-session-001",
        "actorId": "test-user-001"
    }


@pytest.fixture
def sample_s3_event():
    """
    S3ファイル処理用のイベントのサンプル。

    Returns:
        dict: S3バケットとキー情報を含むイベント
    """
    return {
        "input": {
            "text": ""
        },
        "s3_info": {
            "bucket": "test-bucket",
            "key": "test-folder/test-file.txt"
        }
    }


@pytest.fixture
def empty_event():
    """
    入力が空のイベント。

    エラーハンドリングのテストに使用する。

    Returns:
        dict: 空の入力を持つイベント
    """
    return {
        "input": {}
    }


@pytest.fixture
def invalid_event():
    """
    不正な形式のイベント。

    エラーハンドリングのテストに使用する。

    Returns:
        dict: inputキーがないイベント
    """
    return {}


@pytest.fixture
def mock_context():
    """
    Lambda/AgentCore実行時のコンテキストオブジェクトのモック。

    現在のhandler実装ではcontextは使用されていないが、
    将来の拡張に備えて定義しておく。

    Returns:
        dict: 空のコンテキストオブジェクト
    """
    return {}


@pytest.fixture
def clean_env(monkeypatch):
    """
    テスト用に環境変数をクリーンな状態にするフィクスチャ。

    AGENTCORE関連の環境変数を削除して、テストの独立性を確保する。

    Args:
        monkeypatch: pytestのmonkeypatchフィクスチャ

    Yields:
        None: 環境変数がクリーンな状態でテストを実行
    """
    # 削除する環境変数のリスト
    env_vars_to_remove = [
        "AGENTCORE_MEMORY_ID",
        "SESSION_ID",
        "ACTOR_ID",
    ]

    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)

    yield


@pytest.fixture
def set_memory_env(monkeypatch):
    """
    Memory機能をテストするための環境変数を設定するフィクスチャ。

    Args:
        monkeypatch: pytestのmonkeypatchフィクスチャ

    Returns:
        callable: 環境変数を設定する関数
    """
    def _set_env(memory_id="test-memory-id", session_id="test-session", actor_id="test-actor"):
        """
        Memory関連の環境変数を設定する。

        Args:
            memory_id: メモリID
            session_id: セッションID
            actor_id: アクターID
        """
        if memory_id:
            monkeypatch.setenv("AGENTCORE_MEMORY_ID", memory_id)
        monkeypatch.setenv("SESSION_ID", session_id)
        monkeypatch.setenv("ACTOR_ID", actor_id)

    return _set_env
