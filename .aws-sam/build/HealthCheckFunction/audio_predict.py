import boto3
import os
import logging
import json
import sys
import csv
sys.path.append('/mnt/access')
import numpy as np
import tensorflow as tf
from scipy.io import wavfile

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOGLEVEL", "INFO").upper())
s3_client = boto3.client('s3')
dynamodb_client = boto3.resource('dynamodb')
S3_BUCKET = 'audioholdbucket'

def load_yamnet_model(model_path):
    return tf.saved_model.load(model_path)

def class_names_from_csv(class_map_csv_text):
  """Returns list of class names corresponding to score vector."""
  class_names = []
  with tf.io.gfile.GFile(class_map_csv_text) as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
      class_names.append(row['display_name'])

  return class_names

def insert_audio_status(s3_key, class1, class2):
    """
    Insert the filename to the AudioStatus dynamodb table

    :param filename: Name of the S3 object
    :return: True if successful, False otherwise
    """
    try:
        table = dynamodb_client.Table('AudioStatus')
        table.put_item(Item={'s3_key': s3_key, 'status':"Predicted", 'iclass1': class1, 'iclass2': class2})
    except Exception as e:
        logger.info(f"Error inserting filename to AudioStatus table: {e}")
        return False
    
    return True

def lambda_handler(event, context):
    logger.info(f"Event: {event}")
    
    try:
        # Specify the path to the YAMNet model
        yamnet_model_path = '/mnt/access/yamnet_model'
        
        # Load the YAMNet model
        yamnet_model = load_yamnet_model(yamnet_model_path)

        for record in event['Records']:
            message = json.loads(record['body'])
            for s3_record in message['Records']:
                s3_key = s3_record['s3']['object']['key']
                
                logger.info(f"Processing file: {s3_key}")

                input_audio_file_path = '/tmp/input_audio.wav'

                #Download the audio file from S3 to the Lambda function's /tmp directory
                s3_client.download_file(S3_BUCKET, s3_key, input_audio_file_path)

                # Load the NPY file
                sample_rate, wav_data = wavfile.read(input_audio_file_path, 'rb')
                wav_data = np.mean(wav_data, axis=1)
                logger.info(f"Sample rate: {sample_rate}")

                # Normalize the audio data
                waveform = wav_data / tf.int16.max

                class_map_path = yamnet_model.class_map_path().numpy()
                class_names = class_names_from_csv(class_map_path)

                # Classify the audio using YAMNet
                scores, embeddings, spectrogram = yamnet_model(waveform)

                # Process the YAMNet output as needed
                # Example: Print the top 3 detected labels
                scores_np = scores.numpy()
                infered_class = class_names[scores_np.mean(axis=0).argmax()]
                inferred_class_two = class_names[scores_np.mean(axis=0).argsort()[-2]]
                logger.info(f'The main sounds are: {infered_class} {inferred_class_two}')

                s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

                # Insert the filename to the AudioStatus table with the predicted genre
                s3_key = s3_key.split('/')[1]
                insert_audio_status(f"uploadedAudio/{s3_key}", infered_class, inferred_class_two)

                

    except Exception as e:
        logger.error(f"Error in lambda_handler: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }