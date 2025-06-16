# pyspark_jobs/ml_model_inference.py
# This script demonstrates a conceptual Spark job for ML model inference.
# It reads pre-processed, curated data from a Delta Lake table in MinIO,
# simulates loading a simple ML model, performs inference, and
# writes the results back to another Delta Lake table.
# This highlights how Spark serves as a processing engine for analytical workflows.

import sys
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, rand, current_timestamp
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml import Pipeline

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
            # Spline configuration for lineage tracking
            # IMPORTANT NOTE: The `spline-rest` service is mapped to port 8083 externally,
            # but internally it listens on 8080. Use the internal port for inter-container communication.
            .config("spark.spline.producer.url", "http://spline-rest:8080/producer")
            .config("spark.spline.mode", "ENABLED")
            .config("spark.spline.log.level", "WARN")
            .config("spark.driver.extraJavaOptions", "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar")
            .getOrCreate())

if __name__ == "__main__":
    # Command-line arguments: input curated data path, output inference path
    # Example: docker exec -it spark-master spark-submit \
    #          --packages io.delta:delta-core_2.12:2.4.0 \
    #          --conf spark.sql.extensions=io.delta.sql.DeltaSparkSessionExtension \
    #          --conf spark.sql.catalog.spark_catalog=org.apache.spark.sql.delta.catalog.DeltaCatalog \
    #          --conf spark.hadoop.fs.s3a.endpoint=http://minio:9000 \
    #          --conf spark.hadoop.fs.s3a.access.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.secret.key=minioadmin \
    #          --conf spark.hadoop.fs.s3a.path.style.access=true \
    #          --conf spark.spline.producer.url=http://spline-rest:8080/producer \
    #          --conf spark.spline.mode=ENABLED \
    #          --driver-java-options "-javaagent:/opt/bitnami/spark/jars/spline-agent-bundle-0.7.1.jar" \
    #          /opt/bitnami/spark/jobs/ml_model_inference.py \
    #          s3a://curated-data-bucket/financial_data_curated_batch \
    #          s3a://model-output-bucket/financial_fraud_predictions
    if len(sys.argv) != 3:
        print("Usage: ml_model_inference.py <curated_data_input_path> <inference_output_path>")
        sys.exit(-1)

    curated_data_path = sys.argv[1]
    inference_output_path = sys.argv[2]

    spark = create_spark_session("MLModelInference")
    spark.sparkContext.setLogLevel("WARN")

    print(f"Reading curated data from: {curated_data_path}")
    df_curated = spark.read.format("delta").load(curated_data_path)

    if df_curated.count() == 0:
        print(f"No data found in {curated_data_path}. Exiting.")
        spark.stop()
        sys.exit(0)

    print("Curated Data Schema:")
    df_curated.printSchema()
    print("Sample Curated Data (before inference):")
    df_curated.show(5, truncate=False)

    # --- Conceptual ML Model Inference ---
    print("Simulating ML model inference...")

    # For demonstration, we'll create a dummy 'is_fraud' column
    # based on a simple rule and then run a conceptual Logistic Regression.
    # In a real scenario, a trained model would be loaded (e.g., from MLflow or serialized).

    # 1. Feature Engineering (Conceptual) - Prepare features for a dummy model
    # Assume 'amount' and a random feature are inputs
    # Let's add a dummy 'feature_1' for demonstration
    df_features = df_curated.withColumn("feature_1", rand()) \
                            .withColumn("label", when(col("amount") > 500, 1).otherwise(0)) # Dummy label for training

    # Define the features to be used by the model
    feature_columns = ["amount", "feature_1"] # Use 'amount' and the dummy feature_1
    assembler = VectorAssembler(inputCols=feature_columns, outputCol="features")

    # Conceptual Logistic Regression Model
    # In a real scenario, this model would be loaded from a persisted state, not trained here.
    lr = LogisticRegression(featuresCol="features", labelCol="label", maxIter=10, regParam=0.3, elasticNetParam=0.8)

    # Create a dummy pipeline to include feature assembly and the model
    pipeline = Pipeline(stages=[assembler, lr])

    # Fit a dummy model (only for pipeline structure demonstration, not real training)
    # In a real application, you'd load a pre-trained model.
    # If df_features is empty, this fit will fail.
    try:
        dummy_model = pipeline.fit(df_features.limit(10)) # Fit on a small subset to avoid error if no data
    except Exception as e:
        print(f"Warning: Could not fit dummy ML model. This might happen if input data is too small/empty. Error: {e}")
        dummy_model = None # Set to None if fitting fails

    # Perform inference (prediction) if dummy model was created
    if dummy_model:
        df_predicted = dummy_model.transform(df_features) \
                                   .select(
                                       col("transaction_id"),
                                       col("amount"),
                                       col("enriched_category"),
                                       col("prediction").alias("fraud_prediction"), # The model's prediction
                                       col("probability").alias("fraud_probability"), # Probability vector
                                       current_timestamp().alias("inference_timestamp")
                                   )
    else:
        # Fallback if model could not be fitted (e.g., no data)
        df_predicted = df_curated.withColumn("fraud_prediction", lit(0.0)) \
                                 .withColumn("fraud_probability", lit(None)) \
                                 .withColumn("inference_timestamp", current_timestamp())

    print("Inference Result Schema:")
    df_predicted.printSchema()
    print("Sample Inference Results:")
    df_predicted.show(5, truncate=False)

    # --- Write Inference Results to Delta Lake ---
    print(f"Writing inference results to Delta Lake: {inference_output_path}")
    (df_predicted.write
     .format("delta")
     .mode("overwrite") # Overwrite with latest inference results
     .option("overwriteSchema", "true")
     .save(inference_output_path))

    print(f"ML model inference complete. Results written to {inference_output_path}")

    spark.stop()

