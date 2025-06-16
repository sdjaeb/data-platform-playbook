# pyspark_jobs/mongo_processor.py
# This script demonstrates Apache Spark's ability to read semi-structured data
# directly from MongoDB, apply transformations (e.g., flatten nested fields,
# handle optional fields), and then write the processed data to a structured
# Delta Lake table in MinIO.

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, current_timestamp, lit
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, MapType

def create_spark_session(app_name):
    """
    Helper function to create a SparkSession with necessary configurations
    for Delta Lake, MinIO (S3-compatible), and MongoDB connectivity.
    Also includes Spline configuration for lineage tracking.
    """
    # IMPORTANT NOTE: The Spline agent JARs (spline-spark-agent-bundle_2.12-0.7.1.jar and
    # spline-agent-bundle-0.7.1.jar) need to be present in the Spark container's
    # `/opt/bitnami/spark/jars` directory. This is handled by the `spline_jars` volume
    # in `docker-compose.yml`. Ensure you have downloaded these JARs locally.
    return (SparkSession.builder
            .appName(app_name)
            .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.mongodb.spark:mongo-spark-connector_2.12:10.0.0")
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
            .config("spark.spline.log.level", "WARN")
            .config("spark.driver.extraJavaOptions", "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar")
            .getOrCreate())

if __name__ == "__main__":
    # Command-line arguments: MongoDB database name, MongoDB collection name, Delta output path
    # Example for financial events: docker exec -it spark-master spark-submit \
    #          --packages io.delta:delta-core_2.12:2.4.0,org.mongodb.spark:mongo-spark-connector_2.12:10.0.0 \
    #          --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
    #          --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
    #          --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    #          --conf spark.hadoop.fs.s3a.access.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.path.style.access=true \
    #          --conf spark.spline.producer.url=http://spline-rest:8080/producer \
    #          --conf spark.spline.mode=ENABLED \
    #          --driver-java-options "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar" \
    #          /opt/bitnami/spark/jobs/mongo_processor.py \
    #          my_data_platform_db financial_events s3a://curated-data-bucket/mongo_financial_events_curated
    #
    # Example for insurance claims: python mongo_processor.py dynamic_insurance_data claims s3a://curated-data-bucket/mongo_insurance_claims_curated
    if len(sys.argv) != 4:
        print("Usage: mongo_processor.py <mongo_db_name> <mongo_collection_name> <delta_output_path>")
        sys.exit(-1)

    mongo_db_name = sys.argv[1]
    mongo_collection_name = sys.argv[2]
    delta_output_path = sys.argv[3]

    spark = create_spark_session(f"MongoDBToDelta_{mongo_collection_name}")
    spark.sparkContext.setLogLevel("WARN")

    # MongoDB connection URI (use 'mongodb' service name in Docker Compose)
    # The credentials 'root'/'password' are for the admin database if not specified
    # The connection string can vary; using the recommended format for root user with authSource
    mongo_uri = "mongodb://root:password@mongodb:27017/?authSource=admin"

    # Read data from MongoDB
    print(f"Reading data from MongoDB: db={mongo_db_name}, collection={mongo_collection_name}")
    try:
        df_mongo = (spark.read.format("mongodb")
                    .option("spark.mongodb.input.uri", f"{mongo_uri}")
                    .option("database", mongo_db_name)
                    .option("collection", mongo_collection_name)
                    .load())
    except Exception as e:
        # IMPORTANT NOTE: For `mongo_processor.py` to work, you must first
        # insert some data into MongoDB manually as described in the "Highlighting MongoDB"
        # document (Basic Use Case). Spark cannot read from an empty/non-existent collection
        # without failing.
        print(f"Error reading from MongoDB. Ensure MongoDB is running and data exists. Error: {e}")
        spark.stop()
        sys.exit(-1)

    if df_mongo.count() == 0:
        print(f"No data found in MongoDB collection {mongo_collection_name}. Exiting.")
        spark.stop()
        sys.exit(0)

    print("Schema of data read from MongoDB:")
    df_mongo.printSchema()
    print("Sample data read from MongoDB:")
    df_mongo.show(5, truncate=False)

    # --- Example Transformation Logic based on collection name ---
    df_transformed = None
    if mongo_collection_name == "claims":
        print("Applying transformations for insurance claims data...")
        # Select relevant fields and flatten nested 'details' object
        # Also explode the 'damages' array to create one row per damage item
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
    elif mongo_collection_name == "financial_events":
        print("Applying transformations for financial events data...")
        # Select and rename fields. Handle optional fields by aliasing or using lit(None) if they might not exist.
        df_transformed = df_mongo.select(
            col("event_id"),
            col("type"),
            col("user_id"),
            col("timestamp"),
            col("ip_address"),
            col("status"),
            # Use .alias for renaming; if a column doesn't exist, it will become null.
            col("reason").alias("failure_reason"),
            col("attempts").alias("login_attempts"),
            current_timestamp().alias("processing_timestamp")
        )
    elif mongo_collection_name == "customer_profiles":
        print("Applying transformations for customer profiles data...")
        # Example of flattening a nested contact object and exploding addresses array
        df_transformed = df_mongo.select(
            col("customer_id"),
            col("name"),
            col("contact.email").alias("email"),
            col("contact.phone").alias("phone"),
            explode(col("addresses")).alias("address_details"), # Explode addresses array
            current_timestamp().alias("processing_timestamp")
        ).select(
            col("customer_id"),
            col("name"),
            col("email"),
            col("phone"),
            col("address_details.street").alias("address_street"),
            col("address_details.city").alias("address_city"),
            col("address_details.zip").alias("address_zip"),
            col("address_details.type").alias("address_type"),
            col("processing_timestamp")
        )
    else:
        print(f"No specific transformation defined for collection '{mongo_collection_name}'. Writing as is.")
        # If no specific transformation, just add a timestamp and write
        df_transformed = df_mongo.withColumn("processing_timestamp", current_timestamp())

    print("Schema after transformation:")
    df_transformed.printSchema()
    print("Sample transformed data:")
    df_transformed.show(5, truncate=False)

    # --- Write the processed data to Delta Lake in MinIO ---
    print(f"Writing transformed data to Delta Lake: {delta_output_path}")
    # Use "overwrite" mode for idempotency in batch processing.
    # "overwriteSchema" is useful during development for schema evolution.
    (df_transformed.write
     .format("delta")
     .mode("overwrite")
     .option("overwriteSchema", "true")
     .save(delta_output_path))

    print("Transformation and write to Delta Lake complete.")

    spark.stop()
