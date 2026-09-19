# Roadmap

Updated: 2026-09-19

| Phase | Scope | Exit condition | Status |
| --- | --- | --- | --- |
| 0 | Project definition | Roles, constraints, roadmap, and threat model documented | Complete |
| 1 | Server foundation | Ubuntu installed and remote administration working | Complete per Phase 2 record |
| 2 | SSH, security, and reliability | Key authentication, firewall, Tailscale, updates, health tooling, and power behavior checked | Complete per Phase 2 record |
| 3 | Local LLM and API practice | Local inference, authenticated API tests, private cross-host requests, and recovery checks demonstrated | Complete |
| 4 | Backend and temporary context | Authenticated backend chat, prompt separation, readiness/error handling, bounded context, reset, automated tests, and Postman validation | Complete |
| 5 | Telegram adapter | Authorized Telegram user can chat, retain temporary context, reset it, and receive unavailable responses | Next |
| 6 | PostgreSQL, tasks, and reminders | Durable storage, migrations, task lifecycle, reminder delivery, restart recovery, and backup/restore tested | Planned |
| 7 | Document ingestion and retrieval | Notes/PDFs indexed with source metadata and retrieval evaluated | Planned |
| 8 | RAG and citations | Answers grounded in retrieved passages with verifiable citations | Planned |

A browser interface may be considered later, but Telegram is the first planned user-facing adapter. Security, privacy, backups, and operational checks continue across every phase.
