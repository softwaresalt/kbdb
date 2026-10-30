---
title: "056.004-T T4 restored-production acceptance evidence"
description: "Evidence record for the reversible kbdb production-entry restoration, the PTY capture tooling, and three exact-client /mcp show sessions plus the sequential T1 wire control"
doc_type: "decision"
decision_status: "decided"
session_date: "2026-10-30"
agent: "ship"
backlog_refs:
  - "055-S"
  - "056.004-T"
  - "056-F"
tags:
  - "t4"
  - "056-f"
  - "runtime-verification"
---

## Authorization context

The operator reasserted the dark-factory pipeline at 2026-10-30T07:21:17Z after
the concrete recovery proposal. The Orchestrator then directed two reversible
steps: back up and restore the direct `kbdb` launch, and add workspace-local
terminal capture. This record quotes no approval beyond that sequence.

## Production entry restoration

Scope: only the `mcpServers.kbdb` launch fields in `.mcp.json`. Every other
entry and the metadata fields `type`, `x-kbdb-managed`, and `tools` are
unchanged.

| Field | Before | After |
|---|---|---|
| `command` | `bun` | absolute `.kbdb\bin\kbdb.exe` under the workspace |
| `args` | `.copilot/graphtor-mcp-shim.cjs`, `kbdb`, `serve` | `serve` |

* Original `.mcp.json` SHA-256: `533B43AA35E3119A63CBAC4E556E7E183BA73D36291E469A816CB1F5782FD705`
* Restored `.mcp.json` SHA-256: `0FFC9431E4493391EC2019787D1A37CE5F6A8CA606C28DDA388F9F83179E0F2A`
* Shim file `.copilot/graphtor-mcp-shim.cjs` is untouched (SHA-256 `4F47AA2548D9F9C70D6B908885BFBF07F0B84EF02354A6034EA42381E4A8DA7E`).
* The shim was a server-side stdio wrapper: it spawned `kbdb serve`, proxied
  its stdio, and injected an `initialized` message.
* Verified byte-exact backup: `logs/t4/backup/mcp.json.20261030T072800Z.bak`
  (ignored directory, hash recorded in `logs/t4/backup/hashes.txt`).
* Rollback: copy the backup over `.mcp.json`, or revert the commit that
  carries the entry change.

### Delivered binary

The installed `C:\Tools\kbdb.exe` (29,646,336 bytes, dated 2026-10-26) predates
the H3-A merge and is not delivered code, and it sits outside the workspace,
so it was neither used nor overwritten. The delivered binary is the workspace
release build of the head (`kbdb 0.3.1`, SHA-256
`983E1A84FC7C7A13485B565CDB194FBEE6B54403F7D965F4E373584F13A87546`), copied
to the managed location `.kbdb\bin\kbdb.exe`. That is the path the installer's
binary resolution ladder prefers, so the entry uses an absolute command.

## Capture method

A pywinpty PTY hosts the exact `C:\Tools\copilot.exe` (GitHub Copilot CLI
1.0.105, SHA-256 `AB6D710D551C137C766A6C8EF6EE2E7779C106870C96B9A91A91FA17B9748624`) interactively. pyte rebuilds the screen, and the real `/mcp show kbdb`
slash command is typed. No `-p` prompt and no model call occur. The PTY host
is client terminal capture, not an MCP server wrapper: the server command,
args, environment, and cwd are the unmodified entry. Pinned dependencies live
in `tools/t4-capture/requirements.txt` (pywinpty 3.1.0, pyte 0.8.2,
wcwidth 0.9.3) and install into the ignored `logs/t4/venv`.

Fields evaluated (only those the screen exposes): entry name, `status` equal
to `connected`, `serverMetadata` present (the initialize result), no OS error
232 or failed-connection text, and the advertised tool list and count.
Process logs are not parsed.

## Runs

Run directory `logs/t4/runs/20261030T073853Z` (ignored), head
`1571f809ed2046104d6eeb9af1059a4513f79a98`, config SHA-256 as above, all
sessions gate off with no diagnostic sink.

