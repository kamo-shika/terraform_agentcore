"""
Lambda function to invoke AgentCore Runtime when S3 events are received.

This function:
1. Receives S3 event notifications
2. Extracts bucket and object key information
3. Retrieves user-id from S3 object metadata
4. Invokes AgentCore Runtime with the S3 object details
5. Processes the streaming response from the agent
"""

import json
import os
import logging
from typing import Dict, Any
import boto3
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3_client = boto3.client('s3')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime')

# Environment variables
AGENT_RUNTIME_ARN = os.environ.get('AGENT_RUNTIME_ARN')
AGENTCORE_MEMORY_ID = os.environ.get('AGENTCORE_MEMORY_ID')


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler function that processes S3 events and invokes AgentCore Runtime.

    Args:
        event: S3 event notification
        context: Lambda context object

    Returns:
        Dict containing status and response details
    """
    logger.info(f"Received event: {json.dumps(event)}")

    # Validate environment variables
    if not AGENT_RUNTIME_ARN:
        error_msg = "AGENT_RUNTIME_ARN environment variable is not set"
        logger.error(error_msg)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': error_msg})
        }

    try:
        # Process each S3 record in the event
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
    Process a single S3 record and invoke AgentCore Runtime.

    Args:
        record: S3 event record
        context: Lambda context object

    Returns:
        Dict containing processing results
    """
    # Extract S3 bucket and object information
    s3_info = record.get('s3', {})
    bucket_name = s3_info.get('bucket', {}).get('name')
    object_key = s3_info.get('object', {}).get('key')
    event_name = record.get('eventName')

    logger.info(f"Processing S3 event: {event_name} - s3://{bucket_name}/{object_key}")

    # Get S3 object metadata to extract user-id
    try:
        head_response = s3_client.head_object(Bucket=bucket_name, Key=object_key)
        user_id = head_response.get('Metadata', {}).get('user-id', 'anonymous')
        logger.info(f"User ID from metadata: {user_id}")
    except ClientError as e:
        logger.warning(f"Could not get metadata for {bucket_name}/{object_key}: {e}")
        user_id = 'anonymous'

    # Create session ID based on file path
    session_id = f"{bucket_name}/{object_key}".replace('/', '_')

    # Create input payload for the agent with S3 info
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

    # Invoke AgentCore Runtime
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
    Invoke AgentCore Runtime and process the response.

    Args:
        agent_runtime_arn: ARN of the AgentCore Runtime
        session_id: Session identifier for conversation context
        payload: Input payload to send to the agent

    Returns:
        Complete agent response as string
    """
    logger.info(f"Invoking agent runtime: {agent_runtime_arn}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Payload: {json.dumps(payload)}")

    try:
        # Call InvokeAgentRuntime API
        response = bedrock_agent_runtime.invoke_agent_runtime(
            agentRuntimeArn=agent_runtime_arn,
            sessionId=session_id,
            inputPayload=json.dumps(payload).encode('utf-8')
        )

        # Process streaming response
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
    Process the streaming response from AgentCore Runtime.

    Args:
        event_stream: Event stream from InvokeAgentRuntime response

    Returns:
        Complete response text
    """
    response_parts = []

    try:
        for event in event_stream:
            # Handle different event types in the stream
            if 'chunk' in event:
                chunk = event['chunk']

                # Extract text from chunk
                if 'bytes' in chunk:
                    chunk_text = chunk['bytes'].decode('utf-8')
                    response_parts.append(chunk_text)
                    logger.debug(f"Received chunk: {chunk_text}")

            elif 'trace' in event:
                # Handle trace events for debugging
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

    # Combine all response parts
    complete_response = ''.join(response_parts)
    return complete_response if complete_response else "No response from agent"
