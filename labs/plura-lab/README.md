# Plura.ai Lab: Real-Time Voice AI Ingestor

## Architecture: Low-Latency Streaming (Hexagonal)
Focus: Synchronizing STT -> LLM -> TTS without state desync.

### Stack
- **API:** Node.js / TypeScript (As requested in JD)
- **State:** Redis (Real-time session/mutex)
- **Buffer:** Kafka (Event log)
- **Bronze:** MinIO (Raw audio/transcription history)

### Core Challenges
1. **Interrupt Handling:** If user speaks while AI speaks, stop TTS stream immediately.
2. **State Desync:** Use Redis distributed locking to prevent LLM thoughts from overlapping.
3. **Refactor Path:** Lab focuses on migrating legacy JS handlers to typed TS interfaces.

### Setup
```bash
# Run from data-platform-playbook root
docker compose -f platform-core/docker-compose.base.yml -f platform-core/docker-compose.core.yml up -d
python3 Plura-lab/data-generator/gen_calls.py
```
