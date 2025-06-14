# Description: PySpark script for streaming ETL from Kafka to Delta Lake.
# Source: Highlighting Apache Spark, Basic Use Case; Highlighting Delta Lake, Basic Use Case.
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StringType, FloatType, TimestampType, BooleanType, MapType

def create_spark_session(app_name):
    """Helper function to create a SparkSession with Delta Lake and Kafka packages."""
    return (SparkSession.builder.appName(app_name)
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,io.delta:delta-core_2.12:2.4.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate())

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: streaming_consumer.py <kafka_topic> <kafka_broker> <delta_output_path>")
        sys.exit(-1)

    kafka_topic = sys.argv[1]
    kafka_broker = sys.argv[2]
    delta_output_path = sys.argv[3]

    spark = create_spark_session(f"KafkaToDeltaStream_{kafka_topic}")
    spark.sparkContext.setLogLevel("WARN") # Reduce verbosity of Spark logs

    # Define schema for the incoming Kafka message value (financial/insurance data)
    # This schema should match the data structure produced by FastAPI
    # For simplicity, using a combined schema, in reality you'd have specific ones
    # for financial_transactions and insurance_claims if strict
    data_schema = StructType() \
        .add("transaction_id", StringType(), True) \
        .add("timestamp", StringType(), True) \
        .add("account_id", StringType(), True) \
        .add("amount", FloatType(), True) \
        .add("currency", StringType(), True) \
        .add("transaction_type", StringType(), True) \
        .add("merchant_id", StringType(), True) \
        .add("category", StringType(), True) \
        .add("is_flagged", BooleanType(), True) \
        .add("claim_id", StringType(), True) \
        .add("policy_number", StringType(), True) \
        .add("claim_amount", FloatType(), True) \
        .add("claim_type", StringType(), True) \
        .add("claim_status", StringType(), True) \
        .add("customer_id", StringType(), True) \
        .add("incident_date", StringType(), True)

    # Read from Kafka as a streaming DataFrame
    kafka_df = (spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", kafka_broker)
                .option("subscribe", kafka_topic)
                .option("startingOffsets", "latest") # Start consuming new messages
                .load())

    # Parse the value column (which contains the JSON message)
    # Add metadata for debugging (topic, offset, timestamp)
    parsed_df = kafka_df.selectExpr("CAST(key AS STRING)", "CAST(value AS STRING) as json_value",
                                    "topic", "partition", "offset", "timestamp") \
        .select(from_json(col("json_value"), data_schema).alias("data"),
                col("topic"), col("partition"), col("offset"), col("timestamp").alias("kafka_timestamp")) \
        .select("data.*", "topic", "partition", "offset", "kafka_timestamp")

    # Define checkpoint location for fault tolerance and exactly-once processing
    checkpoint_location = f"{delta_output_path}/_checkpoints"

    # Write the processed data to Delta Lake
    query = (parsed_df.writeStream
             .format("delta")
             .outputMode("append") # Append new data to the Delta table
             .option("checkpointLocation", checkpoint_location) # Required for streaming writes
             .option("mergeSchema", "true") # Enable schema evolution (from Delta Lake Adv Use Case 1)
             .start(delta_output_path))

    print(f"Spark Structured Streaming job for topic '{kafka_topic}' started, writing to: {delta_output_path}")
    print(f"Checkpoint location: {checkpoint_location}")

    query.awaitTermination() # Keep the job running until terminated
    spark.stop()