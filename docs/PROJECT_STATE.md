# Project state

Updated: 2026-09-14  
Current milestone: Phase 3 complete  
Next phase: Phase 4 — backend API

## Foundation inherited from Phase 2

The supplied Phase 2 record reports Ubuntu Server installation, key-only non-root SSH, restrictive UFW rules, Tailscale, unattended security updates, sensor and disk-health tooling, and disabled server suspend/hibernate. These are historical verification results, not a fresh audit of every setting in Phase 3.

Phase 3 re-established working SSH/private connectivity. Device identities, exact administrative rules, addresses, and raw health readings are deliberately excluded from this public record.

## Phase 3 configuration

| Item | Recorded value |
| --- | --- |
| Inference OS | Windows 11 |
| Inference RAM | 32 GB |
| GPU | RTX 4060 Laptop GPU, 8,188 MiB VRAM |
| NVIDIA driver observed | 591.86 |
| Runtime | LM Studio 0.4.24 (Build 1), Stable channel |
| Model | HauhauCS/Qwen3.5-9B-Uncensored-HauhauCS-Aggressive |
| API identifier | `qwen3.5-9b-uncensored-hauhaucs-aggressive` |
| Format / quantization | GGUF / Q4_K_M |
| Configured context | 4,096 tokens |
| Tested native chat endpoint | `POST /api/v1/chat` |
| Ordinary test request | Reasoning off, non-streaming |

## Verified outcomes

- Local chat generation and GPU activity during generation.
- Authenticated Postman model listing and native chat generation.
- Collection variables and four passing response tests.
- Authenticated control-server model listing and chat generation over Tailscale.
- Missing-token rejection by the inference API.
- Connectivity over a relayed Tailscale path during the reported hotspot test; authenticated inference on that specific network was not separately recorded.
- Bounded connection timeout followed by successful model-list recovery.
- Temporary token removed from the test shell.

See [Phase 3 validation](phases/PHASE_3.md) for observations and limitations.

## Open items

- Campus-network testing, sleep/wake testing, and startup automation.
- Sustained-load performance and exact GPU layer offload measurement.
- Audit effective listener/firewall exposure, overlapping rules, and unauthorized-peer access.
- Recheck administrative firewall rules after network changes.
- Confirm credential rotation if any token was entered directly into shell history; clearing a variable does not revoke a token or remove historical copies.
- Define backend credential storage, timeouts, and log retention.
- Review tailnet access policy/MFA and plan encrypted backups before importing valuable data.
- Choose embedding placement and retrieval stack later. A downloaded embedding model is not an implemented RAG pipeline.
