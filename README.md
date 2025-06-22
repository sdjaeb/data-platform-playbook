# Modern Data Stack Lab: Local & Learn

This repository contains a Docker Compose-based local development environment for building and understanding a modern, enterprise-ready data platform. It's designed for hands-on experience with core data engineering technologies, covering ingestion, storage, processing, orchestration, governance, and observability.

The `docs` folder contains historical and deep-dive documentation that served as the basis for this project.

## Table of Contents

1.  Core Architectural Concepts
2.  Key Technologies
3.  Getting Started
    *   Prerequisites
    *   Platform Architecture
    *   Running the Full Stack
    *   Running a Subset of Services
4.  Platform Usage & Walkthrough
    *   Accessing UIs
    *   End-to-End Flow
5.  Project Structure
6.  Contributing
7.  License

## 1. Core Architectural Concepts

The platform is designed around a layered architecture, promoting modularity, scalability, and maintainability:

*   **Ingestion Layer:** Captures data from various sources (e.g., APIs, event streams).
*   **Storage Layer (Data Lakehouse):** Provides flexible, scalable, and transactional storage for raw, curated, and processed data.
*   **Processing Layer:** Transforms, cleanses, and enriches data using a distributed computing framework.
*   **Orchestration & Governance Layer:** Manages workflow dependencies, schedules jobs, and provides a data catalog, lineage, and quality insights.
*   **Observability Layer:** Monitors system health, performance, and data flow, enabling proactive issue detection.
*   **Consumption Layer:** Makes processed data available for analytics, reporting, and downstream applications.

## 2. Key Technologies

This project leverages the following open-source technologies, which are central to modern data platforms:

*   **FastAPI:** High-performance web framework for building data ingestion APIs.
*   **Apache Kafka:** Distributed streaming platform for real-time data ingestion.
*   **Apache Spark:** Unified analytics engine for large-scale data processing.
*   **Delta Lake:** Storage layer bringing ACID transactions to the data lake.
*   **MinIO:** High-performance, S3-compatible object storage for the local data lake.
*   **PostgreSQL:** Central relational database for application metadata (Airflow, Superset).
*   **MongoDB:** NoSQL document database for semi-structured data.
*   **Apache Airflow:** Workflow orchestration platform to schedule and monitor data pipelines.
*   **Apache Superset:** Data visualization and business intelligence platform.
*   **Spline:** Automated data lineage tracking for Apache Spark jobs.
*   **OpenMetadata:** Unified data catalog for data discovery and governance.
*   **Grafana Stack (Grafana, Loki, Prometheus, Alloy):** A full observability suite for visualizing metrics, logs, and traces.
*   **LocalStack:** Emulates AWS services for local cloud development.

## 3. Getting Started

### Prerequisites

Ensure you have the following installed on your machine:

*   **Docker & Docker Compose v2+**
*   **Git**
*   **Python 3.x**

### Platform Architecture

This project uses a modular Docker Compose setup located in the `platform-core/` directory. Service definitions are split across multiple `docker-compose.*.yml` files, each representing a logical component of the data platform (e.g., `core`, `processing`, `orchestration`).

A top-level `platform-core/docker-compose.yml` file uses the `include` directive to assemble the entire platform.

### Running the Full Stack

The easiest way to run the entire platform is by using the bootstrap script. It handles prerequisite checks, directory setup, and brings up all services in the correct order.

From the root of the repository, run:

```bash
cd platform-core
./scripts/bootstrap.sh
```

This command will take several minutes as it builds images and starts all services. Monitor the output for progress.

### Running a Subset of Services

The primary benefit of the modular architecture is the ability to run only the parts of the platform you need, saving system resources.

To do this, you specify the desired `docker-compose.*.yml` files using the `-f` flag. You must **always** include `docker-compose.base.yml`.

**Example: Run only the core databases and the Spark processing stack:**

```bash
cd platform-core

docker compose \
  -f docker-compose.base.yml \
  -f docker-compose.core.yml \
  -f docker-compose.processing.yml \
  up -d
```

## 4. Platform Usage & Walkthrough

### Accessing UIs

Once the `bootstrap.sh` script completes, you can access the following UIs:

| Service              | URL                                      | Credentials (User / Pass) |
| -------------------- | ---------------------------------------- | ------------------------- |
| FastAPI Docs         | `http://localhost:8000/docs`             | N/A                       |
| MinIO Console        | `http://localhost:9001`                  | `minioadmin` / `minioadmin` |
| Spark Master UI      | `http://localhost:8081`                  | N/A                       |
| Spark History Server | `http://localhost:18080`                 | N/A                       |
| Airflow UI           | `http://localhost:8080`                  | `admin` / `admin`         |
| Grafana UI           | `http://localhost:3000`                  | `admin` / `admin`         |
| Spline UI            | `http://localhost:9090`                  | N/A                       |
| OpenMetadata UI      | `http://localhost:8585`                  | `admin` / `admin`         |
| Superset UI          | `http://localhost:8088`                  | `admin` / `admin`         |
| cAdvisor (raw)       | `http://localhost:8083`                  | N/A                       |

### End-to-End Flow

Follow these steps to see the platform in action:

1.  **Generate Data:** In a new terminal, run the data simulator to send data to the FastAPI endpoint.
    ```bash
    python3 simulate_data.py
    ```

2.  **Observe Ingestion:** Data flows from the simulator to FastAPI, which produces messages to Kafka. A Spark streaming job consumes these messages and writes the raw data as Delta tables into the `raw-data-bucket` in MinIO.

3.  **Run Transformation Pipeline:** In the Airflow UI (`http://localhost:8080`), unpause and trigger the `full_pipeline_with_governance` DAG. This will orchestrate a Spark batch job to transform the raw data and write it to the `curated-data-bucket`.

4.  **Explore & Monitor:**
    *   **OpenMetadata:** See the new tables and view their end-to-end data lineage.
    *   **Superset:** Connect to the curated data and build dashboards.
    *   **Grafana:** View dashboards monitoring container health and application metrics.

## 5. Project Structure

The repository is organized to logically separate different components:

```
.
├── platform-core/            # Contains all Docker Compose files, configs, and scripts
│   ├── airflow_dags/         # Airflow DAG definitions
│   ├── config/               # Shared configuration files (e.g., Grafana Alloy)
│   ├── fastapi_app/          # FastAPI ingestion service
│   ├── observability/        # Grafana dashboards and provisioning files
│   ├── postgres-init/        # Initialization scripts for PostgreSQL
│   ├── pyspark_jobs/         # Spark transformation jobs
│   ├── scripts/              # Helper scripts (e.g., bootstrap.sh)
│   ├── secrets/              # Secret files (placeholders)
│   ├── superset_config/      # Superset configuration
│   ├── webhook_listener_app/ # MinIO webhook listener service
│   └── docker-compose.*.yml  # Modular Docker Compose files
├── docs/                     # Historical and deep-dive documentation
├── simulate_data.py          # Script to generate sample data
└── README.md                 # This file
```

## 6. Contributing

Contributions are welcome! If you find issues or have suggestions for improvements, please open an issue or submit a pull request.

## 7. License

This project is licensed under the MIT License. See the `LICENSE` file for details.