# Advanced Concept: Time Travel with Apache Iceberg

Apache Iceberg provides ACID transactions and snapshot-based isolation for large-scale data lakes. In this lab, we use Iceberg (simulated via snapshot-versioned Parquet) to enable **forensic point-in-time analysis**.

## Why Time Travel?
In software security, we often need to answer:
- "What was the vulnerability status of this product *on the day of the release*?"
- "A new CVE was discovered today; were we vulnerable last week before we patched?"

## How it works (Iceberg)
Every write in Iceberg creates a new **Snapshot**. The table metadata tracks these snapshots over time.

### 1. Identify Snapshot IDs
```python
# Conceptual PyIceberg code
from pyiceberg.catalog import load_catalog

catalog = load_catalog("docs")
table = catalog.load_table("silver.enriched_sboms")
snapshots = table.history()
for snapshot in snapshots:
    print(f"Snapshot {snapshot.snapshot_id} created at {snapshot.timestamp_ms}")
```

### 2. Query at a Point in Time
```python
# Query data as it existed 24 hours ago
yesterday_ms = int((time.time() - 86400) * 1000)
df_yesterday = table.scan(snapshot_id=table.snapshot_id_at_time(yesterday_ms)).to_polars()
```

## Lab Implementation (Simulated)
In `Manifest-lab/jobs/silver_job.py`, we simulate this by writing to a `silver/snapshots/` directory with timestamps.

To "Time Travel" in this lab, you can point Polars to a specific snapshot file:
```python
import polars as pl
# Query a specific snapshot from yesterday
df_at_t1 = pl.read_parquet("platform-core/data/minio/silver/snapshots/sboms_20260423120000.parquet")
```

## ACID Guarantees
Iceberg ensures that while the `silver_job.py` is writing a massive new update, users querying the table see a consistent, frozen state of the previous snapshot. No partial reads or corrupted data.
