# Description: PySpark script to read from MongoDB, transform, and write to Delta Lake.
# Source: Highlighting MongoDB, Advanced Use Case 2.
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, current_timestamp

def create_spark_session(app_name):
    """Helper function to create a SparkSession with Delta Lake and MongoDB packages."""
    return (SparkSession.builder.appName(app_name)
            .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.mongodb.spark:mongo-spark-connector_2.12:10.0.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate())

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: mongo_processor.py <mongo_db_name> <mongo_collection_name> <delta_output_path>")
        sys.exit(-1)

    mongo_db_name = sys.argv[1]
    mongo_collection_name = sys.argv[2]
    delta_output_path = sys.argv[3]

    spark = create_spark_session(f"MongoDBToDelta_{mongo_collection_name}")
    spark.sparkContext.setLogLevel("WARN")

    # MongoDB connection URI (use 'mongodb' service name in Docker Compose)
    mongo_uri = "mongodb://root:password@mongodb:27017/"

    # Read data from MongoDB
    print(f"Reading data from MongoDB: db={mongo_db_name}, collection={mongo_collection_name}")
    df_mongo = (spark.read.format("mongodb")
                .option("spark.mongodb.input.uri", f"{mongo_uri}{mongo_db_name}.{mongo_collection_name}")
                .load())

    print("Schema of data read from MongoDB:")
    df_mongo.printSchema()
    df_mongo.show(5, truncate=False)

    # --- Example Transformation: Flattening nested 'details' and 'attachments' for 'claims' ---
    # Assuming the 'claims' collection with nested structures
    if mongo_collection_name == "claims":
        print("Applying transformations for claims data...")
        # Select relevant fields and flatten nested 'details' object
        df_transformed = df_mongo.select(
            col("claim_id"),
            col("policy_id"),
            col("claim_date"),
            col("status"),
            col("details.type").alias("claim_type"),
            col("details.incident_date").alias("incident_date"),
            col("details.vehicle_vin").alias("vehicle_vin"),
            explode(col("details.damages")).alias("damage_item"), # Explode damages array
            current_timestamp().alias("processing_timestamp")
        )
        print("Schema after flattening:")
        df_transformed.printSchema()
        df_transformed.show(5, truncate=False)

    elif mongo_collection_name == "financial_events":
        print("Applying transformations for financial events data...")
        df_transformed = df_mongo.select(
            col("event_id"),
            col("type"),
            col("user_id"),
            col("timestamp"),
            col("ip_address"),
            col("status"),
            col("reason").alias("failure_reason"), # Handle optional field
            col("attempts").alias("login_attempts"), # Handle optional field
            current_timestamp().alias("processing_timestamp")
        )
        print("Schema after selecting/renaming:")
        df_transformed.printSchema()
        df_transformed.show(5, truncate=False)
    else:
        print("No specific transformation defined for this collection. Writing as is.")
        df_transformed = df_mongo.withColumn("processing_timestamp", current_timestamp())


    # Write the processed data to Delta Lake in MinIO
    print(f"Writing transformed data to Delta Lake: {delta_output_path}")
    df_transformed.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(delta_output_path)
    print("Transformation and write to Delta Lake complete.")

    spark.stop()