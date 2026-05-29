import httpx
import time
import uuid

URL = "http://localhost:8001/ingest/sbom"

def generate_aibom(model_name: str):
    """Generates a CycloneDX-style AIBOM fragment."""
    return {
        "bom_format": "CycloneDX",
        "spec_version": "1.6",
        "metadata": {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "component": {
                "name": model_name,
                "type": "machine-learning-model",
                "version": "v1.0.0"
            }
        },
        "components": [
            {
                "name": f"{model_name}-weights",
                "type": "file",
                "hashes": [{"alg": "SHA-256", "content": uuid.uuid4().hex}]
            },
            {
                "name": "training-dataset-v1",
                "type": "data",
                "properties": [
                    {"name": "manifest:bias_checked", "value": "true"},
                    {"name": "manifest:license", "value": "Apache-2.0"}
                ]
            }
        ]
    }

async def ingest_aiboms():
    models = ["llama-3-8b", "mistral-7b-v0.1", "stable-diffusion-xl"]
    print(f"🚀 Ingesting {len(models)} AIBOMs into the Manifest pipeline...")
    
    async with httpx.AsyncClient() as client:
        for model in models:
            aibom = generate_aibom(model)
            resp = await client.post(URL, json=aibom)
            if resp.status_code == 202:
                print(f"✅ Ingested AIBOM for {model} | CID: {resp.json().get('cid')}")
            else:
                print(f"❌ Failed to ingest {model}: {resp.text}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(ingest_aiboms())
