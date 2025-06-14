# Modern Data Stack Lab: Local & Learn

This repository contains the comprehensive guide and a Docker Compose-based local development environment for building and understanding a modern, enterprise-ready data platform. It emphasizes practical, hands-on experience with core data engineering technologies, covering ingestion, storage, processing, orchestration, observability, and governance.

## Table of Contents

1.  [Purpose and Introduction](#1-purpose-and-introduction)
2.  [Core Architectural Concepts](#2-core-architectural-concepts)
3.  [Key Technologies](#3-key-technologies)
4.  [Getting Started (Local Environment Setup)](#4-getting-started-local-environment-setup)
    * [Prerequisites](#prerequisites)
    * [Quick Start](#quick-start)
    * [Accessing UIs](#accessing-uis)
5.  [Platform Usage & Walkthrough](#5-platform-usage--walkthrough)
6.  [Deep Dives & Advanced Topics](#6-deep-dives--advanced-topics)
7.  [Project Structure](#7-project-structure)
8.  [Contributing](#8-contributing)
9.  [License](#9-license)

## 1. Purpose and Introduction

In today's data-driven world, enterprises require robust and scalable data platforms to ingest, process, store, and analyze vast amounts of data from diverse sources. This project provides a blueprint and a fully functional local environment that mirrors a production-grade data platform. It's designed for experienced Data Engineers and Senior Software Engineers to rapidly prototype, test, and understand complex distributed data systems without incurring cloud costs or dependencies.

The guide meticulously covers:
* Building a resilient local development environment.
* Implementing Python-based ETL pipelines.
* Adhering to modern architectural patterns and best practices, including Infrastructure as Code (IaC), CI/CD, comprehensive testing, data contracts, and observability.
* Exploring advanced topics like Machine Learning (ML) tooling, AI/LLM integration, and cloud migration strategies.

## 2. Core Architectural Concepts

The platform is designed around a layered architecture, promoting modularity, scalability, and maintainability:

* **Ingestion Layer:** Captures data from various sources, handling high throughput and diverse formats.
* **Storage Layer (Data Lakehouse):** Provides flexible, scalable, and transactional storage for raw, refined, and curated data.
* **Processing Layer:** Transforms, cleanses, and enriches data using distributed computing frameworks.
* **Orchestration & Governance Layer:** Manages workflow dependencies, schedules jobs, and provides data catalog, lineage, and quality insights.
* **Observability Layer:** Monitors system health, performance, and data flow, enabling proactive issue detection.
* **Consumption Layer:** Makes processed data available for analytics, reporting, and downstream applications.

## 3. Key Technologies

This project leverages the following open-source technologies, which are central to modern data platforms:

* **FastAPI:** High-performance web framework for building data ingestion APIs.
* **Apache Kafka:** Distributed streaming platform for real-time data ingestion and decoupled architecture.
* **Apache Spark:** Unified analytics engine for large-scale data processing (batch and streaming).
* **Delta Lake:** Open-source storage layer that brings ACID transactions, schema enforcement, and time travel to data lakes (on MinIO).
* **MinIO:** High-performance, S3-compatible object storage for local data lake simulation.
* **PostgreSQL:** Robust relational database for application metadata, reference data, and Apache Airflow's metastore.
* **MongoDB:** Flexible NoSQL document database for semi-structured data or specific application use cases.
* **Apache Airflow:** Workflow orchestration platform to programmatically author, schedule, and monitor data pipelines.
* **Spline:** Automated data lineage tracking for Apache Spark jobs.
* **OpenMetadata:** Unified data catalog, data lineage, and data quality platform for data discovery and governance.
* **Grafana Alloy:** OpenTelemetry Collector distribution for unified telemetry (metrics, logs, traces) collection.
* **Grafana:** Open-source platform for interactive data visualization, monitoring, and alerting.
* **cAdvisor:** Container Advisor for monitoring resource usage and performance of Dockerized services.
* **AWS SAM CLI:** (Conceptual integration) Local development tool for serverless applications.
* **Locust:** (Conceptual integration) Open-source load testing tool.

## 4. Getting Started (Local Environment Setup)

This section guides you through setting up the complete data platform on your local machine using Docker Compose.

### Prerequisites

Ensure you have the following installed on your machine:

* **Docker Desktop** (or Docker Engine on Linux): For running containers.
* **Git:** For cloning this repository.
* **Python 3.x:** With `pip` for running scripts and managing Python dependencies.
* **`docker-compose`:** (Usually included with Docker Desktop, or install separately).
* **AWS SAM CLI:** (Optional, for serverless examples; install if you plan to use `sam_lambda` features).

### Quick Start

1.  **Clone the Repository:**
    ```bash
    git clone <your-repo-url>/data-ingestion-platform.git
    cd data-ingestion-platform
    ```

2.  **Run the Quick Start Script:**
    This script will create necessary directories, copy conceptual code snippets to their working locations, and bring up all Docker Compose services for the **Advanced Track** environment.

    ```bash
    chmod +x scripts/quick_start.sh
    ./scripts/quick_start.sh
    ```
    *This command will take several minutes as it builds images and starts numerous services. Monitor the output for progress and any errors.*

### Accessing UIs

Once the `quick_start.sh` script completes and services become healthy, you can access the following UIs in your web browser:

* **FastAPI Docs (Swagger UI):** `http://localhost:8000/docs`
* **MinIO Console:** `http://localhost:9901` (User: `minioadmin`, Pass: `minioadmin`)
* **Spark Master UI:** `http://localhost:8080` (Check Spark job status, not for applications)
* **Spark History Server:** `http://localhost:18080` (After Spark jobs run, for historical job details)
* **Airflow UI:** `http://localhost:8081` (User: `admin`, Pass: `admin`)
* **Grafana UI:** `http://localhost:3000` (User: `admin`, Pass: `admin`)
* **Spline UI:** `http://localhost:9090`
* **OpenMetadata UI:** `http://localhost:8585`

## 5. Platform Usage & Walkthrough

After the environment is up, you can start interacting with the platform:

1.  **Generate Data:**
    The `simulate_data.py` script sends mock financial transactions and insurance claims to the FastAPI ingestor.
    ```bash
    python3 scripts/simulate_data.py
    ```
    Keep this running in a separate terminal to provide continuous data flow.

2.  **Observe Data Flow:**
    * **FastAPI Logs:** Check `docker compose logs fastapi_ingestor` to see incoming requests and Kafka messages being sent.
    * **Kafka Consumption (Spark):** The Spark streaming job (`streaming_consumer.py`) continuously consumes from Kafka and writes to MinIO. Monitor `docker compose logs spark` or Spark UI to see this.
    * **MinIO Console:** Observe new files appearing in `raw-data-bucket/financial_data_delta/` and `raw-data-bucket/insurance_data_delta/`.

3.  **Run ETL/ELT Jobs:**
    * **Airflow Orchestration:** Trigger the `financial_data_lake_pipeline` DAG in the Airflow UI (`http://localhost:8081`). This DAG orchestrates Spark jobs for ingestion and transformation.
    * **MinIO Console:** See transformed data appear in `curated-data-bucket/`.

4.  **Monitor with Grafana:**
    * Explore dashboards in Grafana (`http://localhost:3000`) to visualize API request rates, Kafka consumer lag, Spark resource utilization, and overall container health.

5.  **Explore Data Catalog & Lineage with OpenMetadata/Spline:**
    * Access OpenMetadata (`http://localhost:8585`) to browse data assets, view schemas, and inspect data lineage for your Spark-processed tables.

## 6. Deep Dives & Advanced Topics

This project is accompanied by a series of "Deep Dive" documents that provide detailed explanations and interactive how-tos for specific aspects of the platform:

* **Deep Dive: ML Tooling in the Platform:** Explores feature engineering, model training, and inference using Spark and your data lakehouse.
* **Deep Dive: Integrating AI/LLMs/MLOps:** Covers data preparation for RAG, LLM interaction via API gateways, and MLOps principles for AI/LLM workloads.
* **Deep Dive: Applying Platform Concepts to Snowflake:** Maps local open-source components to their Snowflake equivalents and demonstrates data ingestion and transformation in Snowflake.
* **Deep Dive: Cloud Component Comparison (AWS, Azure, GCP):** Provides a high-level comparison of managed service equivalents across the major cloud providers.

Refer to these documents for detailed explanations and guided exercises.

## 7. Project Structure

The repository is organized to logically separate different components and concerns:


```
data-ingestion-platform/
├── .github/                 # GitHub Actions CI/CD workflows
│   └── workflows/
├── data/                    # Persistent Docker volumes for all services
│   ├── postgres/
│   ├── mongodb/
│   ├── minio/
│   ├── spark-events/
│   ├── grafana/
│   ├── openmetadata_mysql/
│   └── openmetadata_elasticsearch/
├── src/                     # Core Python application logic (common utils, models)
│   └── common/
│   └── models/              # Pydantic/Avro schemas for data contracts
├── fastapi_app/             # FastAPI ingestion service (Docker context, app code, tests)
│   ├── app/                 # FastAPI application source
│   ├── tests/               # Unit and integration tests
│   └── Dockerfile
│   └── requirements.txt
├── pyspark_jobs/            # Apache Spark transformation jobs (PySpark scripts)
│   ├── tests/               # Unit and contract tests for Spark jobs
├── airflow_dags/            # Apache Airflow DAG definitions
├── observability/           # Grafana dashboards, Grafana Alloy configurations
├── openmetadata_ingestion_scripts/ # Python scripts for OpenMetadata connectors
├── terraform_infra/         # Infrastructure as Code (IaC) using Terraform
│   ├── modules/             # Reusable Terraform modules for AWS services
│   ├── environments/        # Environment-specific Terraform configurations (dev, staging, prod)
├── sam_lambda/              # AWS SAM CLI local serverless development examples
├── load_testing/            # Locust load test scripts
├── scripts/                 # Utility scripts (e.g., quick_start.sh, simulate_data.py)
├── conceptual_code/         # Consolidated source code snippets from documentation
└── docker-compose.yml       # Central Docker Compose file for local environment
└── docker-compose.test.yml  # Docker Compose for integration testing
└── README.md                # This document
```

## 8. Contributing

Contributions are welcome! If you find issues or have suggestions for improvements, please open an issue or submit a pull request.

## 9. License

This project is licensed under the MIT License. See the `LICENSE` file for details.
