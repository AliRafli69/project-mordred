# Project brief

Updated: 2026-09-14

## Purpose

Build a private study assistant with a browser-based chatbot, then add RAG to answer questions from personal notes and PDFs with citations. Learning Postman, backend API development, and RAG is an explicit part of the project.

## Design constraints

- Keep prompts and inference on user-controlled machines.
- Use an always-on Ubuntu control server and a separate Windows GPU inference computer.
- Treat inference availability as intermittent; the GPU computer is also a personal development laptop.
- Keep the model API private; do not expose it directly to the public Internet.
- Add components in small, testable phases, with documented decisions and recovery behavior.

## Intended capabilities

1. A private browser chat interface backed by a server-side API.
2. Local LLM inference with explicit availability and error reporting.
3. Document ingestion, retrieval, and answers grounded in retrieved passages.
4. Citations that identify the supporting document and location.
5. Repeatable API tests and measurable retrieval/answer quality.

## Scope boundaries

Phase 3 establishes inference and API basics only. The browser interface belongs to Phase 5, and document ingestion and RAG to Phases 6–7. Telegram and Dialogflow are not part of the current implementation plan. Embedding placement, backend framework, database, and retrieval technology are not selected here.

Public documentation excludes device identities, account details, private addresses, credentials, personal documents, and raw operational logs.
