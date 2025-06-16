# pyspark_jobs/streaming_consumer.py
# This script demonstrates Spark Structured Streaming consuming real-time data from Kafka topics,
# parsing JSON messages, applying a basic schema, and writing the results to a Delta Lake table in MinIO.

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType, FloatType

# Define schemas for incoming Kafka messages.
# These schemas correspond to the JSON structure of messages produced by the FastAPI ingestor.

# Schema for financial transactions
financial_transaction_schema = StructType([
    StructField("transaction_id", StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("account_id", StringType(), True),
    StructField("amount", DoubleType(), True),
    StructField("currency", StringType(), True),
    StructField("transaction_type", StringType(), True),
    StructField("merchant_id", StringType(), True),
    StructField("category", StringType(), True),
])

# Schema for insurance claims
insurance_claim_schema = StructType([
    StructField("claim_id", StringType(), True),
    StructField("timestamp", TimestampType(), True),
    StructField("policy_number", StringType(), True),
    StructField("claim_amount", DoubleType(), True),
    StructField("claim_type", StringType(), True),
    StructField("claim_status", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("incident_date", TimestampType(), True),
])


def create_spark_session(app_name):
    """
    Helper function to create a SparkSession with necessary configurations
    for Kafka, Delta Lake, and MinIO (S3-compatible) connectivity.
    Also includes Spline configuration for lineage tracking.
    """
    # IMPORTANT NOTE: The Spline agent JARs (spline-spark-agent-bundle_2.12-0.7.1.jar and
    # spline-agent-bundle-0.7.1.jar) need to be present in the Spark container's
    # `/opt/bitnami/spark/jars` directory. This is handled by the `spline_jars` volume
    # in `docker-compose.yml`. Ensure you have downloaded these JARs locally.
    return (SparkSession.builder
            .appName(app_name)
            .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            # MinIO (S3-compatible) configuration
            .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") # MinIO service name in Docker Compose
            .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
            .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            # Spline configuration for lineage tracking
            # IMPORTANT NOTE: The `spline-rest` service is mapped to port 8083 externally,
            # but internally it listens on 8080. Use the internal port for inter-container communication.
            .config("spark.spline.producer.url", "http://spline-rest:8080/producer")
            .config("spark.spline.mode", "ENABLED")
            .config("spark.spline.log.level", "WARN") # Reduce verbose logging
            # IMPORTANT NOTE: This Java agent path assumes spline-agent-bundle-0.7.1.jar is in /opt/bitnami/spark/jars
            .config("spark.driver.extraJavaOptions", "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar")
            .getOrCreate())

def process_stream(spark, kafka_topic, kafka_broker, delta_output_path, schema, data_type):
    """
    Sets up and processes a Spark Structured Stream from a Kafka topic to a Delta Lake table.
    """
    print(f"Starting Spark Structured Streaming for {data_type} from Kafka topic: {kafka_topic}")
    print(f"Writing to Delta Lake path: {delta_output_path}")

    # Read from Kafka topic
    # Spark will infer the Kafka message structure (key, value, topic, partition, offset, timestamp)
    df_raw = (spark.readStream
              .format("kafka")
              .option("kafka.bootstrap.servers", kafka_broker)
              .option("subscribe", kafka_topic)
              .option("startingOffsets", "earliest") # Start reading from the beginning of the topic
              .load())

    # Parse the JSON 'value' column into structured data using the defined schema
    # Add a processing timestamp for auditing
    df_parsed = df_raw.selectExpr("CAST(value AS STRING) as json_data") \
                      .withColumn("data", from_json(col("json_data"), schema)) \
                      .select("data.*") \
                      .withColumn("processing_timestamp", current_timestamp())

    # Write the processed data to Delta Lake in append mode.
    # The 'checkpointLocation' is crucial for fault tolerance and exactly-once processing.
    # 'mergeSchema' allows schema evolution in Delta Lake.
    query = (df_parsed.writeStream
             .format("delta")
             .outputMode("append") # Append new data to the Delta table
             .option("checkpointLocation", f"{delta_output_path}/_checkpoint")
             .option("mergeSchema", "true") # Allow schema evolution
             .trigger(processingTime="10 seconds") # Process data every 10 seconds
             .start(delta_output_path)) # Start the streaming query

    return query


if __name__ == "__main__":
    # Command-line arguments: Kafka topic, Kafka broker, Delta output path
    # Example: docker exec -it spark-master spark-submit \
    #          --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,io.delta:delta-core_2.12:2.4.0 \
    #          --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
    #          --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
    #          --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    #          --conf spark.hadoop.fs.s3a.access.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.path.style.access=true \
    #          --conf spark.spline.producer.url=http://spline-rest:8080/producer \
    #          --conf spark.spline.mode=ENABLED \
    #          --driver-java-options "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar" \
    #          /opt/bitnami/spark/jobs/streaming_consumer.py \
    #          raw_financial_transactions kafka:29092 s3a://raw-data-bucket/financial_data_delta
    #
    # To run this from your host (assuming `spark-master` is the Spark container name):
    # docker exec -it spark-master spark-submit --packages ... /opt/bitnami/spark/jobs/streaming_consumer.py raw_financial_transactions kafka:29092 s3a://raw-data-bucket/financial_data_delta

    if len(sys.argv) != 4:
        print("Usage: streaming_consumer.py <kafka_topic> <kafka_broker> <delta_output_path>")
        sys.exit(-1)

    kafka_topic_name = sys.argv[1]
    kafka_broker_address = sys.argv[2]
    delta_output_location = sys.argv[3]

    spark = create_spark_session("KafkaToDeltaStream")
    spark.sparkContext.setLogLevel("WARN") # Set Spark logging level to WARN to reduce verbosity

    # Determine which schema to use based on the topic name
    if "financial" in kafka_topic_name:
        schema_to_use = financial_transaction_schema
        data_type_name = "Financial Transactions"
    elif "insurance" in kafka_topic_name:
        schema_to_use = insurance_claim_schema
        data_type_name = "Insurance Claims"
    else:
        print(f"Unknown Kafka topic: {kafka_topic_name}. Cannot determine schema.")
        sys.exit(-1)

    # Start the streaming process
    streaming_query = process_stream(
        spark,
        kafka_topic_name,
        kafka_broker_address,
        delta_output_location,
        schema_to_use,
        data_type_name
    )

    # Await termination of the streaming query to keep the application alive
    # until it's manually stopped (e.g., via Ctrl+C).
    print(f"Streaming query for {data_type_name} started. Press Ctrl+C to stop.")
    try:
        streaming_query.awaitTermination()
    except KeyboardInterrupt:
        print("Streaming query interrupted. Shutting down Spark.")
        streaming_query.stop()
        spark.stop()

