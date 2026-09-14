# Decision log

Updated: 2026-09-14

Phase 0–2 decision identifiers are retained from the supplied archive. Deployment-specific values are omitted. Later decisions amend the project direction without rewriting historical intent.

## Foundation decisions

| ID | Decision | Status / rationale |
| --- | --- | --- |
| D-001 | Separate control and inference hosts | Retained; keep control services independent of GPU-computer availability |
| D-002 | Ubuntu Server 24.04 LTS on the control host | Implemented; headless server foundation |
| D-003 | Keep a stable control-host identity | Implemented; actual hostname belongs in private operational notes |
| D-004 | Standard OpenSSH with key authentication | Reported verified in Phase 2; no direct root or password SSH |
| D-005 | Restrict SSH to approved network paths | Retained; no broad public SSH exposure; review historical LAN rules after moves |
| D-006 | UFW default-deny inbound | Reported verified in Phase 2; explicitly authorize services |
| D-007 | Tailscale for private cross-network access | Implemented and exercised in Phase 3 |
| D-008 | DHCP for LAN addressing | Retained; avoid dependence on one fixed LAN subnet |
| D-009 | Automatic security updates | Reported enabled in Phase 2; unattended reboot policy remains deliberate |
| D-010 | Disable suspend/hibernate on the control server | Reported verified in Phase 2; does not apply to the personal inference computer |
| D-011 | Temperature and disk-health monitoring | Reported established in Phase 2; not a substitute for backups |
| D-012 | Add security tools only for concrete needs | Retained; minimize unnecessary maintenance |
| D-013 | Preserve a working administrative session during access changes | Retained; validate and test a second session before closing the first |
| D-014 | Defer application components during Phase 2 | Historical; Telegram direction superseded by D-016; persistence technology still undecided |
| D-015 | Treat security as continuous | Retained; review new components, credentials, listeners, and backups |

## D-016 — Browser study assistant with RAG

Accepted. Build a browser-based study assistant and later add notes/PDF retrieval with citations. Postman and RAG are explicit learning goals. Telegram and Dialogflow are outside the current plan.

## D-017 — Keep LM Studio on Windows

Accepted and tested. Use LM Studio 0.4.24 (Build 1) for the initial inference service. It supports the demonstrated local chat and API workflow. Do not switch to standalone llama.cpp without a concrete requirement. The runtime version is an observed baseline, not an instruction to remain on it indefinitely.

## D-018 — Initial chat model and context

Accepted and tested. Use `HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive`, GGUF Q4_K_M, with a 4,096-token context. This reflects the owner's preference for reduced refusal behavior and the observed ability to run it on the available GPU. Reduced refusal does not establish accuracy, safety, or citation quality.

VRAM headroom is limited. Larger contexts and concurrent requests require measurement. No model weights are included in this repository; model licensing has not been reviewed here.

## D-019 — Native chat API with explicit reasoning control

Accepted for initial integration. Use `/api/v1/chat` with `reasoning: "off"` for ordinary short study requests. Tests through `/v1/chat/completions` reached output caps while generating drafting/reasoning text; native reasoning-off requests returned complete short answers. This is a tested configuration choice, not a claim that the compatible endpoint cannot support other configurations.

## D-020 — Layered private API access

Implemented for the tested path. Require a bearer token and restrict Windows inbound TCP/1234 by Tailscale interface and peer addresses. No public API exposure is intended. Keep CORS disabled and external tool/MCP access unnecessary to this phase disabled or denied. A narrow allow rule alone does not prove that no overlapping rule grants wider access.

## D-021 — Credential and publication hygiene

Accepted. Keep tokens in local secret storage, not committed requests or documentation. Postman uses a Local Vault reference. Temporary test-shell credentials are cleared after use. Backend secret storage is deferred to Phase 4. Raw screenshots, private addresses, user identities, notes, PDFs, and logs are not public repository content.

## D-022 — Intermittent inference is normal

Accepted; manual failure/recovery tested, backend handling pending. Use bounded timeouts and clear unavailable responses. No infinite retries or automatic cloud fallback. The control server remains independent of inference availability.

## D-023 — Defer embedding architecture

Accepted. Embedding location and retrieval stack will be selected in the document/RAG phases. Presence of an embedding model in the runtime does not select it for the project or verify embeddings.
