"""
app/config.pyのテスト。

このテストは、アプリケーション全体で使用される設定値の一元管理をテストする。
設定値は環境変数から取得でき、デフォルト値も提供される。
"""



class TestDefaultValues:
    """
    設定のデフォルト値をテストするクラス。

    環境変数が設定されていない場合、適切なデフォルト値が使用されることを確認する。
    """

    def test_default_model_id(self, clean_env):
        """
        MODEL_IDのデフォルト値が正しいことを確認。

        環境変数が設定されていない場合、日本リージョンのClaude Sonnet 4.5が
        デフォルトとして使用される。
        """
        from app.config import MODEL_ID

        assert MODEL_ID == "jp.anthropic.claude-sonnet-4-5-20250929-v1:0"

    def test_default_region(self, clean_env):
        """
        REGIONのデフォルト値が正しいことを確認。

        環境変数が設定されていない場合、ap-northeast-1（東京リージョン）が
        デフォルトとして使用される。
        """
        from app.config import REGION

        assert REGION == "ap-northeast-1"

    def test_default_session_id(self, clean_env):
        """
        DEFAULT_SESSION_IDのデフォルト値が正しいことを確認。

        環境変数が設定されていない場合、ローカル開発用のセッションIDが
        デフォルトとして使用される。
        """
        from app.config import DEFAULT_SESSION_ID

        assert DEFAULT_SESSION_ID == "local-session-001"

    def test_default_actor_id(self, clean_env):
        """
        DEFAULT_ACTOR_IDのデフォルト値が正しいことを確認。

        環境変数が設定されていない場合、ローカル開発用のアクターIDが
        デフォルトとして使用される。
        """
        from app.config import DEFAULT_ACTOR_ID

        assert DEFAULT_ACTOR_ID == "local-user"

    def test_default_input_text(self, clean_env):
        """
        DEFAULT_INPUT_TEXTのデフォルト値が正しいことを確認。

        環境変数が設定されていない場合、シンプルな挨拶がデフォルトの
        入力テキストとして使用される。
        """
        from app.config import DEFAULT_INPUT_TEXT

        assert DEFAULT_INPUT_TEXT == "Hello"


class TestEnvironmentVariableOverrides:
    """
    環境変数による設定値の上書きをテストするクラス。

    環境変数が設定されている場合、その値がデフォルト値より優先されることを確認する。
    """

    def test_model_id_from_env(self, monkeypatch):
        """
        MODEL_IDが環境変数から正しく読み取られることを確認。

        MODEL_ID環境変数が設定されている場合、その値が使用される。
        """
        # 環境変数を設定
        custom_model = "us.anthropic.claude-3-opus-20240229-v1:0"
        monkeypatch.setenv("MODEL_ID", custom_model)

        # モジュールを再インポートして環境変数を反映
        import importlib

        import app.config

        importlib.reload(app.config)

        assert app.config.MODEL_ID == custom_model

    def test_region_from_env(self, monkeypatch):
        """
        REGIONが環境変数から正しく読み取られることを確認。

        AWS_REGION環境変数が設定されている場合、その値が使用される。
        """
        # 環境変数を設定
        custom_region = "us-east-1"
        monkeypatch.setenv("AWS_REGION", custom_region)

        # モジュールを再インポートして環境変数を反映
        import importlib

        import app.config

        importlib.reload(app.config)

        assert app.config.REGION == custom_region

    def test_session_id_from_env(self, monkeypatch):
        """
        DEFAULT_SESSION_IDが環境変数から正しく読み取られることを確認。

        SESSION_ID環境変数が設定されている場合、その値が使用される。
        """
        # 環境変数を設定
        custom_session = "custom-session-123"
        monkeypatch.setenv("SESSION_ID", custom_session)

        # モジュールを再インポートして環境変数を反映
        import importlib

        import app.config

        importlib.reload(app.config)

        assert app.config.DEFAULT_SESSION_ID == custom_session

    def test_actor_id_from_env(self, monkeypatch):
        """
        DEFAULT_ACTOR_IDが環境変数から正しく読み取られることを確認。

        ACTOR_ID環境変数が設定されている場合、その値が使用される。
        """
        # 環境変数を設定
        custom_actor = "custom-user-456"
        monkeypatch.setenv("ACTOR_ID", custom_actor)

        # モジュールを再インポートして環境変数を反映
        import importlib

        import app.config

        importlib.reload(app.config)

        assert app.config.DEFAULT_ACTOR_ID == custom_actor

    def test_input_text_from_env(self, monkeypatch):
        """
        DEFAULT_INPUT_TEXTが環境変数から正しく読み取られることを確認。

        DEFAULT_INPUT_TEXT環境変数が設定されている場合、その値が使用される。
        """
        # 環境変数を設定
        custom_text = "こんにちは、世界！"
        monkeypatch.setenv("DEFAULT_INPUT_TEXT", custom_text)

        # モジュールを再インポートして環境変数を反映
        import importlib

        import app.config

        importlib.reload(app.config)

        assert app.config.DEFAULT_INPUT_TEXT == custom_text


