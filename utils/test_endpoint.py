from json import loads
from os import environ

import boto3
import requests

url = "https://7lkjqnzhph.execute-api.us-east-1.amazonaws.com/Prod/"
endpoint = "audio_upload"

header = {
    "body":"This is the body"
}

response = requests.post(f"{url}{endpoint}/", headers=header)
data = response.json()
print(data)