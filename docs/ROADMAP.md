# Roadmap

Updated: 2026-09-14

| Phase | Scope | Exit condition | Status |
| --- | --- | --- | --- |
| 0 | Project definition | Roles, constraints, roadmap, and threat model documented | Complete |
| 1 | Server foundation | Ubuntu server installed, storage/networking established, remote administration working | Complete per Phase 2 record |
| 2 | SSH, security, and reliability | Key authentication, firewall, private remote access, updates, health tooling, and power behavior checked | Complete per Phase 2 record |
| 3 | Local LLM and Postman | Local inference, authenticated API tests, private server-to-inference requests, and manual timeout/recovery verified | Complete |
| 4 | Backend API | Server-side inference integration, secret handling, health/error responses, and repeatable API tests | Next |
| 5 | Browser chatbot | Private browser chat through the backend, without exposing inference credentials to the browser | Planned |
| 6 | Document ingestion and retrieval | Notes/PDFs indexed with source metadata; retrieval evaluated; embedding placement decided | Planned |
| 7 | RAG and citations | Answers grounded in retrieved passages, verifiable citations, and insufficient-evidence handling tested | Planned |

Security, backups, privacy, and operational checks continue across all phases. Each completion claim must identify what was actually tested; planned features are not deployed features.
