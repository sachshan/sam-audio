# sam-app

![alt text](https://github.com/sachshan/sam-audio/blob/master/architecture.drawio.svg)

This project contains source code and supporting files for a serverless application that you can deploy with the SAM CLI. The application can tag the uploaded audio with 521 possible tags. 

It includes the following files and folders.

- app - Code for the application's Lambda function.
- events - Invocation events that you can use to invoke the function.
- tests - Unit tests for the application code. 
- template.yaml - A template that defines the application's AWS resources.


The application is designed to tag audio files with their respective genres. The application utilizes various AWS services to create a serverless architecture for efficient audio processing and tag prediction.

Key components of the application include an API Gateway named "AudioUploadApi" with CORS support, facilitating endpoints for uploading audio files, checking audio status, and performing health checks. 

"AudioUploadFunction" created a file name and saves it in the AudioStatus DynamoDB table. It then request the AudioHoldBucket for a presigned url to put an audio file, which it returns to the user.  AudioStatusFunction interact request the AudioStatus DynamoDB table, to return the current status of the Audio and tags.

Two critical Lambda functions, "AudioProcessFunction" and "AudioPredictFunction," leverage AWS Elastic File System (EFS) to process audio files. AudioProcessFunction uses a FFMPEG layer to convert the audio files to wav files at 16KHZ. AudioPredictFunction employs the YAMNET model for predicting audio genres, respectively. These functions are triggered by SQS queues, ensuring scalability and fault tolerance. Additionally, dead-letter queues are configured to handle failed message processing gracefully.

IAM roles with specific permissions are assigned to Lambda functions, enabling them to access S3, DynamoDB, EFS, SQS, and CloudWatch Logs securely. The application is designed to provide a comprehensive solution for tagging audio files in a serverless and scalable manner.