| Session | Copilot PID | Server PID | Server start (UTC) | `/mcp show` status | Tools |
|---|---|---|---|---|---|
| 1 | 5688 | 36396 | 2026-10-30T08:03:52Z | connected, serverMetadata present | 8 |
| 2 | 20680 | 40432 | 2026-10-30T08:04:06Z | connected, serverMetadata present | 8 |
| 3 | 18876 | 36204 | 2026-10-30T08:04:19Z | connected, serverMetadata present | 8 |

Per session the runner also verified: the server's executable hash equals the
entry's binary hash, the server is a direct child of the Copilot process
(Win32_Process table; any intermediate non-Copilot process is refused), and the
server's current directory read from its process block equals the canonical
workspace.

Advertised tools: `get_chunk_by_id`, `get_document`, `get_status`,
`list_sources`, `research_topic`, `search_local_docs`, `search_semantic`,
`traverse_doc_links`.

### T1 wire control

`tests/t4_production_control_test.rs` runs the `056.002-T` read-only control
against the same delivered binary and workspace, sequentially before and after
the sessions: `initialize` returned `jsonrpc` 2.0 with the correlated id and
`protocolVersion` `2025-06-18` (server `kbdb` 0.3.1), `tools/list` equals the
manifest, and one `get_status` returned non-empty text with a protocol-clean
stdout. The recorded child exit code 1 is the driver's teardown signal, not a
protocol failure.

## Limitations and notes

* The first cold control run timed out at 60 seconds in `get_status` because
  the workspace holds a 1.18 GB database. The runner now allows 300 seconds;
  a warm run completes in about 23 seconds. Server latency is unchanged and no
  product change was made.
* The 24-hour healthy rule is satisfied by three starts within minutes; the
  observation window is recorded, not extended.
* The three `052-S` treatment runs did not count toward this result.
* The committed `.mcp.json` now carries a machine-specific absolute command path (as the installer does for a managed binary), so the T4 gate only works from this checkout location.
* After each session the runner stops only the recorded server PID, and only while it still runs the delivered executable; the runner now confirms every client and server PID is gone before continuing.

## Corrective pass: owned-process cleanup (2026-10-30)

Review found that the capture tool's cleanup identified the recorded server PID
by executable path only and then ran `Stop-Process -Id <pid> -Force`. If that PID
were reused by another client's `kbdb` with the same executable, the tool could
have terminated an unrelated server. This pass completes the existing
owned-child-only cleanup contract; it is not a general PID-management feature.

* Fix: `OwnedProcess` in `tools/t4-capture/t4_capture.py` opens a verified OS
  process handle right after the server is identified (image name and creation
  time checked against the recorded values at their shared microsecond precision,
  compared as exact integers). While held, the OS
  cannot reuse that PID. Cwd reads, exit checks, and termination all act on that
  handle; no PID-based kill remains. If ownership cannot be proven the open fails
  closed, nothing is terminated, and the error names the unowned server PID.
  A creation-time check alone would still race, so the handle is what binds
  the identity.
* Tests (red then green): five OS-boundary tests using only a `ping.exe` child the
  test owns: verified terminate, same-exe/different-creation refusal with no
  termination, different-exe refusal, unopenable PID, and a closed-handle terminate
  that surfaces an error, and a 10 ms creation-time mismatch refusal. Python suite: 21
  existing plus 11 new, 32 pass. A final strict run, `20261030T213606Z`, passed on the final
  harness.
* A review-fix and a flake: a status block rendering before the tools block made one
  session fail closed (tool list missing). The capture now waits until both blocks
  render (`mcp_show_rendered`, three tests). That failed run is a real recorded
  failure, not hidden.
* Real strict reruns with the corrected harness, sequential wire controls before and
  after each: `20261030T212815Z` and `20261030T212908Z` all passed (three
  `/mcp show kbdb` sessions each, connected, 8 tools, no 232, owned cleanup
  confirmed, no leftover PIDs). Latest run sessions: Copilot PIDs 3076, 34648, 44096;
  server PIDs 7604, 33716, 7776. Copilot CLI 1.0.105; server executable SHA-256 and
  config SHA-256 unchanged from above. The three earlier runs remain valid
  historical evidence.
