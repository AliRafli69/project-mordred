# Threat model

Updated: 2026-09-14  
Coverage: server foundation and Phase 3 inference/API prototype

## Assets and boundaries

Protect administrative keys, API tokens, private prompts and responses, future study documents/indexes, and service availability. Relevant boundaries include the local network, tailnet membership, each host's firewall, API authentication, browser/backend separation, and future retrieved-document content.

Potential threats include compromised peer devices, stolen credentials, untrusted networks, vulnerable dependencies, malicious model/document inputs, physical theft, and configuration mistakes.

## Controls and residual risk

| Risk | Recorded control | Limitation / next action |
| --- | --- | --- |
| Unauthorized administration | Phase 2 key-only non-root SSH and restrictive UFW | Recheck effective rules after network changes; review tailnet membership and MFA |
| Unauthorized model API use | Required bearer token and peer-scoped Windows firewall rule | Audit overlapping rules/listeners and test unauthorized peers; tailnet membership is not sufficient authorization |
| Credential disclosure | Local Vault reference and temporary shell-variable cleanup | Never commit values; revoke exposed tokens; shell history and logs may retain earlier copies |
| Prompt disclosure | Local inference and private inter-host path | Local logs, saved responses, request sync, backups, and plugins can still disclose content |
| Inference unavailable | Manual timeout and recovery tests | Backend error handling and actual sleep/wake recovery remain pending |
| Resource exhaustion | Small test prompts and 4,096-token context | Concurrency, queue limits, rate limits, and sustained-load behavior need evaluation |
| Incorrect model answers | No claim that reduced refusal improves reliability | Evaluate study-answer quality; citations and grounding are not implemented |
| Tool abuse / document prompt injection | No tool execution needed for Phase 3 | Treat future retrieved text as untrusted data; authorize tools separately from model output |
| Disk loss / physical compromise | Phase 2 health tooling | Monitoring is not backup or encryption; plan protected backups before valuable ingestion |

## Operating rules

- Keep inference credentials server-side when the browser interface is added.
- Do not assume private addressing or a single firewall rule proves isolation.
- Keep prompts harmless in API practice. Secret storage does not make all saved request content private.
- A request using `store: false` is not evidence that every local log or client history is disabled.
- Keep a working administrative session during firewall/SSH changes and verify access independently.
- Model capabilities advertised by metadata are not tested capabilities.

This document describes controls and unresolved risks, not a comprehensive penetration test or a guarantee of security.
