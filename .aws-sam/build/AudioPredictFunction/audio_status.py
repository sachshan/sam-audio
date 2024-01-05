import json
import logging
from os import environ
import boto3

# import requests

logger = logging.getLogger()
logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')

def retrieve_audio_status(s3_key):
    """
    Retrieve the status of the audio file from the AudioStatus dynamodb table

    :param s3_key: Name of the S3 object
    :return: Status of the audio file
    """
    try:
        table = dynamodb_client.Table('AudioStatus')
        response = table.get_item(Key={'s3_key': s3_key})
    except Exception as e:
        logger.info(f"Error retrieving status from AudioStatus table: {e}")
        return None

    return response.get('Item', {}).get('status'), response.get('Item', {}).get('iclass1'), response.get('Item', {}).get('iclass2')

def lambda_handler(event, context):
    logger.info(f"Event: {event}")

    try:
        # Get the s3_key from the query parameters
        s3_key = event.get('queryStringParameters', {}).get('s3_key')

        if not s3_key:
            logger.info("s3_key not provided in query parameters.")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 's3_key not provided'})
            }

        # Retrieve the status from DynamoDB
        status, iclass1, iclass2 = retrieve_audio_status(s3_key)

        if status is not None:
            logger.info(f"Status for s3_key {s3_key}: {iclass1}, {iclass2}")
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'iclass1': iclass1, 'iclass2': iclass2, 'status': status})
            }
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': 'Status not found for the given s3_key'})
            }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }

    

