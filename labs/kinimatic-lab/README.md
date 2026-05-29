# Kinimatic Lab: Distributed Logistics Intelligence

## Architecture: Event-Driven Medallion
Focus: Normalizing 350+ messy WMS/EDI sources into unified visibility.

### Stack
- **API:** Python / Flask (As requested in JD)
- **Messaging:** AWS EventBridge (Emulated via LocalStack) or Kafka
- **Database:** PostgreSQL (Item Master / Inventory)
- **AI Agents:** LangGraph (NOS Network Optimization)

### Core Challenges
1. **EDI Normalization:** Transforming raw X12/EDIFACT into clean Silver-tier JSON.
2. **Eventual Consistency:** Reconciling 'Shipment Departed' with 'Inventory Adjusted' across distributed nodes.
3. **AI-First SDLC:** Use Claude Code to generate the LangGraph state machine.

### Setup
```bash
# Run from data-platform-playbook root
docker compose -f platform-core/docker-compose.base.yml -f platform-core/docker-compose.core.yml -f platform-core/docker-compose.emulation.yml up -d
python3 Kinimatic-lab/data-generator/gen_logistics.py
```
