"""
FastAPI HTTPサーバー - Bedrock AgentCore Runtime用。

このモジュールは、AgentCore Runtimeとの通信用にHTTPエンドポイントを提供します。
- /invocations: エージェントのメイン処理エンドポイント
- /ping: ヘルスチェックエンドポイント
"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .main import handler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーションの初期化
app = FastAPI(
    title="AgentCore Runtime Server",
    description="Bedrock AgentCore Runtime用HTTPサーバー",
    version="1.0.0"
)


@app.get("/ping")
async def ping():
    """
    ヘルスチェックエンドポイント。

    Returns:
        dict: ステータスメッセージを含む辞書

    Example:
        >>> GET /ping
        {"status": "healthy"}
    """
    logger.info("Health check requested")
    return {"status": "healthy"}


@app.post("/invocations")
async def invocations(request: Request):
    """
    エージェント実行のメインエンドポイント。

    AgentCore Runtimeからのリクエストを受け取り、エージェントを実行します。
    リクエストボディはそのままhandler関数に渡されます。

    Args:
        request: FastAPIリクエストオブジェクト

    Returns:
        JSONResponse: エージェントの実行結果

    Raises:
        HTTPException: エージェント実行時のエラー

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
        event = await request.json()
        logger.info(f"Invocation request received: {event}")

        # main.pyのhandler関数を呼び出し
        # contextパラメータは空の辞書（AgentCoreでは未使用）
        result = handler(event, {})

        logger.info(f"Invocation completed with status: {result.get('statusCode')}")

        # レスポンスを返す
        return JSONResponse(
            status_code=result.get("statusCode", 200),
            content=result.get("body", {})
        )

    except Exception as e:
        logger.error(f"Error processing invocation: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/")
async def root():
    """
    ルートエンドポイント。

    Returns:
        dict: サーバー情報を含む辞書
    """
    return {
        "service": "AgentCore Runtime Server",
        "status": "running",
        "endpoints": {
            "health": "/ping",
            "invocations": "/invocations (POST)"
        }
    }


if __name__ == "__main__":
    # ローカルでの開発/テスト用
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
