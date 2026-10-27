---
policy_id: "P-DYN-001"
policy_type: "workspace-specific"
status: "proposed"
proposed_at: "2026-10-26T17:27:00Z"
evidence_count: 7
---

# Windows Reparse-Point, Encoding, and File-Handle Hygiene Gate

## Status: Proposed

This policy was auto-proposed by `auto-tune` based on recurring patterns in the compound
learning library. Review and decide: accept (copy to `.github/policies/` or append to
`workflow-policies.md`) or reject (delete this file with a note in the tuning report).

## Policy Definition

| Field | Value |
|---|---|
| **APPLIES_TO** | ship, build-feature, runtime-verification, rust-engineer |
| **GATE_POINT** | Before PR creation and during Windows test/script verification |
| **PRECONDITION** | Filesystem writes, subprocess invocations, and test fixtures touching Windows paths or handles are identified in the diff |
| **POSTCONDITION** | Reparse points/junctions fail closed before write/traversal, subprocess/file I/O uses explicit UTF-8 without BOM, and SQLite/process handles are closed before directory moves or temp cleanup |
| **VIOLATION_ACTION** | Halt the task or PR gate, log the Windows hygiene violation, and remediate before merge |

## Rationale

Cross-cutting Windows issues (reparse points, CRLF/UTF-8 BOM encoding, OS error 232 pipe closure, and stale file locks) recur across 7 compound learnings spanning best-practices, runtime-errors, and workflow-issues.

## Evidence

Derived from 7 compound learnings sharing the pattern `windows`.

Evidence references:

* `docs/compound/best-practices/git-binary-test-fixtures-gitattributes-2026-05-05.md`
* `docs/compound/best-practices/reparse-point-fail-closed-containment-2026-07-16.md`
* `docs/compound/python-subprocess-windows-gh-api-encoding-2026-05-05.md`
* `docs/compound/runtime-errors/mcp-serve-os-error-232-handshake-signature-2026-09-13.md`
* `docs/compound/runtime-errors/sync-reingest-canonical-source-root-2026-05-21.md`
* `docs/compound/workflow-issues/cargo-artifact-lock-stale-process-2026-04-30.md`
* `docs/compound/workflow-issues/session-shell-cleanup-closure-2026-04-30.md`

## Acceptance Path

To accept this policy:

1. Review the evidence references and validate the pattern is real and recurring.
2. Copy this file to `.github/policies/` or append a new entry to `.github/policies/workflow-policies.md`.
3. Update any agents or skills that should enforce this policy gate.
4. Run `autoharness verify-workspace` to confirm no dangling cross-references remain.
5. Record acceptance in the tuning report.

To reject: delete this file and note the rejection in the tuning report with a reason.
