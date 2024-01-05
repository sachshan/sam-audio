import json
import logging
from os import environ
import boto3
import uuid
# import requests

logger = logging.getLogger()
logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')

def generate_presigned_url(bucket_name, object_key, expiration=3600):
    """
    Generate a presigned URL for S3 object upload

    :param bucket_name: Name of the S3 bucket
    :param object_name: Name of the object within the bucket
    :param expiration: Time in seconds for the URL to remain valid (default is 1 hour)
    :return: Presigned URL as a string. If error, returns None.
    """
    try:
        response = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_key},
            ExpiresIn=expiration
        )
    except Exception as e:
        logger.info(f"Error generating presigned URL: {e}")
        return None

    return response

def insert_audio_status(s3_key):
    """
    Insert the filename to the AudioStatus dynamodb table

    :param filename: Name of the S3 object
    :return: True if successful, False otherwise
    """
    try:
        table = dynamodb_client.Table('AudioStatus')
        table.put_item(Item={'s3_key': s3_key, 'status': 'Uploading'})
    except Exception as e:
        logger.info(f"Error inserting filename to AudioStatus table: {e}")
        return False

    return True

def table_exists(table_name):
    existing_tables = dynamodb_client.list_tables()['TableNames']
    return table_name in existing_tables

def lambda_handler(event, context):
    logger.info(f"Event: {event}")
    
    s3_bucket = 'audioholdbucket'
    key_prefix = 'uploadedAudio'
    unique_filename = str(uuid.uuid4())
    s3_key = f"{key_prefix}/{unique_filename}.wav"

    # Insert the filename to the AudioStatus dynamodb table
    if not insert_audio_status(s3_key):
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to insert filename to AudioStatus table'})
        }
    else:
        logger.info(f"Successfully inserted filename to AudioStatus table: {s3_key}")

    # Generate a presigned URL
    presigned_url = generate_presigned_url(s3_bucket, s3_key)
    
    if presigned_url:
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'presigned_url': presigned_url,
                's3_key': s3_key
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Failed to generate presigned URL'})
        }
