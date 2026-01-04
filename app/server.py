"""
FastAPI HTTPサーバー - Bedrock AgentCore Runtime用。

このモジュールは、AgentCore Runtimeとの通信用にHTTPエンドポイントを提供します。
- /invocations: エージェントのメイン処理エンドポイント
- /ping: ヘルスチェックエンドポイント
"""

import logging
import os
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from strands.telemetry import StrandsTelemetry

from .main import handler

# ロギング設定はconfig.pyで一元管理されている
logger = logging.getLogger(__name__)

# ==============================================================================
# OpenTelemetry設定
# ==============================================================================
# StrandsTelemetryを初期化してOTLPエクスポーターを設定
# AgentCore Runtimeがテレメトリデータを収集し、CloudWatchに配信する
try:
    strands_telemetry = StrandsTelemetry()
    strands_telemetry.setup_otlp_exporter()
    logger.info("StrandsTelemetry initialized with OTLP exporter")
except Exception as e:
    # テレメトリ初期化に失敗してもサーバーは起動を続行
    logger.warning(f"Failed to initialize StrandsTelemetry: {e}")

# FastAPIアプリケーションの初期化
app = FastAPI(title="AgentCore Runtime Server", description="Bedrock AgentCore Runtime用HTTPサーバー", version="1.0.0")


@app.get("/ping")
async def ping() -> dict[str, str]:
    """
    ヘルスチェックエンドポイント。

    Returns:
        ステータスメッセージを含む辞書: {"status": "healthy"}

    Example:
        >>> GET /ping
        {"status": "healthy"}
    """
    logger.info("Health check requested")
    return {"status": "healthy"}


@app.post("/invocations")
async def invocations(request: Request) -> JSONResponse:
    """
    エージェント実行のメインエンドポイント。

    AgentCore Runtimeからのリクエストを受け取り、エージェントを実行します。
    リクエストボディはそのままhandler関数に渡されます。

    Args:
        request: FastAPIリクエストオブジェクト

    Returns:
        エージェントの実行結果を含むJSONレスポンス

    Raises:
        Exception: エージェント実行時のエラー（catchされて500エラーとして返される）

    Example:
        >>> POST /invocations
        >>> {
        >>>   "input": {
        >>>     "text": "Hello, agent!"
        >>>   },
        >>>   "sessionId": "session-123",
        >>>   "actorId": "user-456"
        >>> }
    """
    try:
        # リクエストボディをJSONとして取得
        event: dict[str, Any] = await request.json()
        logger.info(f"Invocation request received: {event}")

        # main.pyのhandler関数を呼び出し
        # contextパラメータは空の辞書（AgentCoreでは未使用）
        result = handler(event, {})

        logger.info("Invocation completed successfully")

        # AgentCore Runtimeが期待する形式にレスポンスを変換
        # handler戻り値: {"statusCode": 200, "body": {"response": "..."}}
        # AgentCore期待値: {"response": "...", "status": "success"}
        if result.get("statusCode") == 200:
            response_body = result.get("body", {})
            response_text = response_body.get("response", "")
            agentcore_response = {"response": response_text, "status": "success"}
            return JSONResponse(content=agentcore_response)
        else:
            # エラーの場合
            error_body = result.get("body", {})
            return JSONResponse(
                status_code=result.get("statusCode", 500), content={"error": error_body.get("error", "Unknown error")}
            )

    except Exception as e:
        logger.error(f"Error processing invocation: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/")
async def root() -> dict[str, Any]:
    """
    ルートエンドポイント。

    Returns:
        サーバー情報を含む辞書
    """
    return {
        "service": "AgentCore Runtime Server",
        "status": "running",
        "endpoints": {"health": "/ping", "invocations": "/invocations (POST)"},
    }


@app.get("/debug")
async def debug() -> dict[str, Any]:
    """
    デバッグ用エンドポイント。環境変数とメモリ設定を返す。

    Returns:
        環境変数とメモリ設定の情報を含む辞書
    """
    from .config import LTM_ENABLED, LTM_NAMESPACE, get_memory_id

    memory_id = get_memory_id()
    return {
        "env": {
            "AGENTCORE_MEMORY_ID": os.getenv("AGENTCORE_MEMORY_ID", "NOT SET"),
            "LTM_ENABLED": os.getenv("LTM_ENABLED", "NOT SET"),
        },
        "config": {
            "memory_id": memory_id,
            "ltm_enabled": LTM_ENABLED,
            "ltm_namespace": LTM_NAMESPACE,
        },
        "memory_initialized": memory_id is not None and len(memory_id) > 0,
    }


if __name__ == "__main__":
    # ローカルでの開発/テスト用
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
