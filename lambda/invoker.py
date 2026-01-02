"""
S3イベントを受信してAgentCore Runtimeを呼び出すLambda関数。

この関数は以下を実行します：
1. S3イベント通知を受信
2. バケット名とオブジェクトキー情報を抽出
3. S3オブジェクトメタデータからuser-idを取得
4. S3オブジェクトの詳細情報とともにAgentCore Runtimeを呼び出し
5. エージェントからのストリーミングレスポンスを処理
"""

import json
import os
import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# ロギング設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# AWSクライアントの初期化
s3_client = boto3.client('s3')
bedrock_agentcore = boto3.client('bedrock-agentcore')

# 環境変数
AGENT_RUNTIME_ARN = os.environ.get('AGENT_RUNTIME_ARN')
AGENTCORE_MEMORY_ID = os.environ.get('AGENTCORE_MEMORY_ID')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    S3イベントを処理してAgentCore Runtimeを呼び出すLambdaハンドラー関数。

    Args:
        event: S3イベント通知
        context: Lambdaコンテキストオブジェクト

    Returns:
        ステータスとレスポンス詳細を含む辞書
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # 環境変数の検証
    if not AGENT_RUNTIME_ARN:
        error_msg = "AGENT_RUNTIME_ARN environment variable is not set"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

    try:
        # イベント内の各S3レコードを処理
        results = []
        for record in event.get('Records', []):
            if record.get('eventSource') == 'aws:s3':
                result = process_s3_record(record, context)
                results.append(result)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Successfully processed S3 events',
                'results': results
            })
        }

    except Exception as e:
        logger.error(f"Error processing event: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def process_s3_record(record: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    単一のS3レコードを処理してAgentCore Runtimeを呼び出します。

    Args:
        record: S3イベントレコード
        context: Lambdaコンテキストオブジェクト

    Returns:
        処理結果を含む辞書
    """
    # S3バケットとオブジェクト情報を抽出
    s3_info = record.get('s3', {})
    bucket_name = s3_info.get('bucket', {}).get('name')
    object_key = s3_info.get('object', {}).get('key')
    event_name = record.get('eventName')

    logger.info(f"Processing S3 event: {event_name} - s3://{bucket_name}/{object_key}")

    # S3オブジェクトメタデータからuser-idを取得
    try:
        head_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        user_id = head_response.get('Metadata', {}).get('user-id', 'anonymous')
        logger.info(f"User ID from metadata: {user_id}")
    except ClientError as e:
        logger.warning(f"Could not get metadata for {bucket_name}/{object_key}: {e}")
        user_id = 'anonymous'

    # ファイルパスに基づいてセッションIDを作成
    session_id = f"{bucket_name}/{object_key}".replace('/', '_')

    # S3情報を含むエージェント用の入力ペイロードを作成
    input_payload = {
        "input": {
            "text": f"S3ファイルを処理してください: s3://{bucket_name}/{object_key}"
        },
        "s3_info": {
            "bucket": bucket_name,
            "key": object_key
        },
        "sessionId": session_id,
        "actorId": user_id
    }

    # AgentCore Runtimeを呼び出し
    try:
        response = invoke_agent_runtime(
            agent_runtime_arn=AGENT_RUNTIME_ARN,
            session_id=session_id,
            payload=input_payload
        )

        return {
            'bucket': bucket_name,
            'key': object_key,
            'event': event_name,
            'user_id': user_id,
            'agent_response': response,
            'session_id': session_id
        }

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        logger.error(f"AWS API error invoking agent: {error_code} - {error_message}")
        raise

    except Exception as e:
        logger.error(f"Error invoking agent for {bucket_name}/{object_key}: {str(e)}")
        raise


def invoke_agent_runtime(
    agent_runtime_arn: str,
    session_id: str,
    payload: Dict[str, Any]
) -> str:
    """
    AgentCore Runtimeを呼び出してレスポンスを処理します。

    Args:
        agent_runtime_arn: AgentCore RuntimeのARN
        session_id: 会話コンテキストのセッション識別子
        payload: エージェントに送信する入力ペイロード

    Returns:
        エージェントの完全なレスポンス（文字列）
    """
    logger.info(f"Invoking agent runtime: {agent_runtime_arn}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        # InvokeAgentRuntime APIを呼び出し
        response = bedrock_agentcore.invoke_agent_runtime(
            agentRuntimeArn=agent_runtime_arn,
            runtimeSessionId=session_id,
            payload=json.dumps(payload).encode('utf-8')
        )

        # ストリーミングレスポンスを処理
        event_stream = response.get('completion')
        complete_response = process_event_stream(event_stream)

        logger.info(f"Agent response: {complete_response[:500]}...")
        return complete_response

    except ClientError as e:
        logger.error(f"Error invoking agent runtime: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


def process_event_stream(event_stream) -> str:
    """
    AgentCore Runtimeからのストリーミングレスポンスを処理します。

    Args:
        event_stream: InvokeAgentRuntimeレスポンスのイベントストリーム

    Returns:
        完全なレスポンステキスト
    """
    response_parts = []

    try:
        for event in event_stream:
            # ストリーム内の異なるイベントタイプを処理
            if 'chunk' in event:
                chunk = event['chunk']

                # チャンクからテキストを抽出
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    response_parts.append(chunk_text)
                    logger.debug(f"Received chunk: {chunk_text}")

            elif 'trace' in event:
                # デバッグ用のトレースイベントを処理
                logger.debug(f"Trace event: {event['trace']}")

            elif 'internalServerException' in event:
                error = event['internalServerException']
                raise Exception(f"Internal server error: {error.get('message')}")

            elif 'validationException' in event:
                error = event['validationException']
                raise Exception(f"Validation error: {error.get('message')}")

            elif 'throttlingException' in event:
                error = event['throttlingException']
                raise Exception(f"Throttling error: {error.get('message')}")

    except Exception as e:
        logger.error(f"Error processing event stream: {e}")
        raise

    # すべてのレスポンスパーツを結合
    complete_response = ''.join(response_parts)
    return complete_response if complete_response else "No response from agent"
