# Postman practice

The manually tested collection is named `Mordred`. Its actual export was not supplied with the source documents, so this package does not invent an exported collection or claim a reconstructed one was tested.

## Recorded setup

| Setting | Value |
| --- | --- |
| Collection variable `base_url` | `http://127.0.0.1:1234` for same-computer tests |
| Collection variable `model` | `qwen3.5-9b-uncensored-hauhaucs-aggressive` |
| Bearer token field | `{{vault:mordred-lm-token}}` — reference only, never the secret |
| List models | `GET {{base_url}}/v1/models` |
| Model details | `GET {{base_url}}/api/v1/models` |
| Native chat | `POST {{base_url}}/api/v1/chat` |

The native reasoning-off test checked HTTP 200, expected model identity, non-empty answer content, and zero reasoning-output tokens. A missing token was also rejected during manual tests.

## Before committing an export

Export the actual collection, then inspect its full JSON, including authorization, scripts, variables, descriptions, and saved response examples. Remove real credentials, private addresses, identity metadata, and personal prompts. Keep only placeholders and harmless practice inputs. Do not export Local Vault contents or private environments.

Local Vault protects the secret; it does not guarantee that collection content, examples, or other client data will never synchronize. Review client/workspace settings before using private notes in any request.
