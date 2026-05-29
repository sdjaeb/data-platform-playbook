import asyncio
import json
import os
import uuid
from datetime import datetime
from aiokafka import AIOKafkaConsumer
import boto3
from botocore.client import Config

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC = "raw-sboms"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = "minioadmin"
MINIO_SECRET_KEY = "minioadmin"
BUCKET_NAME = "bronze"

s3 = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version='s3v4')
)

async def consume():
    consumer = AIOKafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id="bronze-consumer-group",
        auto_offset_reset='earliest'
    )
    await consumer.start()
    
    # Ensure bucket exists
    try:
        s3.create_bucket(Bucket=BUCKET_NAME)
    except Exception:
        pass

    try:
        async for msg in consumer:
            data = json.loads(msg.value.decode("utf-8"))
            cid = data.get("cid")
            request_id = data.get("request_id", str(uuid.uuid4()))
            
            # Path: data/minio/bronze/sboms/cid.json
            local_dir = "data/minio/bronze/sboms"
            os.makedirs(local_dir, exist_ok=True)
            
            if cid:
                path = f"{local_dir}/{cid}.json"
            else:
                now = datetime.now()
                path = f"{local_dir}/legacy_{now.strftime('%Y%m%d_%H%M%S')}_{request_id}.json"
            
            # Check if CID already exists
            if os.path.exists(path):
                print(f"⏩ CID {cid} already exists. Skipping write.")
                continue
            
            # Write raw JSON to local disk
            with open(path, "w") as f:
                json.dump(data, f)
            
            print(f"💾 Stored {path} on disk")
            
    finally:
        await consumer.stop()

if __name__ == "__main__":
    asyncio.run(consume())
