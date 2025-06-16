# pyspark_jobs/delta_merge_cdc.py
# This script demonstrates advanced Delta Lake capabilities for Spark:
# 1. Performing an UPSERT (UPDATE or INSERT) operation using MERGE INTO.
# 2. Reading Change Data Feed (CDF) for tracking data changes.
# This is crucial for maintaining slowly changing dimensions (SCD Type 2) or
# synchronizing data with other systems.

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_timestamp
from delta.tables import DeltaTable

def create_spark_session(app_name):
    """
    Helper function to create a SparkSession with necessary configurations
    for Delta Lake and MinIO (S3-compatible) connectivity.
    Also includes Spline configuration for lineage tracking.
    """
    # IMPORTANT NOTE: The Spline agent JARs (spline-spark-agent-bundle_2.12-0.7.1.jar and
    # spline-agent-bundle-0.7.1.jar) need to be present in the Spark container's
    # `/opt/bitnami/spark/jars` directory. This is handled by the `spline_jars` volume
    # in `docker-compose.yml`. Ensure you have downloaded these JARs locally.
    return (SparkSession.builder
            .appName(app_name)
            .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            # MinIO (S3-compatible) configuration
            .config("spark.hadoop.fs.s3a.endpoint", "http://minio:9000") # MinIO service name in Docker Compose
            .config("spark.hadoop.fs.s3a.access.key", "minioadmin")
            .config("spark.hadoop.fs.s3a.secret.key", "minioadmin")
            .config("spark.hadoop.fs.s3a.path.style.access", "true")
            # Enable Delta Lake Change Data Feed (CDF) for the session
            # IMPORTANT NOTE: CDF must be enabled on the table itself if it already exists,
            # using `ALTER TABLE table_name SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')`
            # or it needs to be enabled at creation. This config ensures new tables created
            # by this Spark session have CDF enabled by default.
            .config("spark.databricks.delta.properties.defaults.enableChangeDataFeed", "true")
            # Spline configuration for lineage tracking
            # IMPORTANT NOTE: The `spline-rest` service is mapped to port 8083 externally,
            # but internally it listens on 8080. Use the internal port for inter-container communication.
            .config("spark.spline.producer.url", "http://spline-rest:8080/producer")
            .config("spark.spline.mode", "ENABLED")
            .config("spark.spline.log.level", "WARN")
            .config("spark.driver.extraJavaOptions", "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar")
            .getOrCreate())

