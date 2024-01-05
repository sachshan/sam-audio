import boto3
import os
from os import environ
import logging
import json
import sys
import subprocess
sys.path.append('/mnt/access')
from scipy.io import wavfile
import numpy as np

logger = logging.getLogger()
logger.setLevel(environ.get("LOGLEVEL", "INFO").upper())
s3_client = boto3.client('s3')
S3_BUCKET = 'audioholdbucket'
dynamodb_client = boto3.resource('dynamodb')

def insert_audio_status(s3_key):
    """
    Insert the filename to the AudioStatus dynamodb table

    :param filename: Name of the S3 object
    :return: True if successful, False otherwise
    """
    try:
        table = dynamodb_client.Table('AudioStatus')
        table.put_item(Item={'s3_key': s3_key, 'status': 'Processing'})
    except Exception as e:
        logger.info(f"Error inserting filename to AudioStatus table: {e}")
        return False

    return True

def lambda_handler(event, context):
    logger.info(f"Event: {event}")
    try:
        for record in event['Records']:
            message = json.loads(record['body'])
            for s3_record in message['Records']:
                s3_key = s3_record['s3']['object']['key']
                
                logger.info(f"Processing file: {s3_key}")

                input_audio_file_path = '/tmp/input_audio.wav'
                output_audio_file_path = '/tmp/output_audio.wav'

                #Download the audio file from S3 to the Lambda function's /tmp directory
                s3_client.download_file(S3_BUCKET, s3_key, input_audio_file_path)

                #Conver the audio file to wav using ffmpeg
                subprocess.run(['/mnt/access/ffmpeg', '-i', input_audio_file_path, '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '2', output_audio_file_path])

                # Upload the processed audio file to S3
                orginal_key = s3_key
                s3_key = s3_key.split('/')[1]
                output_s3_key = f'processed/{s3_key}'  # Modify the path as needed
                s3_client.upload_file(output_audio_file_path, S3_BUCKET, output_s3_key)

                # Insert the filename to the AudioStatus table
                insert_audio_status(orginal_key)
                logger.info(f"Processed file uploaded to S3: {output_s3_key}")

                s3_client.delete_object(Bucket=S3_BUCKET, Key=orginal_key)
    
    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }