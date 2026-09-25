# Phase 5 — Telegram adapter

Recorded: 2026-09-25
Status: complete, with remaining manual scenarios listed below

## Exit condition

An explicitly allowed Telegram user can chat in a private conversation, retain bounded temporary context, reset it, check status, and receive clear unavailable responses while the G14 or LM Studio is offline.

## Delivered

- Separate long-polling Compose service with no published port, explicit user-ID allowlist, private-chat restriction, and backend bearer authentication.
- `/start`, `/help`, `/status`, `/reset`, ordinary text, unsupported-input guidance, and ordered splitting of long replies.
- Stable `telegram:user:<user_id>` backend conversation mapping; ordered update processing; no blind retry after uncertain chat completion.
- Controlled responses for backend timeout, inference outage, and prompt configuration failure. Routine HTTP client logs are restricted to warning level to avoid exposing Telegram request URLs.

## Automated verification

In this checkout, the owner ran the Docker test image and reported `102 passed, 2 warnings in 1.00s`. Both warnings were dependency deprecations in FastAPI/Starlette test-client code. `docker compose config --quiet` passed. The test and runtime images built successfully, and Compose started both services. The backend reported healthy; the adapter was running at the time of `docker compose ps`. `/health` returned HTTP 200 with status `ok`, and `/ready` returned HTTP 200 with inference `available`. Python syntax parsing passed for all 31 application and test files; staged plus unstaged `git diff --check` passed.

A review of all added diff lines found no Telegram bot-token shape, provider token shape, private IPv4 address, PEM private-key marker, or non-placeholder credential assignment. `.env` and the private prompt file are ignored and untracked. The review patch must be regenerated after documentation edits and reviewed before any commit or push.

## Live validation

The earlier Phase 5 session confirmed `/start`, `/status` across backend/inference availability states, ordinary chat, follow-up recall, `/reset`, post-reset forgetting, and a clear G14/LM Studio offline response. It also confirmed that the updated private personality was active through a fresh conversation, and that backend and adapter containers were running. These are historical live observations, distinct from the current automated checks.

Live long-reply splitting and unsupported-input handling were not recorded as manually tested. The new prompt configuration message has a focused automated regression test; a live prompt-read failure has not been repeated for this change.

## Limits

Backend conversation state is in memory and disappears on restart. `/reset` clears backend context only; Telegram messages remain. Telegram transport still passes through Telegram infrastructure. Without persistent update and idempotency storage, a crash after backend success but before Telegram offset confirmation can redeliver an update. PostgreSQL, tasks, reminders, and RAG remain outside Phase 5.
