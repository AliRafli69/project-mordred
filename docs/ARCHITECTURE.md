# Architecture

Updated: 2026-09-14

## Component placement

| Component | Host | Status |
| --- | --- | --- |
| Secure administration and private networking | Ubuntu control server and Windows peer | Established |
| LM Studio and chat model | Windows inference computer | Tested |
| Postman | Windows development computer | Tested |
| Custom backend API | Ubuntu control server | Phase 4 |
| Browser interface hosting | Ubuntu control server | Phase 5 |
| Documents and retrieval index | Ubuntu control server | Phases 6–7 |
| Embedding generation | Undecided | Deferred |

## Request flow

Currently, Postman on the inference computer and manual HTTP requests from the control server can reach LM Studio. The planned application flow is browser → control-server backend → private inference API. The backend, not the browser, will hold the inference credential.

LM Studio's local development base URL is `http://127.0.0.1:1234`. Cross-machine clients use the inference computer's private Tailscale address, intentionally omitted here. Loopback refers to the machine making the request; it is not the remote inference address.

## Networking and authentication

- Standard OpenSSH uses key authentication; Tailscale supplies its network transport, not a replacement for SSH authentication.
- The Phase 2 record reports UFW default-deny inbound with explicitly allowed administrative paths. Those historical rules must be reviewed after network changes.
- The Phase 3 Windows rule allows TCP port 1234 on the Tailscale interface, scoped to the control server's source address and inference computer's destination address.
- LM Studio requires a bearer token. Network reachability alone does not grant API access.
- LAN-serving mode must not be mistaken for Tailscale-only binding. Host firewall scope remains important, including other overlapping rules and IPv6 listeners.
- No public forwarding or cloud-inference fallback is part of the design.

## Availability contract (planned backend behavior)

The inference computer may sleep, disconnect, or stop its model service. The backend must apply bounded connection and response timeouts, distinguish authentication errors from reachability failures, and return a clear unavailable response. It must not retry indefinitely or silently send prompts elsewhere. Recovery should be possible when the inference service returns.

Manual timeout and recovery checks were performed in Phase 3; application-level handling is not implemented yet.
