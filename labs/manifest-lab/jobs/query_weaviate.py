import weaviate
import weaviate.classes as wvc
import ollama

# Configuration
WEAVIATE_URL = "localhost"
WEAVIATE_PORT = 8083
EMBED_MODEL = "nomic-embed-text"

def query_threats(user_query: str):
    # 1. Connect to Weaviate (v4 Style)
    client = weaviate.connect_to_local(
        host=WEAVIATE_URL,
        port=WEAVIATE_PORT
    )
    
    try:
        print(f"🔍 Performing Semantic Search (v4): '{user_query}'")
        
        # 2. Get the collection
        if not client.collections.exists("SecurityMetadata"):
            print("❌ Collection 'SecurityMetadata' missing. Run rag_discovery.py first.")
            return

        collection = client.collections.get("SecurityMetadata")

        # 3. Convert query to vector
        query_vector = ollama.embeddings(model=EMBED_MODEL, prompt=user_query)['embedding']
        
        # 4. Query (v4 Style)
        response = collection.query.near_vector(
            near_vector=query_vector,
            limit=3,
            return_metadata=wvc.query.MetadataQuery(distance=True)
        )
        
        # 5. Display Results
        print("\n--- Semantic Matches Found ---")
        if not response.objects:
            print("❌ No matches found.")
            return

        for i, obj in enumerate(response.objects):
            props = obj.properties
            distance = obj.metadata.distance
            print(f"{i+1}. [{props['component_name']}@{props['version']}] - Severity: {props['severity']}")
            print(f"   Context: {props['summary']}")
            print(f"   Confidence Score: {1 - float(distance):.4f}\n")

    finally:
        client.close()

if __name__ == "__main__":
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "Show me components with XML parsing risks."
    query_threats(q)
