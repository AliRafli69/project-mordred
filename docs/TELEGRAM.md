# Telegram adapter operations

Updated: 2026-09-25

The adapter long-polls Telegram from a separate Docker Compose service. It has no published inbound port. Telegram messages pass through Telegram's infrastructure; only backend-to-LM Studio inference runs over the private path.

## Private configuration

Copy the placeholders in `.env.example` into the ignored `.env` and supply the real values privately. `MORDRED_TELEGRAM_BOT_TOKEN` is the bot token. `MORDRED_TELEGRAM_ALLOWED_USER_IDS` is a comma-separated list of positive numeric Telegram **user** IDs, not chat IDs or usernames. The adapter permits only these users in private chats; group and other users' messages never reach the backend. Set `MORDRED_TELEGRAM_BACKEND_API_KEY` to the same backend key used by the backend. `MORDRED_TELEGRAM_BACKEND_BASE_URL` normally remains `http://backend:8000` inside Compose.

Keep `.env` readable only by the operator (for example, mode `600`). The private prompt remains at the ignored `prompts/system_prompt.private.txt`, mounted into the backend as a Compose secret and excluded from the image. The backend runs as UID/GID `10001`; the host file must be readable by that group. On this deployment the file uses owner UID `1000`, group GID `10001`, mode `640`. Never print the token, backend key, or prompt to troubleshoot them.

## Deploy and inspect

Run these commands on the **HP Ubuntu — Bash** host from the repository root after private configuration exists:

```bash
docker compose config --quiet
docker compose build backend telegram-adapter
docker compose up -d backend telegram-adapter
docker compose ps
docker compose logs --tail=50 telegram-adapter
curl --fail --silent http://127.0.0.1:8000/health
curl --fail --silent http://127.0.0.1:8000/ready
```

If `MORDRED_BIND_PORT` differs from the example, adjust the loopback port in the two `curl` commands. `/ready` returns HTTP 503 while the G14 or LM Studio is unavailable; `/health` can remain healthy. Avoid `docker compose config` without `--quiet`, because it can render configured environment values. Do not paste raw container logs into public issues.

## Behavior

`/start` introduces the bot and `/help` lists commands. `/status` reports backend and local inference availability. Ordinary text calls the backend with a stable `telegram:user:<user_id>` conversation ID, so follow-up questions use bounded temporary context. `/reset` clears that backend context for the user; it does not delete Telegram messages. Backend restarts also erase all temporary context. Unsupported input gets a plain-text explanation. Replies longer than Telegram's 4096-character limit are split in order.

When the G14 sleeps, disconnects, or LM Studio stops, chat reports local inference unavailable or timed out. A prompt-file read failure instead asks the operator to check backend prompt configuration. Backend authentication and protocol errors have separate messages. The adapter does not automatically repeat a chat request after a timeout because the backend may already have processed it.

## Troubleshooting and limits

- If the adapter fails to start, check that the bot token, backend key, and allowlist are present and valid in the ignored `.env`; inspect short, sanitized logs.
- If chat reports prompt configuration unavailable while `/health` and `/ready` succeed, check the private prompt file's existence and group readability for backend GID `10001`. Do not display its contents.
- If `/status` reports local inference unavailable, check whether the G14 is awake, connected, and serving the configured model in LM Studio.
- If delivery to Telegram fails, an already handled update is consumed. An adapter crash after backend success but before Telegram confirms the polling offset can redeliver an update. Persistent update and idempotency storage are deferred beyond Phase 5.