if __name__ == "__main__":
    # Command-line argument: Delta Lake table path for the dimension table
    # Example: docker exec -it spark-master spark-submit \
    #          --packages io.delta:delta-core_2.12:2.4.0 \
    #          --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
    #          --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
    #          --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    #          --conf spark.hadoop.fs.s3a.access.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.path.style.access=true \
    #          --conf spark.databricks.delta.properties.defaults.enableChangeDataFeed=true \
    #          --conf spark.spline.producer.url=http://spline-rest:8080/producer \
    #          --conf spark.spline.mode=ENABLED \
    #          --driver-java-options "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar" \
    #          /opt/bitnami/spark/jobs/delta_merge_cdc.py \
    #          s3a://curated-data-bucket/financial_transactions_dim
    if len(sys.argv) != 2:
        print("Usage: delta_merge_cdc.py <delta_table_path>")
        sys.exit(-1)

    delta_table_path = sys.argv[1]

    spark = create_spark_session("DeltaLakeMergeCDC")
    spark.sparkContext.setLogLevel("WARN")

    # --- 1. Initial Data Setup (if table doesn't exist) ---
    print(f"Ensuring Delta table exists at: {delta_table_path}")
    if not DeltaTable.isDeltaTable(spark, delta_table_path):
        print("Delta table does not exist. Creating with initial data.")
        initial_data = [
            ("T001", "ACC-001", 100.00, "USD", "purchase", "MER-ABC"),
            ("T002", "ACC-002", 200.00, "EUR", "sale", "MER-XYZ"),
            ("T003", "ACC-003", 50.00, "GBP", "refund", "MER-DEF")
        ]
        initial_df = spark.createDataFrame(initial_data, ["transaction_id", "account_id", "amount", "currency", "transaction_type", "merchant_id"]) \
                           .withColumn("created_at", current_timestamp()) \
                           .withColumn("updated_at", current_timestamp())

        (initial_df.write
         .format("delta")
         .mode("overwrite")
         .option("overwriteSchema", "true")
         # IMPORTANT NOTE: Ensure CDF is enabled on table creation if you want to use it from the start.
         # This property sets it for the table.
         .option("delta.enableChangeDataFeed", "true")
         .save(delta_table_path))
        print("Initial data written.")
    else:
        print("Delta table already exists. Checking if CDF is enabled.")
        # Programmatically check and enable CDF if not already.
        # This is a good practice for idempotency.
        delta_table_instance = DeltaTable.forPath(spark, delta_table_path)
        if not delta_table_instance.is_cdf_enabled:
            print("CDF is not enabled on this Delta table. Enabling it now.")
            spark.sql(f"ALTER TABLE delta.`{delta_table_path}` SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')")
        else:
            print("CDF is already enabled on this Delta table.")


    delta_table = DeltaTable.forPath(spark, delta_table_path)

    print("\n--- Current Data in Delta Table ---")
    delta_table.toDF().show()

    # --- 2. Prepare Incoming Data for MERGE ---
    print("\n--- Preparing Incoming Data for Merge ---")
    # This data simulates new records and updates to existing records.
    # T002: Update (amount, currency)
    # T004: New Insert
    # T005: New Insert
    incoming_data = [
        ("T002", "ACC-002", 250.00, "GBP", "sale", "MER-XYZ"), # Update T002
        ("T004", "ACC-004", 75.00, "USD", "deposit", "MER-ABC"), # New record
        ("T005", "ACC-005", 1200.50, "JPY", "withdrawal", "MER-123") # New record
    ]
    incoming_df = spark.createDataFrame(incoming_data, ["transaction_id", "account_id", "amount", "currency", "transaction_type", "merchant_id"]) \
                        .withColumn("updated_at_incoming", current_timestamp()) # Add a timestamp for incoming data

    print("Incoming Data Schema:")
    incoming_df.printSchema()
    print("Sample Incoming Data:")
    incoming_df.show()

    # --- 3. Perform MERGE INTO Operation ---
    print("\n--- Performing MERGE INTO Operation ---")
    # MERGE INTO allows for UPSERT logic (UPDATE if matched, INSERT if not matched).
    (delta_table.alias("target")
     .merge(
         incoming_df.alias("source"),
         "target.transaction_id = source.transaction_id" # Join condition
     )
     .whenMatchedUpdate(
         set = {
             "amount": "source.amount",
             "currency": "source.currency",
             "updated_at": "source.updated_at_incoming"
         }
     )
     .whenNotMatchedInsert(
         values = {
             "transaction_id": "source.transaction_id",
             "account_id": "source.account_id",
             "amount": "source.amount",
             "currency": "source.currency",
             "transaction_type": "source.transaction_type",
             "merchant_id": "source.merchant_id",
             "created_at": "source.updated_at_incoming", # Use incoming timestamp as creation for new records
             "updated_at": "source.updated_at_incoming"
         }
     )
     .execute())

    print("\n--- Data in Delta Table After MERGE ---")
    delta_table.toDF().show()

    # --- 4. Read Change Data Feed (CDF) ---
    # CDF must be enabled on the Delta table. If not enabled during creation,
    # it can be enabled with: ALTER TABLE table_name SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')
    # or by setting spark.databricks.delta.properties.defaults.enableChangeDataFeed to true in SparkSession.
    print("\n--- Reading Change Data Feed (CDF) ---")
    try:
        # Get the latest version from the history
        history_df = delta_table.history()
        latest_version = history_df.select("version").orderBy(col("version").desc()).first()["version"]
        print(f"Latest Delta table version: {latest_version}")

        # Read changes since the beginning (or a specific version)
        # The '_change_type' column indicates the type of change (insert, update_preimage, update_postimage, delete)
        df_cdc = (spark.read
                  .format("delta")
                  .option("readChangeFeed", "true")
                  .option("startingVersion", 0) # Read from version 0 to current
                  .load(delta_table_path))

        print("Change Data Feed Schema:")
        df_cdc.printSchema()
        print("Change Data Feed Records:")
        df_cdc.show(truncate=False)

    except Exception as e:
        print(f"Error reading Change Data Feed. Ensure it's enabled on the table and Spark session. Error: {e}")
        print("To enable CDF on an existing table, run:")
        print(f"  spark.sql(\"ALTER TABLE delta.`{delta_table_path}` SET TBLPROPERTIES ('delta.enableChangeDataFeed' = 'true')\")")


    spark.stop()

