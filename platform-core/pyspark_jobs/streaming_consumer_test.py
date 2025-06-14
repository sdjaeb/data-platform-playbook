# Description: Simplified PySpark streaming consumer for integration tests.
# Source: Deep-Dive Addendum: IaC & CI/CD Recipes, Section 5.4 (context of test_data_flow.py).
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import StructType, StringType, FloatType, TimestampType, MapType, BooleanType

def create_spark_session(app_name):
    """Helper function to create a SparkSession with Delta Lake and Kafka packages."""
    return (SparkSession.builder.appName(app_name)
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,io.delta:delta-core_2.12:2.4.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate())

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: streaming_consumer_test.py <kafka_topic> <kafka_broker> <delta_output_path>")
        sys.exit(-1)

    kafka_topic = sys.argv[1]
    kafka_broker = sys.argv[2]
    delta_output_path = sys.argv[3]

    spark = create_spark_session("KafkaToDeltaTest")
    spark.sparkContext.setLogLevel("WARN")

    # Define schema for the incoming Kafka message value (adjust as per your FastAPI data)
    # This should broadly match the data sent by FastAPI for financial transactions in integration tests.
    schema = StructType() \
        .add("transaction_id", StringType()) \
        .add("timestamp", StringType()) \
        .add("account_id", StringType()) \
        .add("amount", FloatType()) \
        .add("currency", StringType()) \
        .add("transaction_type", StringType()) \
        .add("merchant_id", StringType(), True) \
        .add("category", StringType(), True) \
        .add("is_flagged", BooleanType(), True) # Add this if your test data includes it

    # Read from Kafka
    kafka_df = (spark.readStream
                .format("kafka")
                .option("kafka.bootstrap.servers", kafka_broker)
                .option("subscribe", kafka_topic)
                .option("startingOffsets", "earliest") # Start from earliest for integration tests
                .load())

    # Parse the value column from Kafka
    parsed_df = kafka_df.selectExpr("CAST(value AS STRING) as json_value") \
        .select(from_json(col("json_value"), schema).alias("data")) \
        .select("data.*")

    # Write to Delta Lake
    query = (parsed_df.writeStream
             .format("delta")
             .outputMode("append")
             .option("checkpointLocation", f"{delta_output_path}/_checkpoints")
             .option("mergeSchema", "true") # Enable schema merging for tests
             .start(delta_output_path))

    # Run for a short period to capture test data
    print(f"Spark streaming test job running for {30} seconds to ingest data to {delta_output_path}...")
    query.awaitTermination(30) # Run for 30 seconds to capture test data
    query.stop()
    print("Spark streaming test job stopped.")
    spark.stop()