# Project Mordred

A private, self-hosted personal assistant built incrementally to learn backend API development, local LLM integration, Telegram bots, persistence, and retrieval-augmented generation (RAG).

## Status

Phase 4 is complete. The Ubuntu control server now runs a containerized FastAPI backend with health and readiness checks, authenticated chat, public/private personality assembly, controlled inference settings, bounded temporary conversation context, and authenticated conversation reset.

The backend uses LM Studio on a separate Windows GPU computer over a private Tailscale path. Temporary context is held only in backend memory and disappears on restart.

Phase 5 adds Telegram as the first user-facing adapter. Phase 6 adds PostgreSQL-backed persistence, tasks, and reminders. Document retrieval and RAG remain later work.

## Architecture

- **Control server:** Ubuntu Server on an always-on HP Pavilion.
- **Inference computer:** Windows on an ASUS ROG G14 with an RTX 4060 Laptop GPU; runs LM Studio and may sleep or disconnect.
- **Private transport:** Tailscale, host firewalls, and separate API credentials.
- **Current clients:** Postman and authenticated HTTP clients.
- **Next client:** Telegram bot adapter.

The backend owns inference credentials, personality assembly, generation limits, conversation bounds, and error translation. Clients cannot supply their own model or system prompt.

## Documentation

- [Project brief](docs/PROJECT_BRIEF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Roadmap](docs/ROADMAP.md)
- [Decision log](docs/DECISIONS.md)
- [Current state](docs/PROJECT_STATE.md)
- [Phase 3 validation](docs/phases/PHASE_3.md)
- [Phase 4 validation](docs/phases/PHASE_4.md)
- [Postman practice](postman/README.md)
- [Publication checklist](docs/PUBLISHING.md)

This public repository excludes deployment credentials, private personality text, private addresses, personal documents, saved conversations, and model weights.
