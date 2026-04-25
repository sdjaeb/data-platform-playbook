---
description: "PySpark Jobs and Data Processing"
applyTo: "**/pyspark_jobs/**/*.py"
---

## Spark Rules

- **Schema Enforcement**: Always define schemas explicitly when reading data.
- **Delta Lake**: Prefer Delta Lake for ACID transactions and time travel.
- **Resource Management**: Configure executor memory and cores appropriately for the task.
- **Logging**: Use the Spark log4j logger for consistency.
- **Testing**: Use local Spark sessions for unit testing transformations.
- **Lineage**: Ensure Spline or OpenMetadata lineage is captured.
