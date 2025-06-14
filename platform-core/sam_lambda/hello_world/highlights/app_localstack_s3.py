# Description: AWS Lambda function interacting with S3 via LocalStack.
# Source: Highlighting AWS SAM CLI, Advanced Use Case 1.
import json
import os
import boto3
from datetime import datetime

# Configure S3 client to point to LocalStack
# This environment variable will be passed during `sam local invoke` or set in Lambda env
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL", "http://localstack:4566") # Default to localstack service name
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "my-local-data-bucket")

# Using 'minioadmin' for localstack for consistency with MinIO setup if needed,
# though LocalStack typically doesn't require explicit credentials if policies allow.
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "test")

s3_client = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name='us-east-1' # LocalStack is region-agnostic but a region is needed for boto3
)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event, indent=2))
    bucket_name = S3_BUCKET_NAME
    object_key = f"processed-data/{context.aws_request_id}.json" # Use AWS request ID for unique key

    try:
        input_data = {}
        if 'body' in event and isinstance(event['body'], str):
            input_data = json.loads(event['body'])
        else:
            input_data = event

        # Simulate a lightweight transformation: add a processing timestamp
        if isinstance(input_data, dict):
            input_data['processed_timestamp'] = datetime.utcnow().isoformat() + 'Z'
        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": "Invalid input data format for processing."}),
                "headers": {"Content-Type": "application/json"}
            }

        # Create bucket if it doesn't exist (LocalStack convenience)
        # Note: In production, buckets should be pre-provisioned via IaC.
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"Bucket {bucket_name} already exists.")
        except s3_client.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                print(f"Bucket {bucket_name} does not exist, creating...")
                s3_client.create_bucket(Bucket=bucket_name) # LocationConstraint might be needed for non-us-east-1
                print(f"Bucket {bucket_name} created.")
            else:
                raise # Re-raise other errors

        # Write processed data to S3
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=json.dumps(input_data).encode('utf-8')
        )
        print(f"Object written to s3://{bucket_name}/{object_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Data processed and stored in S3://{bucket_name}/{object_key}",
                "processed_data": input_data
            }),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    except json.JSONDecodeError:
        print("Error: Invalid JSON in event body.")
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "Invalid JSON input"}),
            "headers": {
                "Content-Type": "application/json"
            }
        }
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal server error: {e}"}),
            "headers": {
                "Content-Type": "application/json"
            }
        }