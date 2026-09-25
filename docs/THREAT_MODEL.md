# Threat model

Updated: 2026-09-25
Coverage: server foundation through Phase 5 Telegram adapter

## Assets

Protect SSH keys, backend and LM Studio credentials, personality prompts, messages, responses, Telegram credentials and user identifiers, future PostgreSQL data, documents, indexes, and service availability.

## Controls and residual risk

| Risk | Current control | Limitation or next action |
| --- | --- | --- |
| Unauthorized administration | Key-only non-root SSH and firewall baseline | Recheck rules after network changes |
| Unauthorized backend use | Loopback binding and bearer authentication | Rate controls remain future work |
| Unauthorized Telegram use | Explicit user-ID allowlist and private-chat-only check before backend calls | A compromised allowed account can use the bot; protect the account and token |
| Telegram transport privacy | No direct Telegram-to-LM Studio access | Messages still traverse Telegram infrastructure |
| Unauthorized LM Studio use | Bearer token and private-network firewall scope | Audit overlapping rules and listeners |
| Credential disclosure | Ignored `.env`, secret types, no committed values | Rotate exposed values and avoid logs/screenshots |
| Private persona disclosure | Ignored file, restricted permissions, secret mount | Host compromise and backups remain risks |
| Conversation leakage | Validated IDs and isolated bounded histories | IDs are not authentication; clients must own their mapping |
| Inference unavailable | Bounded timeouts and controlled responses | Telegram must avoid infinite retries |
| Resource exhaustion | Message, history, character, timeout, and output limits | Add concurrency and rate controls as usage grows |
| Incorrect answers | No reliability claim based on model branding | Evaluate accuracy; RAG is not implemented |
| Prompt injection | Clients cannot replace the system prompt | Future retrieved text remains untrusted |
| Data loss | Temporary context is deliberately disposable | Plan backups before persistent data |
| Duplicate update after crash | Ordered polling and no blind chat retry | An update can be redelivered after backend success and before offset confirmation; persistent idempotency is deferred |

## Operating rules

- Never commit real credentials or the private persona.
- Do not log tokens, prompt contents, or private conversations.
- Keep model and system configuration server-controlled.
- Treat Telegram identity and backend authentication as separate controls.
- Do not infer isolation merely from private addressing.
- Do not persist valuable personal data without backup and recovery plans.
