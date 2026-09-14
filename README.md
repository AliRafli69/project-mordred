# Project Mordred

A private, self-hosted study assistant built incrementally to learn API development, Postman, and retrieval-augmented generation (RAG).

## Status

Phase 3 is complete: local model inference, authenticated API requests, Postman tests, and private server-to-inference connectivity have been demonstrated. The custom backend, browser chatbot, document retrieval, and cited answers are not implemented yet.

## Architecture

- **Control server:** Ubuntu Server on an HP Pavilion; always-on host for the planned backend, browser interface, document storage, and retrieval index.
- **Inference computer:** Windows on an ASUS ROG G14 with an RTX 4060 Laptop GPU; runs LM Studio and may sleep or disconnect.
- **Private connection:** Tailscale, with host firewall restrictions and API authentication.

The control server must tolerate unavailable inference. There is no automatic cloud-inference fallback. Embedding placement remains undecided.

## Documentation

- [Project brief](docs/PROJECT_BRIEF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Roadmap](docs/ROADMAP.md)
- [Decision log](docs/DECISIONS.md)
- [Current state](docs/PROJECT_STATE.md)
- [Phase 3 validation](docs/phases/PHASE_3.md)
- [Postman practice](postman/README.md)
- [Publication checklist](docs/PUBLISHING.md)

This repository contains public project documentation, not deployment credentials or private study material. It does not bundle model weights or a working application. Model licensing is separate from repository content.
