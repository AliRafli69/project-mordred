# Phase 3 — Local LLM setup and Postman basics

Recorded: 2026-09-14  
Status: core milestone complete

## Exit condition

Run the selected model locally, exercise authenticated APIs in Postman, obtain a generated answer from the control server over the private connection, and demonstrate bounded failure and recovery. Document results without claiming the backend, browser chatbot, or RAG is already implemented.

## Completion checklist

- [x] Check inference OS, RAM, GPU/driver/VRAM, and available storage.
- [x] Load the selected Q4_K_M model with a 4,096-token context.
- [x] Generate local chat responses and observe GPU activity.
- [x] List models and request chat responses in Postman with authentication.
- [x] Use collection variables and response assertions; four tests passed.
- [x] Test native reasoning-off requests.
- [x] Verify private peer connectivity and scoped Windows firewall filters.
- [x] Obtain authenticated model listing and generation from the control server.
- [x] Observe API reachability over a relayed cross-network path.
- [x] Observe bounded timeout and subsequent model-list recovery.
- [x] Clear the temporary credential from the active test shell.

## Test observations

| Test | Observation | Interpretation |
| --- | --- | --- |
| Local generation monitor | Approximately 42–61% GPU utilization; roughly 7,700 MiB allocated out of 8,188 MiB | Consistent with GPU-assisted generation; not proof of full layer offload |
| Fresh runtime chat | 23.18 tokens/s, 169 output tokens, normal EOS | Basic local generation works |
| Native Postman chat | 110 output tokens, 22.14 tokens/s, 0.246 s time to first token, zero reasoning tokens | Complete short response with reasoning disabled |
| Postman assertions | 4/4 passed | Checked HTTP success, model identity, non-empty message, and zero reasoning tokens |
| Control-server chat | 55 output tokens, 15.72 tokens/s, 0.710 s time to first token | Authenticated private inference works |
| Missing credential | API returned `invalid_api_key` | Server was reachable and rejected the request |
| Unavailable service/path | Connection timed out after approximately 5 seconds; curl exit 28 | Bounded network failure observed; cause cannot be inferred from timeout alone |
| Recovery | Model list returned; curl exit 0 | Access restored |
| Reported hotspot test | Tailscale relay active; unauthenticated request reached API and was rejected | Cross-network reachability, not a separately recorded authenticated generation test |

These are short functional observations, not controlled benchmarks. Workload and concurrent personal-computer use varied. Inference statistics do not isolate network latency. curl exit 0 alone is not proof of HTTP success; without failure-on-HTTP-error options, curl may return 0 for an authentication-error response.

## API learning outcomes

- The model is the weights; LM Studio is the runtime that executes them.
- The API is the HTTP interface; Postman is a client for exercising it.
- GET model listing checks access and metadata, not answer generation.
- POST chat supplies input and generation settings, then returns generated text and statistics.
- Authentication, transport success, and valid answer content are separate checks.
- Context size and output-token cap are different constraints. Earlier compatible-endpoint tests hit output caps; this did not prove the loaded context was full.

## Deferred verification

Image input, exact GPU layer offload, sustained workloads, campus connectivity, actual sleep/wake behavior, automated startup, and negative network-access tests remain open. Metadata reporting vision, tool use, or embedding models is not verification of those features.