class TestConfigStructure:
    """
    設定モジュールの構造をテストするクラス。

    必要な定数がすべて存在し、適切な型であることを確認する。
    """

    def test_all_required_constants_exist(self, clean_env):
        """
        必要な設定定数がすべて存在することを確認。

        config.pyモジュールに、以下の定数が定義されていることを確認：
        - MODEL_ID
        - REGION
        - DEFAULT_SESSION_ID
        - DEFAULT_ACTOR_ID
        - DEFAULT_INPUT_TEXT
        """
        import app.config

        # すべての必須定数が存在することを確認
        required_constants = [
            "MODEL_ID",
            "REGION",
            "DEFAULT_SESSION_ID",
            "DEFAULT_ACTOR_ID",
            "DEFAULT_INPUT_TEXT",
        ]

        for constant in required_constants:
            assert hasattr(app.config, constant), f"{constant} is not defined in app.config"

    def test_all_constants_are_strings(self, clean_env):
        """
        すべての設定定数が文字列型であることを確認。

        設定値はすべて文字列として定義されているべき。
        """
        from app.config import (
            DEFAULT_ACTOR_ID,
            DEFAULT_INPUT_TEXT,
            DEFAULT_SESSION_ID,
            MODEL_ID,
            REGION,
        )

        assert isinstance(MODEL_ID, str), "MODEL_ID should be a string"
        assert isinstance(REGION, str), "REGION should be a string"
        assert isinstance(DEFAULT_SESSION_ID, str), "DEFAULT_SESSION_ID should be a string"
        assert isinstance(DEFAULT_ACTOR_ID, str), "DEFAULT_ACTOR_ID should be a string"
        assert isinstance(DEFAULT_INPUT_TEXT, str), "DEFAULT_INPUT_TEXT should be a string"

    def test_no_empty_default_values(self, clean_env):
        """
        デフォルト値が空文字列でないことを確認。

        すべてのデフォルト値は意味のある値を持つべき。
        """
        from app.config import (
            DEFAULT_ACTOR_ID,
            DEFAULT_INPUT_TEXT,
            DEFAULT_SESSION_ID,
            MODEL_ID,
            REGION,
        )

        assert MODEL_ID != "", "MODEL_ID should not be empty"
        assert REGION != "", "REGION should not be empty"
        assert DEFAULT_SESSION_ID != "", "DEFAULT_SESSION_ID should not be empty"
        assert DEFAULT_ACTOR_ID != "", "DEFAULT_ACTOR_ID should not be empty"
        assert DEFAULT_INPUT_TEXT != "", "DEFAULT_INPUT_TEXT should not be empty"


