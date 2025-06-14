# Description: PySpark script for complex batch transformation and data quality.
# Source: Highlighting Apache Spark, Advanced Use Case 1.
import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, trim, lower, coalesce, lit, current_timestamp, sha2, concat_ws
from pyspark.sql.types import StringType, FloatType, TimestampType, LongType
from delta.tables import DeltaTable

def create_spark_session(app_name):
    """Helper function to create a SparkSession with Delta Lake and PostgreSQL packages."""
    return (SparkSession.builder.appName(app_name)
            .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0,org.postgresql:postgresql:42.6.0")
            .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
            .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
            .getOrCreate())

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: batch_transformations.py <raw_delta_path> <curated_delta_path>")
        sys.exit(-1)

    raw_delta_path = sys.argv[1]
    curated_delta_path = sys.argv[2]

    spark = create_spark_session("BatchETLTransformation")
    spark.sparkContext.setLogLevel("WARN")

    # PostgreSQL connection properties for reference data
    pg_url = "jdbc:postgresql://postgres:5432/main_db" # 'postgres' is the service name in docker-compose
    pg_properties = {
        "user": "user",
        "password": "password",
        "driver": "org.postgresql.Driver"
    }

    print(f"Reading raw data from: {raw_delta_path}")
    df_raw = spark.read.format("delta").load(raw_delta_path)
    df_raw.printSchema()
    df_raw.show(5, truncate=False)

    # Data Cleansing and Transformation
    print("Applying data cleansing and transformations...")
    df_cleaned = df_raw.withColumn("amount_clean",
                                  when(col("amount").isNull(), lit(0.0))
                                  .otherwise(col("amount").cast(FloatType()))) \
                       .withColumn("currency_clean", trim(upper(col("currency")))) # Ensure currency is uppercase and trimmed
    # Apply a simple data quality check: if amount is 0, flag it.
    df_quality = df_cleaned.withColumn("is_amount_zero_flag", when(col("amount_clean") == 0.0, True).otherwise(False))

    # Data Enrichment: Join with PostgreSQL reference data (merchant_lookup)
    print("Loading merchant lookup data from PostgreSQL...")
    try:
        df_merchant_lookup = spark.read.jdbc(url=pg_url, table="merchant_lookup", properties=pg_properties)
        df_merchant_lookup.printSchema()
        df_merchant_lookup.show(5, truncate=False)

        print("Joining with merchant lookup data...")
        # Use coalesce for merchant_id to handle potential nulls from source if needed
        df_enriched = df_quality.join(df_merchant_lookup,
                                      df_quality.merchant_id == df_merchant_lookup.merchant_id,
                                      "left_outer") \
                               .withColumn("enriched_category", coalesce(col("merchant_lookup.category"), col("category"))) \
                               .drop(df_merchant_lookup.merchant_id) # Drop the duplicate join key
    except Exception as e:
        print(f"Error loading merchant lookup data or joining: {e}. Proceeding without enrichment.")
        df_enriched = df_quality.withColumn("enriched_category", col("category")) # Fallback if join fails

    # Select final columns and reorder for the curated zone
    # Mask sensitive data: SHA256 hash of account_id
    df_final = df_enriched.select(
        col("transaction_id"),
        col("timestamp"),
        sha2(col("account_id").cast(StringType()), 256).alias("hashed_account_id"), # Masking
        col("amount_clean").alias("amount"),
        col("currency_clean").alias("currency"),
        col("transaction_type"),
        col("merchant_id"),
        col("enriched_category").alias("category"),
        col("is_amount_zero_flag"),
        current_timestamp().alias("processed_at") # Add processing timestamp
    ).distinct() # Ensure no duplicate transactions after processing

    print("Schema of transformed data:")
    df_final.printSchema()
    df_final.show(5, truncate=False)

    # Write to Curated Delta Lake
    print(f"Writing transformed data to curated zone: {curated_delta_path}")
    # Use overwriteSchema for initial load or if schema changes are breaking and force-applied
    # Otherwise, use mergeSchema if you expect only additive changes.
    df_final.write.format("delta").mode("overwrite").option("overwriteSchema", "true").save(curated_delta_path)
    print("Batch transformation complete.")

    spark.stop()