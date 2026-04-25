---
description: "Infra-as-code & config"
applyTo: "**/infra/**,**/*.tf,**/*.yaml,**/*.yml"
---

## Infra Rules

- Tag resources with stable ownership and environment fields.
- Use least privilege. Do not use wildcard permissions without a clear reason.
- Add alarms or metrics for failure, throttling, and saturation signals.
- Add retention or lifecycle rules for durable storage.
- Cap concurrency and batch where cost can spike.
- Treat production-impacting infra changes as rollback-aware work.
- If a repo already has an IaC style, use it. Do not mix styles casually.
