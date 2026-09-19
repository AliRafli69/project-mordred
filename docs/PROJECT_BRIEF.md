# Project brief

Updated: 2026-09-19

## Purpose

Build a private, self-hosted personal assistant named Mordred using an always-on Ubuntu control server and a separate Windows GPU inference computer. Learning backend APIs, Postman, Telegram integration, persistence, and RAG is part of the project.

## Design constraints

- Keep prompts and inference on user-controlled machines.
- Treat GPU inference as intermittently available.
- Keep LM Studio and backend administration off the public Internet.
- Require authentication even across private networking.
- Keep public instructions separate from the ignored private persona.
- Add components in small, tested, documented phases.
- Do not introduce persistent storage before its planned phase.

## Intended capabilities

1. A server-controlled local-LLM backend.
2. Natural Telegram conversation through a thin adapter.
3. PostgreSQL-backed tasks, reminders, and selected durable data.
4. Later document retrieval and source-grounded answers.
5. Repeatable automated and Postman tests.
6. Clear behavior when inference is unavailable.

## Current boundary

Phase 4 provides the backend, temporary context, reset behavior, prompt assembly, authentication, and failure handling. Phase 5 adds Telegram. Phase 6 adds PostgreSQL-backed persistence, tasks, and reminders. RAG remains later work.

Public documentation excludes credentials, private prompts, private addresses, personal conversations, documents, and raw operational logs.
