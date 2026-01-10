"""
アプリケーション全体で使用される設定値の一元管理モジュール。

このモジュールは、環境変数から設定値を読み取り、デフォルト値を提供する。
設定値は定数として定義され、実行時に動的に値を取得するヘルパー関数も提供する。
また、アプリケーション全体のロギング設定も一元管理する。
"""

import logging
import os

# ========================================
# 定数定義
# ========================================

# モデルID: 使用するAIモデルの識別子（コスト最適化のためNova 2 Liteを使用）
# 注意: Nova 2 Liteは推論プロファイルが必要で、日本リージョン用は jp.amazon.nova-2-lite-v1:0 を使用
MODEL_ID = os.getenv("MODEL_ID", "jp.amazon.nova-2-lite-v1:0")

# リージョン: AWSリソースのデプロイ先リージョン
REGION = os.getenv("AWS_REGION", "ap-northeast-1")

# デフォルトセッションID: ローカル開発用のセッション識別子
DEFAULT_SESSION_ID = os.getenv("SESSION_ID", "local-session-001")

# デフォルトアクターID: ローカル開発用のユーザー識別子
DEFAULT_ACTOR_ID = os.getenv("ACTOR_ID", "local-user")

# デフォルト入力テキスト: エージェントへのデフォルト入力
DEFAULT_INPUT_TEXT = os.getenv("DEFAULT_INPUT_TEXT", "Hello")

# ========================================
# 長期メモリ（LTM）設定
# ========================================

# LTM有効フラグ: ファイル要約の蓄積機能を有効にするかどうか
LTM_ENABLED = os.getenv("LTM_ENABLED", "true").lower() == "true"

# LTM取得件数: 過去の要約を取得する最大件数
LTM_SUMMARY_TOP_K = int(os.getenv("LTM_SUMMARY_TOP_K", "10"))

# LTM関連度スコア閾値: 取得する要約の最低関連度スコア（0.0〜1.0）
LTM_SUMMARY_SCORE = float(os.getenv("LTM_SUMMARY_SCORE", "0.3"))

# LTM Namespace: ファイル要約を保存するNamespace（Terraformと一致させる）
LTM_NAMESPACE = "/file-summaries/{actorId}"

# Actor状態Namespace: Actorの活動状態を保存するNamespace（Terraformと一致させる）
ACTOR_STATE_NAMESPACE = "/actor-state/{actorId}"

# Actor状態取得件数: 過去のActor状態を取得する最大件数
ACTOR_STATE_TOP_K = int(os.getenv("ACTOR_STATE_TOP_K", "5"))


# ========================================
# ロギング設定
# ========================================


def setup_logging() -> None:
    """
    アプリケーション全体のロギング設定を初期化する。

    この関数は、アプリケーション起動時に一度だけ呼び出される。
    ログレベル、フォーマット、ハンドラーを統一的に設定する。

    Returns:
        None
    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )


# ロギング設定を初期化（モジュールインポート時に一度だけ実行）
setup_logging()


# ========================================
# ヘルパー関数
# ========================================


def get_session_id(event: dict) -> str:
    """
    セッションIDを取得する。

    優先順位:
    1. イベントのsessionIdキー
    2. 環境変数SESSION_ID
    3. DEFAULT_SESSION_ID定数

    Args:
        event: AgentCoreから渡されるイベント辞書

    Returns:
        セッションID文字列
    """
    return event.get("sessionId") or os.getenv("SESSION_ID") or DEFAULT_SESSION_ID


def get_actor_id(event: dict) -> str:
    """
    アクターIDを取得する。

    優先順位:
    1. イベントのactorIdキー
    2. 環境変数ACTOR_ID
    3. DEFAULT_ACTOR_ID定数

    Args:
        event: AgentCoreから渡されるイベント辞書

    Returns:
        アクターID文字列
    """
    return event.get("actorId") or os.getenv("ACTOR_ID") or DEFAULT_ACTOR_ID


def get_input_text(event: dict) -> str:
    """
    入力テキストを取得する。

    優先順位:
    1. イベントのinput.textキー
    2. 環境変数DEFAULT_INPUT_TEXT
    3. デフォルト値 "Hello"

    Args:
        event: AgentCoreから渡されるイベント辞書

    Returns:
        入力テキスト文字列
    """
    input_obj = event.get("input", {})
    text = input_obj.get("text", "")
    if text:
        return text

    # 環境変数を確認（テスト時の動的な変更を反映するため）
    env_text = os.getenv("DEFAULT_INPUT_TEXT")
    if env_text:
        return env_text

    # 最終的なデフォルト値
    return "Hello"


def get_memory_id() -> str | None:
    """
    メモリIDを環境変数から取得する。

    Returns:
        環境変数AGENTCORE_MEMORY_IDの値、設定されていない場合はNone
    """
    return os.getenv("AGENTCORE_MEMORY_ID")
