# Architecture

Updated: 2026-09-25

## Component placement

| Component | Host | Status |
| --- | --- | --- |
| Secure administration and private networking | Ubuntu control server and Windows peer | Established |
| LM Studio and chat model | Windows inference computer | Operational when available |
| FastAPI backend | Ubuntu control server | Implemented in Phase 4 |
| Public personality prompt | Repository and backend image | Implemented |
| Private personality prompt | Ignored host file mounted as a Compose secret | Implemented |
| Temporary conversation store | Backend process memory | Implemented and bounded |
| Postman | Windows development computer | Verified through an SSH tunnel |
| Telegram adapter | Ubuntu control server | Implemented in Phase 5 |
| PostgreSQL, tasks, and reminders | Ubuntu control server | Phase 6 |
| Document retrieval and RAG | To be selected later | Deferred |

## Current request flow

The Telegram adapter long-polls Telegram, checks the sender's user ID against an explicit allowlist, and accepts only private chats. It maps each allowed user to `telegram:user:<user_id>` and calls the authenticated FastAPI backend. The backend combines the public prompt, private prompt secret, and optional bounded conversation history, then calls LM Studio over the private network. Telegram never calls LM Studio directly. Telegram message transport still uses Telegram's infrastructure.

## Backend endpoints

| Method | Endpoint | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | None | Confirm the backend process is running |
| `GET` | `/ready` | None | Check LM Studio and model availability |
| `POST` | `/chat` | Backend bearer key | Generate a response with optional temporary context |
| `DELETE` | `/conversations/{conversation_id}` | Backend bearer key | Idempotently clear one temporary conversation |

Omitting `conversation_id` keeps a chat request stateless. Supplied IDs are validated and isolate bounded in-memory conversations.

## Prompt handling

The public prompt is packaged with the backend. The private persona is ignored by Git and Docker build context, permission-restricted on the host, and mounted as a Compose secret. Prompt contents are not logged.

## Conversation behavior

History is isolated by ID, bounded by message count and characters, appended only after successful inference, removable through reset, and lost on restart. It is not durable persistence and is not shared across multiple backend processes.

`/reset` clears backend context for that user; it does not delete Telegram messages. The adapter processes updates in order, does not retry chat calls after an uncertain backend result, and advances its polling offset after handling each update. Without persistent update and idempotency storage, a crash after backend success but before Telegram confirms the offset can redeliver an update.

## Availability and network boundaries

The backend applies bounded connection/read timeouts and returns controlled errors for inference failures. It does not retry forever or silently use cloud inference. The deployed backend is loopback-bound; remote development uses SSH forwarding. LM Studio and the backend use separate bearer credentials.

The adapter is a separate Compose service with no published host port. Its Telegram token and backend credential are supplied through the ignored `.env`; its logs suppress routine `httpx` and `httpcore` request URLs. A backend prompt read failure returns a controlled `prompt_configuration_error`, which the adapter reports as a backend configuration issue.
