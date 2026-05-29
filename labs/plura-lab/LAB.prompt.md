# Lab Build Prompt: Plura.ai (Voice/Real-Time)
Reference: ../LAB_BASE.md

## Objective
Build a low-latency voice AI interaction loop with interrupt handling.

## Architectural Requirements
1. **Hexagonal Structure:** Implement `src/domain` for Call Session logic and `src/infrastructure` for Redis/Twilio adapters.
2. **Medallion Flow:**
   - **Bronze:** Node.js/TypeScript WebSocket gateway landing raw audio streams in MinIO.
   - **Silver:** Polars-based extraction of conversation sentiment and metadata.
   - **Gold:** MongoDB store for "Memory-Aware" user profiles.
3. **Staff Challenge:** Implement a **Redis-backed Interrupt Handler** that kills the TTS stream within 100ms of detecting STT barge-in.

## Execution Steps
1. Setup Node.js WebSocket server in `src/main.ts`.
2. Implement Redis distributed locks for session state in `src/infrastructure/redis_adapter.ts`.
3. Build the sentiment analysis job in `jobs/silver_sentiment.py`.

## AI Critique Task
Ask AI to write the WebSocket handler. Documentation must explain how you improved the AI's error handling to prevent "Ghost Calls" (zombie WebSocket connections) when external APIs timeout.
