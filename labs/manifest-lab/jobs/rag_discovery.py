import polars as pl
import weaviate
import weaviate.classes as wvc
import ollama
import os

# Configuration
SILVER_FILE = "data/minio/silver/enriched-sboms.parquet"
WEAVIATE_URL = "localhost" # v4 uses host/port separately or connect_to_local
WEAVIATE_PORT = 8083
EMBED_MODEL = "nomic-embed-text"
LLM_MODEL = "tinyllama"

def run_rag_discovery():
    print("🤖 Initializing RAG Discovery Agent (Weaviate v4)...")
    
    # 1. Connect to Weaviate (v4 Style)
    client = weaviate.connect_to_local(
        host=WEAVIATE_URL,
        port=WEAVIATE_PORT
    )
    
    try:
        # 2. Setup Collection (formerly Class)
        if client.collections.exists("SecurityMetadata"):
            client.collections.delete("SecurityMetadata")
            print("Cleaning up old collection...")

        client.collections.create(
            name="SecurityMetadata",
            properties=[
                wvc.config.Property(name="component_name", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="version", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="severity", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="cve_id", data_type=wvc.config.DataType.TEXT),
                wvc.config.Property(name="summary", data_type=wvc.config.DataType.TEXT),
            ]
        )
        print("✅ Created Weaviate v4 Collection.")

        # 3. Read Silver Data & Index
        if not os.path.exists(SILVER_FILE):
            print(f"❌ Silver file {SILVER_FILE} missing. Run enrichment first.")
            return

        df = pl.read_parquet(SILVER_FILE)
        print(f"📊 Read {len(df)} components from Silver layer.")
        
        collection = client.collections.get("SecurityMetadata")
        
        for row in df.to_dicts():
            summary = f"Component {row['component_name']} version {row['component_version']} has a security severity of {row['severity']} with CVE {row['cve_id']}."
            
            # Generate Vector using Host Ollama
            vector_resp = ollama.embeddings(model=EMBED_MODEL, prompt=summary)
            vector = vector_resp['embedding']
            
            # Insert into Weaviate (v4 Style)
            collection.data.insert(
                properties={
                    "component_name": str(row['component_name']),
                    "version": str(row['component_version']),
                    "severity": str(row['severity']),
                    "cve_id": str(row['cve_id']),
                    "summary": summary
                },
                vector=vector
            )
        
        print("✅ All metadata indexed into Vector Database.")

        # 4. Ask a Question
        query = "Which components should I worry about most right now and why?"
        print(f"\n❓ User Query: {query}")
        
        # Retrieve relevant context from Weaviate
        query_vector = ollama.embeddings(model=EMBED_MODEL, prompt=query)['embedding']
        
        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=2
        )
        
        context = ""
        for obj in response.objects:
            context += obj.properties['summary'] + "\n"
        
        # Generate Answer using Host Ollama
        prompt = f"Using the following security context, answer the question: {query}\n\nContext:\n{context}"
        
        output = ollama.generate(model=LLM_MODEL, prompt=prompt)
        print(f"\n🤖 AI Response:\n{output['response']}")

    finally:
        client.close()

if __name__ == "__main__":
    run_rag_discovery()
