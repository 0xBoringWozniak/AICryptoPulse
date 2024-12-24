import os
import boto3


AWS_S3_API_KEY = os.getenv("AWS_S3_API_KEY")
AWS_S3_API_SECRET = os.getenv("AWS_S3_API_SECRET")

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_S3_API_KEY,
    aws_secret_access_key=AWS_S3_API_SECRET,
)