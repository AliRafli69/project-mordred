# Postman practice

Postman was used for direct LM Studio exercises in Phase 3 and Mordred backend acceptance checks in Phase 4. Real tokens, private addresses, private prompts, and saved private responses must not be committed.

## Phase 3

Direct LM Studio tests covered model listing, model details, authenticated native chat, reasoning-off behavior, and missing-token rejection.

## Phase 4 environment

| Variable | Example | Handling |
| --- | --- | --- |
| `base_url` | `http://127.0.0.1:18000` | Local end of an SSH tunnel |
| `backend_api_key` | Not recorded | Secret environment value |

The development computer forwarded local port 18000 to backend loopback port 8000 over SSH. Public documentation omits real usernames and hostnames.

## Acceptance sequence

1. `GET {{base_url}}/health` returned HTTP 200.
2. Authenticated `POST {{base_url}}/chat` started a harmless test conversation.
3. A second request with the same conversation ID recalled its temporary codename.
4. Authenticated `DELETE {{base_url}}/conversations/postman-conversation-a` returned reset status.
5. The next request no longer recalled the codename.

## Export safety

Inspect variables, authorization, scripts, examples, and saved responses before committing an export. Remove tokens, private addresses, identities, and personal prompts. Never export secret environment values or Local Vault contents.
