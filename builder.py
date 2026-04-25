import typer
import yaml
from pathlib import Path
from typing import List, Optional

app = typer.Typer(help="Data Platform Playbook Builder CLI")

COMPOSE_FILE = Path("platform-core/docker-compose.yml")

def load_compose():
    with open(COMPOSE_FILE, "r") as f:
        return yaml.safe_load(f)

def save_compose(data):
    with open(COMPOSE_FILE, "w") as f:
        yaml.dump(data, f, sort_keys=False)

@app.command()
def init():
    """Initialize the data platform by selecting components."""
    typer.echo("🚀 Welcome to the Data Platform Playbook Builder!")
    
    # 1. Streaming
    streaming = typer.prompt(
        "Select Streaming Engine", 
        type=typer.Choice(["kafka", "redpanda"]), 
        default="kafka"
    )
    
    # 2. Orchestrator
    orchestrator = typer.prompt(
        "Select Orchestrator", 
        type=typer.Choice(["airflow", "dagster"]), 
        default="airflow"
    )
    
    # 3. AI Stack
    include_ai = typer.confirm("Include AI/LLM Stack (Ollama, Weaviate)?", default=False)
    
    # 4. Extras
    include_temporal = typer.confirm("Include Temporal for durable workflows?", default=False)
    include_risingwave = typer.confirm("Include RisingWave for streaming SQL?", default=False)
    include_opa = typer.confirm("Include OPA for policy enforcement?", default=False)

    # Build the include list
    includes = ["docker-compose.base.yml", "docker-compose.core.yml"]
    
    if streaming == "kafka":
        includes.append("docker-compose.core.yml") # Kafka is in core
    else:
        includes.append("docker-compose.redpanda.yml")
        
    includes.extend([
        "docker-compose.generators.yml",
        "docker-compose.ingestion.yml",
        "docker-compose.processing.yml",
    ])
    
    if orchestrator == "airflow":
        includes.append("docker-compose.orchestration.yml")
    else:
        includes.append("docker-compose.dagster.yml")
        
    includes.extend([
        "docker-compose.dbt.yml",
        "docker-compose.governance.yml",
        "docker-compose.bi.yml",
        "docker-compose.observability.yml",
    ])
    
    if include_ai:
        includes.extend(["docker-compose.ollama.yml", "docker-compose.weaviate.yml"])
        
    if include_temporal:
        includes.append("docker-compose.temporal.yml")
        
    if include_risingwave:
        includes.append("docker-compose.risingwave.yml")

    # Update docker-compose.yml
    compose_data = load_compose()
    compose_data["include"] = includes
    save_compose(compose_data)
    
    typer.echo(f"✅ Data Platform updated! Configuration saved to {COMPOSE_FILE}")
    typer.echo("Run 'docker compose up -d' to start your custom stack.")

if __name__ == "__main__":
    app()
