import polars as pl
import os
import glob
from datetime import datetime
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Configuration
BRONZE_DIR = "data/minio/bronze/sboms/*.json"
SILVER_OUTPUT = "data/minio/silver/enriched-sboms.parquet"
VULNERABILITIES_FILE = "labs/manifest-lab/vulnerabilities.parquet"

# Initialize OpenTelemetry
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)
tracer = trace.get_tracer("silver-processor")

def process_silver():
    with tracer.start_as_current_span("ProcessSilver"):
        print(f"🚀 Starting Advanced Silver transformation job at {datetime.now()}")
        
        try:
            files = glob.glob(BRONZE_DIR)
            if not files:
                print("No bronze files found.")
                return

            # 1. Load data
            # Use standard EAGER load for this lab to handle small individual JSONs easily
            dfs = []
            for f in files:
                dfs.append(pl.read_json(f))
            df_bronze = pl.concat(dfs)
            
            # 2. Normalize
            df_silver = (
                df_bronze
                .explode("data")
                .unnest("data")
                .rename({"name": "component_name", "version": "component_version"})
            )
            
            # 3. Join with CURRENT vulnerabilities (The "Patch" application)
            # Staff-level: We use a LEFT join so that all components are preserved even if no CVE found
            vulnerabilities = pl.read_parquet(VULNERABILITIES_FILE)
            
            df_enriched = df_silver.join(
                vulnerabilities,
                left_on=["component_name", "component_version"],
                right_on=["component_name", "version"],
                how="left"
            ).fill_null("NONE")
            
            # 4. Deduplicate
            df_deduped = df_enriched.unique(subset=["component_name", "component_version"])
            
            # 5. Sink to Snapshots
            os.makedirs(os.path.dirname(SILVER_OUTPUT), exist_ok=True)
            snapshot_time = datetime.now().strftime("%Y%m%d%H%M%S")
            versioned_output = f"data/minio/silver/snapshots/sboms_{snapshot_time}.parquet"
            os.makedirs(os.path.dirname(versioned_output), exist_ok=True)
            
            df_deduped.write_parquet(versioned_output)
            df_deduped.write_parquet(SILVER_OUTPUT)
            
            print(f"✅ Advanced Silver complete. Snapshot: {versioned_output}")
            print(df_deduped.select(["component_name", "component_version", "severity"]))

        except Exception as e:
            print(f"❌ Advanced Silver failed: {str(e)}")

if __name__ == "__main__":
    process_silver()