class TestConfigFunctions:
    """
    設定を取得するヘルパー関数をテストするクラス。

    実行時に動的に設定値を取得する関数の動作を確認する。
    """

    def test_get_session_id_with_event_value(self, clean_env):
        """
        get_session_id関数がイベントからセッションIDを取得することを確認。

        イベントにsessionIdが含まれている場合、その値が優先される。
        """
        from app.config import get_session_id

        event = {"sessionId": "event-session-999"}
        session_id = get_session_id(event)

        assert session_id == "event-session-999"

    def test_get_session_id_with_env_fallback(self, monkeypatch, clean_env):
        """
        get_session_id関数が環境変数からセッションIDを取得することを確認。

        イベントにsessionIdがない場合、環境変数SESSION_IDが使用される。
        """
        from app.config import get_session_id

        monkeypatch.setenv("SESSION_ID", "env-session-888")
        event = {}
        session_id = get_session_id(event)

        assert session_id == "env-session-888"

    def test_get_session_id_with_default_fallback(self, clean_env):
        """
        get_session_id関数がデフォルト値を使用することを確認。

        イベントにも環境変数にもセッションIDがない場合、
        デフォルト値が使用される。
        """
        from app.config import get_session_id

        event = {}
        session_id = get_session_id(event)

        assert session_id == "local-session-001"

    def test_get_actor_id_with_event_value(self, clean_env):
        """
        get_actor_id関数がイベントからアクターIDを取得することを確認。

        イベントにactorIdが含まれている場合、その値が優先される。
        """
        from app.config import get_actor_id

        event = {"actorId": "event-actor-777"}
        actor_id = get_actor_id(event)

        assert actor_id == "event-actor-777"

    def test_get_actor_id_with_env_fallback(self, monkeypatch, clean_env):
        """
        get_actor_id関数が環境変数からアクターIDを取得することを確認。

        イベントにactorIdがない場合、環境変数ACTOR_IDが使用される。
        """
        from app.config import get_actor_id

        monkeypatch.setenv("ACTOR_ID", "env-actor-666")
        event = {}
        actor_id = get_actor_id(event)

        assert actor_id == "env-actor-666"

    def test_get_actor_id_with_default_fallback(self, clean_env):
        """
        get_actor_id関数がデフォルト値を使用することを確認。

        イベントにも環境変数にもアクターIDがない場合、
        デフォルト値が使用される。
        """
        from app.config import get_actor_id

        event = {}
        actor_id = get_actor_id(event)

        assert actor_id == "local-user"

    def test_get_input_text_with_event_value(self, clean_env):
        """
        get_input_text関数がイベントから入力テキストを取得することを確認。

        イベントのinput.textが存在する場合、その値が使用される。
        """
        from app.config import get_input_text

        event = {"input": {"text": "イベントからのテキスト"}}
        input_text = get_input_text(event)

        assert input_text == "イベントからのテキスト"

    def test_get_input_text_with_empty_input(self, clean_env):
        """
        get_input_text関数がデフォルト値を使用することを確認。

        イベントのinput.textが空の場合、デフォルト値が使用される。
        """
        from app.config import get_input_text

        event = {"input": {}}
        input_text = get_input_text(event)

        assert input_text == "Hello"

    def test_get_input_text_with_no_input(self, clean_env):
        """
        get_input_text関数がinputキーがない場合も処理できることを確認。

        イベントにinputキー自体がない場合でも、デフォルト値が使用される。
        """
        from app.config import get_input_text

        event = {}
        input_text = get_input_text(event)

        assert input_text == "Hello"

    def test_get_memory_id_from_env(self, monkeypatch, clean_env):
        """
        get_memory_id関数が環境変数からメモリIDを取得することを確認。

        AGENTCORE_MEMORY_ID環境変数が設定されている場合、その値が返される。
        """
        from app.config import get_memory_id

        monkeypatch.setenv("AGENTCORE_MEMORY_ID", "test-memory-123")
        memory_id = get_memory_id()

        assert memory_id == "test-memory-123"

    def test_get_memory_id_returns_none_when_not_set(self, clean_env):
        """
        get_memory_id関数が環境変数未設定時にNoneを返すことを確認。

        AGENTCORE_MEMORY_ID環境変数が設定されていない場合、Noneが返される。
        これはメモリ機能が無効であることを示す。
        """
        from app.config import get_memory_id

        memory_id = get_memory_id()

        assert memory_id is None
