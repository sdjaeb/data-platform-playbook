# AI RAG: Platform Metadata Discovery

This service uses **Ollama** and **Weaviate** to provide a natural language interface for discovering and diagnosing the data platform.

## How it works
1. **Metadata Ingestion**: A Python script scrapes OpenMetadata, dbt `manifest.json`, and Airflow logs.
2. **Embedding**: The metadata is chunked and embedded using a local model in Ollama (e.g., `nomic-embed-text`).
3. **Vector Storage**: Embeddings are stored in the `Weaviate` vector database.
4. **Natural Language Query**: Users can ask questions like:
   - "Which tables are affected if the `raw_financial` table is deleted?"
   - "Why did the Spark job `delta_merge_cdc` fail yesterday?"
   - "Where is the PII data stored in the gold layer?"

## Setup
1. Ensure Ollama and Weaviate are running: `uv run builder.py init` (select AI Stack).
2. Install dependencies: `uv pip install weaviate-client llama-index ollama`.
3. Run the ingestion script (to be implemented): `python ingest_metadata.py`.
4. Run the query agent: `python query_agent.py`.
