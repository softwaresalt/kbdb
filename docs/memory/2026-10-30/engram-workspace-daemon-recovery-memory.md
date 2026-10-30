---
type: memory
title: Engram workspace daemon recovery
date: 2026-10-30
agent: claude-haiku-5.5 (subagent, operator-routed)
scope: runtime recovery only
---

## Outcome

Recovered. The workspace-owned Engram daemon for `C:\Source\GitHub\kbdb` was
stopped by exact PID and replaced by a new daemon. The CLI reconnected,
`workspace-status` reports the correct binding, a real indexed search returned
content, and the replacement PID stayed alive and responsive after 60 seconds.

The prior circuit (`circuit-break-engram-workspace-status.md`, 3 failures on
the old daemon) is preserved unchanged. This is a changed runtime condition,
not a reset of that counter.

## Ownership Evidence (old daemon)

* PID `22892`, `C:\Tools\engram.exe daemon --workspace C:\Source\GitHub\kbdb`
* Creation time `10/29/2026 12:55:24 PM` local, matching the `.engram\run\engram.pid`
  record `{"pid":22892,"start_time_unix":1793303724}`
* Parent `25876` was no longer running
* Not killed: shim `23084` (another Copilot client), daemons for `backlogit`,
  `engram`, `GSD`, and `intercom`, and all other shims

## ProposedAction and ActionResult

* ProposedAction: stop exact workspace daemon PID `22892` with
  `Stop-Process -Id 22892`, then reconnect through CLI auto-start
* scope: exact daemon only, identity re-verified immediately before stop
  (executable, `daemon --workspace` argument, creation time)
* ActionRisk: destructive/high (conservative); operator-approved in the request
* rollback: supported auto-restart via the CLI shim/daemon startup path
* ActionResult: approved, then applied. Stop returned without error, and
  PID `22892` exited within 3 seconds

## Replacement Daemon

* PID `48288`, `C:\Tools\engram.exe daemon --workspace C:\Source\GitHub\kbdb`
* Creation time `10/29/2026 8:35:31 PM` local
* Parent `41484`
* Pid record now reads `{"pid":48288,"start_time_unix":1793331331}`

## Verification Commands

Each command ran once, with native exit codes preserved.

| Step | Command | Result |
|---|---|---|
| Identify PID | `Get-CimInstance Win32_Process` filter on `engram.exe` | `22892` matched the workspace |
| Parent check | `Get-Process -Id 25876` | not running |
| CLI help | `C:\Tools\engram.exe --help`, `search --help` | read-only, no daemon contact |
| Scoped stop | identity re-check, then `Stop-Process -Id 22892` | exited |
| Bind and status | `engram --workspace C:\Source\GitHub\kbdb --format json workspace-status` | exit 0, `path` = `C:\Source\GitHub\kbdb`, branch `main`, code graph 138 files, 1092 functions, 149 classes, 4999 edges, `stale_files` false |
| Real lookup | `engram --workspace C:\Source\GitHub\kbdb --format json search --region code --limit 5 "workspace daemon readiness"` | exit 0, 5 code results with file paths, line ranges, and summaries |
| Stability | `Start-Sleep 60`, `Get-Process -Id 48288`, then `workspace-status` again | `48288` alive, status exit 0 |

## Remaining Concerns

* `workspace-status` reports `connection_count: 0` and `scan_status.running: true`
  with `files_scanned: 0` and `files_total: 0`. Searches still returned indexed
  content, and `stale_files` is false, so this is noted, not treated as a blocker.
* Root cause of the original readiness timeout on the old daemon is still not
  confirmed. The old `shim-startup-failures.jsonl` history was not modified.
* Shim PID `23084` still belongs to another client. It was left running and may
  hold a stale connection. Its owner should confirm it reconnects.

## Failure Counts

* Old daemon, same operation (`engram workspace-status`): 3 counted failures,
  unchanged and preserved in `circuit-break-engram-workspace-status.md`
* Replacement daemon: 0 failures across 2 `workspace-status` calls and 1
  `search` call

## Not Performed

No source or harness changes, no backlog claims, no shipments, no branches,
commits, pushes, or PR actions, and no edits to `.engram/` artifacts. No
indexes or locks were deleted. The parent assessment memory and the old task
memory (`engram-subagent-access-repair-memory.md`) were not changed.

## Parent Process Verification

The parent independently confirmed recovery after the Haiku subagent returned:

* `engram --workspace C:\Source\GitHub\kbdb workspace-status` exited 0,
  reported the correct workspace and branch, and reported `stale_files: false`
* `engram --workspace C:\Source\GitHub\kbdb --format json search --region code
  --limit 3 "open_serve_databases"` exited 0 with three code results, including
  the exact `open_serve_databases` function in `src\main.rs` at lines 2381-2479
* A final process inspection confirmed PID `48288` still executes
  `C:\Tools\engram.exe daemon --workspace C:\Source\GitHub\kbdb`, with the same
  creation time recorded above

CLI server access is verified in both the requested subagent and the parent.
The existing Copilot shim's own MCP connection was not restarted or verified;
CLI success does not claim that every pre-existing client session reconnected.
