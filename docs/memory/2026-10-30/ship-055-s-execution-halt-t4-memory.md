---
title: "Ship 055-S execution checkpoint: docs delivered, T4 halted"
agent: ship
shipment: 055-S
date: 2026-10-30
status: halted-awaiting-operator-decision
---

## Scope and authority

* Shipment `055-S` (members `056.012-T`, `056.013-T`, `056.004-T`), covering
  feature `056-F` excluded and protected (P-015).
* Dark factory active; routine merge preauthorized
  (`merge_approval_pre_authorized=true`, `admin_fallback_pre_authorized=false`,
  no cascade or destructive exceptions). PR 140 merged at 2026-10-30T06:37:50Z.
* Engram unavailable (two prior `workspace-status` timeouts); backlogit CLI and
  git used as the fallback. No MCP backlog tools.

## Done

* Branch `feat/phase-3-final-documentation-and-restored-production-acceptance`
  (first name `feat/phase3-...` failed the topology branch-ownership check and
  was renamed before any commit). Pre-claim, claim, and post-claim gates pass;
  shipment `055-S` is `active`.
* `056.012-T` docs: `docs/troubleshooting.md` (serve preflight diagnostics and
  client startup) and `docs/mcp-tools.md` (availability notes under
  `search_semantic`, `research_topic`, `get_status`, new
  `Runtime diagnostics and recovery` subsection).
* `056.013-T` docs: managed launch entry and `server/discover` compatibility under
  `### 2. Configure your MCP client`; `serve`, `install`, `upgrade`,
  `uninstall` sections of `docs/cli-reference/graphtor-docs.md`.
* README Quick Start `.mcp.json` example already matches the CLI-honored
  shape used by the docs (`type: stdio`, key `kbdb`); no discriminator change
  selected, so recorded `not-needed` and left unchanged.
* Markdown lint passes on staged files. Docs only, so full Rust build is N/A.
* Actual identity: binary `kbdb` 0.3.1 (`C:\Tools\kbdb.exe`), generated entry key
  `kbdb`, Copilot CLI 1.0.105 (`C:\Tools\copilot.exe`).

## Halted: `056.004-T` (T4) genuine blockers

1. The live production entry is not the delivered entry. `copilot mcp get kbdb
   --json` resolves `.mcp.json` to `bun .copilot/graphtor-mcp-shim.cjs kbdb
   serve`, an untracked, gitignored stdio shim that rewrites protocol traffic.
   T4 forbids wrapper and temporary configs. Restoring the delivered entry
   (`kbdb serve`, generator shape) means editing the operator's `.mcp.json`;
   that authority was not granted.
2. `/mcp show kbdb` is not scriptable. `copilot -p '/mcp show kbdb'` sends the
   text to the model (about 20 AI credits) and returns a model answer, not the
   CLI status screen. Only an interactive session shows the connected status
   the criteria require. The Copilot process log does record
   `Service initialized as client`, but substituting it for `/mcp show` would
   weaken the stated acceptance and needs an explicit decision.

The diagnostic run above used the wrapper entry and counts as nothing for T4.
No T4 runner script was written: its capture contract depends on blocker 2.

## Operator decisions needed

* Authorize restoring the delivered `kbdb` entry in `.mcp.json` (and how to
  preserve the shim for rollback), or name another production workspace.
* Decide how three sessions are captured: interactive operator-run `/mcp show`
  sessions with the runner recording evidence, or an explicit amendment
  accepting the Copilot process log as the CLI-visible source.

## Resume

* Tasks `056.012-T` and `056.013-T` stay `active` until local review, PR, and
  merge. `056.004-T` stays `active`. No task is marked done, no PR is open.
* Run `056.002-T` (`tests/serve_handshake_driver_test.rs`) sequentially, never
  alongside a Copilot session.
* Closure must use `shipment-reconcile` safe-close holding
  `.backlogit/queue/.055-S.md.lock`; no cascade authority is granted.

## Follow-up: capture-feasibility investigation (read-only, no model prompts)

* `copilot --help` and `copilot help commands`: `/mcp` is an interactive slash
  command. Non-interactive surfaces are `-p`/piped stdin (both model prompts)
  and `copilot mcp list|get` (static config, no live connection). `--acp` is a
  different protocol surface, not the `/mcp show` screen. No advertised flag
  prints `/mcp show` output.
* Bounded check with empty piped stdin and `--screen-reader --no-color`: exit 1,
  "No prompt provided. Run in an interactive terminal or provide a prompt with
  -p or via standard in." Without a TTY the CLI refuses interactive mode.
* A valid capture therefore needs a real terminal (PTY or ConPTY) hosting the
  exact `C:\Tools\copilot.exe`, plus VT screen parsing. The repository has no
  such primitive (`tools/mcp-probe` has none, `exact_cli.rs` only records
  `/mcp show kbdb` as a manual invocation string) and no PTY library is
  installed (pywinpty, pexpect, node-pty absent). Adding one is a new
  dependency or native interop, which was not authorized. Result: capture
  method is NOT FEASIBLE with existing primitives; no harness written.
* The shim `.copilot/graphtor-mcp-shim.cjs` spawns `kbdb serve` as a child and
  proxies stdio, tracking `initialize` ids and injecting an `initialized`
  message. That is a server-side stdio wrapper, so it is the forbidden kind.
* Identity retained (SHA-256 prefixes): `.mcp.json` 533B43AA35E3119A, shim
  4F47AA2548D9F9C7, `kbdb.exe` 7C243C9318E303CF, `copilot.exe`
  AB6D710D551C137C, kbdb entry JSON 5C707B1C72B35AC2.
* Two separate blockers remain: (A) config: live entry is the wrapper, restore
  needs authority; (B) capture: no PTY primitive, so the three `/mcp show`
  sessions need either an operator-run interactive session with the runner
  recording evidence, or authority to add a PTY dependency/native interop.
