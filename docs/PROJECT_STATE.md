# Project state

Updated: 2026-09-25
Current milestone: Phase 5 complete
Next phase: Phase 6 — PostgreSQL, tasks, and reminders

## Implemented backend

The Docker Compose-managed FastAPI backend provides `/health`, `/ready`, authenticated `/chat`, server-controlled model and personality configuration, bounded timeouts, controlled inference errors, optional bounded in-memory context, conversation isolation, stateless chat, and authenticated idempotent reset.

## Telegram adapter

The separate Compose service long-polls Telegram with an explicit user-ID allowlist and private-chat restriction. It supports `/start`, `/help`, `/status`, `/reset`, ordinary text, unsupported-input responses, and ordered splitting of long replies. Allowed users get stable backend conversation IDs. Backend prompt configuration failures are reported as such, rather than as LM Studio outages.

## Configuration and secrets

Public examples are committed in `.env.example`. Real `.env` values and the private personality prompt are ignored. The private prompt is mounted as a Compose secret and is not copied into the image.

## Validation

Phase 4 verification is recorded in [PHASE_4.md](phases/PHASE_4.md). The Phase 5 suite passed with 102 tests and 2 dependency warnings; both services built and started, the backend was healthy, and health/readiness returned HTTP 200. Phase 5 automated and live checks are recorded separately in [PHASE_5.md](phases/PHASE_5.md).

## Intentional limitations

- Context is process-local, non-persistent, and lost on restart.
- PostgreSQL, tasks, reminders, scheduling, documents, retrieval, and citations are not implemented yet.
- Inference is unavailable when the Windows GPU computer or LM Studio is unavailable.
- Telegram transport uses Telegram infrastructure. A process crash in the polling confirmation window can redeliver an update.

## Next work

Phase 6 adds PostgreSQL persistence, tasks, and reminders. See [Telegram operations](TELEGRAM.md) for the current deployment.
