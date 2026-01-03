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
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional
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
OUTPUT_BUCKET = os.environ.get('OUTPUT_BUCKET')


def sanitize_session_id(value: str) -> str:
    """
    sessionIdをAgentCore Memory APIの正規表現パターンに準拠させる。

    パターン: [a-zA-Z0-9][a-zA-Z0-9-_]*
    - 最初の文字は英数字
    - 以降は英数字、ハイフン、アンダースコアのみ

    Args:
        value: 元のsessionId

    Returns:
        サニタイズされたsessionId
    """
    # 許可されていない文字をアンダースコアに置換
    sanitized = re.sub(r'[^a-zA-Z0-9-_]', '_', value)
    # 最初の文字が英数字でない場合、プレフィックスを追加
    if sanitized and not sanitized[0].isalnum():
        sanitized = 's' + sanitized
    return sanitized or 'session'


def sanitize_actor_id(value: str) -> str:
    """
    actorIdをAgentCore Memory APIの正規表現パターンに準拠させる。

    パターン: [a-zA-Z0-9][a-zA-Z0-9-_/]*(?::[a-zA-Z0-9-_/]+)*[a-zA-Z0-9-_/]*
    - 最初の文字は英数字
    - 以降は英数字、ハイフン、アンダースコア、スラッシュ

    Args:
        value: 元のactorId

    Returns:
        サニタイズされたactorId
    """
    # 許可されていない文字をアンダースコアに置換
    sanitized = re.sub(r'[^a-zA-Z0-9-_/:]', '_', value)
    # 最初の文字が英数字でない場合、プレフィックスを追加
    if sanitized and not sanitized[0].isalnum():
        sanitized = 'u' + sanitized
    return sanitized or 'anonymous'


def save_response_to_s3(
    bucket_name: str,
    object_key: str,
    session_id: str,
    actor_id: str,
    input_text: str,
    response_text: str
) -> Optional[str]:
    """
    エージェントの応答をS3に保存する。

    Args:
        bucket_name: 入力ファイルのバケット名
        object_key: 入力ファイルのオブジェクトキー
        session_id: セッションID
        actor_id: アクターID
        input_text: エージェントへの入力テキスト
        response_text: エージェントからの応答テキスト

    Returns:
        保存先のS3 URIまたはNone（保存に失敗した場合）
    """
    if not OUTPUT_BUCKET:
        logger.warning("OUTPUT_BUCKET is not set, skipping response save")
        return None

    try:
        # タイムスタンプを生成
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')

        # 出力ファイルのキーを生成
        # outputs/{timestamp}_{session_id}.json
        output_key = f"outputs/{timestamp}_{session_id}.json"

        # 保存するデータを構築
        output_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "actor_id": actor_id,
            "source": {
                "bucket": bucket_name,
                "key": object_key
            },
            "input": input_text,
            "response": response_text
        }

        # S3に保存
        s3_client.put_object(
            Bucket=OUTPUT_BUCKET,
            Key=output_key,
            Body=json.dumps(output_data, ensure_ascii=False, indent=2),
            ContentType='application/json'
        )

        output_uri = f"s3://{OUTPUT_BUCKET}/{output_key}"
        logger.info(f"Response saved to {output_uri}")
        return output_uri

    except ClientError as e:
        logger.error(f"Failed to save response to S3: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error saving response: {e}")
        return None


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

    # ファイルパスに基づいてセッションIDを作成（サニタイズ適用）
    raw_session_id = f"{bucket_name}/{object_key}".replace('/', '_')
    session_id = sanitize_session_id(raw_session_id)
    actor_id = sanitize_actor_id(user_id)

    logger.info(f"Sanitized IDs - sessionId: {session_id}, actorId: {actor_id}")

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
        "actorId": actor_id
    }

    # AgentCore Runtimeを呼び出し
    try:
        response = invoke_agent_runtime(
            agent_runtime_arn=AGENT_RUNTIME_ARN,
            session_id=session_id,
            payload=input_payload
        )

        # エージェント応答をS3に保存
        input_text = input_payload.get('input', {}).get('text', '')
        output_uri = save_response_to_s3(
            bucket_name=bucket_name,
            object_key=object_key,
            session_id=session_id,
            actor_id=actor_id,
            input_text=input_text,
            response_text=response
        )

        return {
            'bucket': bucket_name,
            'key': object_key,
            'event': event_name,
            'user_id': actor_id,
            'agent_response': response,
            'session_id': session_id,
            'output_uri': output_uri
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
        # AgentCore Runtimeは'response'フィールドを返す（'completion'ではない）
        event_stream = response.get('response')
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
    AgentCore RuntimeからのStreamingBodyレスポンスを処理します。

    Args:
        event_stream: InvokeAgentRuntimeレスポンスのStreamingBody

    Returns:
        完全なレスポンステキスト
    """
    try:
        # StreamingBodyからデータを読み取り
        response_data = event_stream.read()

        # バイトデータを文字列にデコード
        response_text = response_data.decode('utf-8')
        logger.debug(f"Received response: {response_text}")

        # JSONレスポンスをパース
        try:
            response_json = json.loads(response_text)
            # AgentCoreの標準レスポンス形式: {"response": "...", "status": "success"}
            if 'response' in response_json:
                return response_json['response']
            else:
                # JSONにresponseフィールドがない場合は、全体を返す
                return response_text
        except json.JSONDecodeError:
            # JSONパースに失敗した場合は、生のテキストを返す
            logger.warning("Response is not valid JSON, returning raw text")
            return response_text

    except Exception as e:
        logger.error(f"Error processing event stream: {e}")
        raise
