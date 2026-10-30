---
title: "H3-A exact-client before/after evidence for the server/discover compatibility response"
date: 2026-10-29
status: accepted
related:
  - 056.011-T
  - 052-S
  - docs/decisions/2026-08-29-mcp-serve-discover-preinitialize-evidence.md
---

## Summary

The candidate response shape, a correlated JSON-RPC `-32601` (method not
found) error to a pre-`initialize` `server/discover`, is accepted by the
exact Copilot CLI (`GitHub Copilot CLI 1.0.105`, `C:\Tools\copilot.exe`).
Before the change the client's MCP status for the server is `failed`; after
the change it is `connected`, which the client reports only once the
`initialize` handshake has completed.

## Method

The evidence path is the transparent `mcp-probe exact-cli` runner
(`056.001-T` over the `056.022-T` wrapper and `056.023-T` redacting
observer), run twice against the exact inner production executable
built from the same tree:

* before: `serve` with the direct `rmcp::serve_server(server, stdio())`
  composition (run nonce `before-056011`)
* after: `serve` with the private `DiscoverCompat` adapter (run nonces
  `after-056011` and `after2-056011`, same result both times)

The probe's temporary configuration and wrapper were used only for this
diagnostic path. They do not substitute for restored-production T4
evidence.

## Observations

| Run | Treatment `last_mcp_status` | Frame evidence |
|---|---|---|
| before | `failed` | one client-to-server frame: `server/discover`, `id: 0`, no `initialize` correlation |
| after (x2) | `connected` | not persisted (see limitation) |

Parameter shape of the probe request: `params: {}` (see the 2026-08-29
evidence note). The before run shows no re-probe before the connection
closed. Re-probe cadence after an accepted `-32601` was not observed
because the client proceeds to `initialize`.

## Limitation

In the after runs the wrapper's redacted evidence file was not written:
the wrapper persists its summary only when its pump returns, and the
connected leg ends with the wrapper terminated by the client session
teardown. The frame-level method/id order for the after run is therefore
not captured, and acceptance rests on the client's own `connected` status.
The probe tooling is owned by `049-S` and is out of scope for this change.
Restored-production acceptance (T4, `056.004-T`) remains the owner of final
frame-level proof.

## Decision

Keep `-32601` as the compatibility response. No `DiscoverResult` payload is
produced and no other pre-`initialize` method is intercepted.
