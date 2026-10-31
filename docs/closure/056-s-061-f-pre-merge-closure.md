---
title: Shipment 056-S feature 061-F pre-merge closure
date: 2026-10-31
mode: pre-merge
shipment: 056-S
feature: 061-F
owner: operator/Ship
readiness: READY_WITH_CONDITIONS
compaction_status: pending
---

## Scope and evidence boundary

Seven task implementations are committed through `bd0ce89`. This is a
conditional pre-merge handoff, not a merge-readiness verdict or release approval.
Earlier blocked assertions in Ship memory are historical; the current operator
handoff supplies the latest quality results.

Read-only Git evidence compares base
`9cbc2b0919fe360e09e292f7399e3986e4a5fed1` with `bd0ce89`.
The implementation changes 12 paths: harness configuration and metadata,
agent/instruction Markdown, developer documentation, `.gitignore`, and removal
of `scripts/git_commands.py` and `scripts/run_git_commands.sh`.
The full diff also contains backlog execution and Ship continuity records.
It contains zero `.rs` files and zero Cargo manifests or lockfiles.

The deleted helpers only printed diagnostic Git commands against another
checkout. Task 007's recorded harness confirms no workflow, script, or Cargo
references to them. No application CLI, MCP server, database, embedding,
acquisition, or synchronization implementation changes.

## Invariants to preserve

* Keep Rust 1.88 declarations and agent routing consistent with configuration
* Keep manifest checksums aligned with the managed artifacts
* Preserve intended Engram metadata visibility without tracking runtime state
* Preserve all unrelated Git stashes and existing P-021 captures
* Keep default OS `TEMP` and `TMP`; do not relocate live `.kbdb`
* Preserve application workspace containment, schema, and MCP contracts
* Use feature-branch PRs and merge commits; never write directly to main

## Validator evidence

| Evidence | Status | Basis or missing prerequisite |
|---|---|---|
| Seven task red/green harnesses | Satisfied | Recorded in Ship execution memory |
| Installed harness verification | Satisfied | Recorded exit 0; blockers and warnings empty |
| Rust check | Satisfied | Parent handoff reports passed |
| Rust format check | Satisfied | Parent handoff reports passed |
| Strict all-targets clippy | Satisfied | Parent handoff reports passed |
| `cargo test --all-targets` | Satisfied | Parent handoff reports passed with default OS temporary environment |
| Full local build | Satisfied | `cargo build --all-targets` exited 0 in this session |
| CI-policy allowlist audit | Satisfied | Exact CI eleven-ignore `cargo audit --deny warnings` exited 0 |
| Local adversarial review | Satisfied for prior HEAD | Patch-backed three-reviewer review of `d8c0c0b` found P0=0, P1=0; this documentary correction requires final-HEAD review |
| Required merge CI | Pending | No current successful checks supplied |
| Application runtime verification | Not applicable | No application runtime surface changed in the inspected diff |
| Manual application checkpoints | Not applicable | No affected application surface for this release unit |

No runtime-verification report is fabricated. The workspace profile's
`cli-status`, `cli-sync`, `mcp-stdio-startup`, handshake expectations, and
`mcp-client-smoke` checkpoint describe application runtime coverage. This work
changes only the profile's MSRV declaration, not those probes or the runtime.
Their non-applicability here is scope-based, not a waiver for future runtime
changes. Runtime verdict: not applicable.

## Pre-deploy audits

* Scope audit passed: no Rust, Cargo, database migration, or deployment changes
* Feature flags, service coordination, and data migration checks: not applicable
* Harness schema and checksum verification: recorded pass; repeat after merge
* Full build and current allowlist audit passed in the parent session.
* Patch-backed review completed; recheck the final corrected HEAD before PR.
* Current-HEAD readiness record and required CI: mandatory before merge
* P-009 merge-commit strategy and P-016 topology: recheck before each merge
* Copilot gate: mandatory when engaged or required; do not infer a pass
* `.engram/.workspace-id` was observed untracked; leave tool-managed state alone

## Deployment and authorization

Release path: delivery PR, merge commit, post-merge harness verification,
then Ship closure reconciliation and any required closure PR.

The current operator request records dark-mode scope `056-S` / `061-F` only.
Delivery and closure merges are pre-authorized within this scope, using merge
commits. Admin fallback is pre-authorized only for a classified
`REVIEW_REQUIRED_BLOCK`, after the normal merge path rejects the merge.
It cannot bypass failed or pending checks, incomplete Copilot review,
unresolved Copilot threads, stale local readiness, scope mismatch, or topology
and merge-strategy gates. No merge or PR operation occurred in this executor.

## Risky action record

| ProposedAction | ActionRisk | Approval and containment | ActionResult |
|---|---|---|---|
| Apply and drop the task 005 route stash | Destructive | Explicit approval recorded in Ship memory; exactly the identified stash | Applied |
| Delete the two unused diagnostic helpers | Destructive | Explicit approval recorded in Ship memory; task 007 paths only | Applied |
| Merge scoped delivery and closure PRs | Moderate | Current operator pre-authorization; all policy gates remain mandatory | Planned |
| Admin merge after normal rejection | High | Only `REVIEW_REQUIRED_BLOCK`; never checks or Copilot bypass | Planned |
| Revert a regression through a PR | High | Separate explicit rollback approval; merge commit; no direct-main action | Planned |

The earlier proposal to relocate `.kbdb` was not executed and is not part of
this rollout. Default OS temporary paths resolved the artificial test failure.

## Monitoring plan and validation window

Owner: operator/Ship. The validation window starts with delivery merge CI and
continues through the first post-merge configuration verification. It closes
only after Ship records those outcomes; no fixed elapsed duration or success
is asserted in advance.

| Signal and observation source | Baseline or healthy signal | Intervention threshold |
|---|---|---|
| Required GitHub PR checks | Successful or explicitly justified non-applicable checks | Any required failure, missing check, or unexpected skip |
| `autoharness verify-workspace --workspace . --json` | Recorded pre-merge baseline: zero blockers and warnings | Any strict schema blocker, blocker, or new warning |
| Config route verification | Orchestrator resolves Gemini/Google/high/long_context | Any mismatch with the approved route or agent metadata |
| Manifest and ignore harnesses | Checksums agree; intended metadata visible; runtime state ignored | Any checksum mismatch or unintended runtime artifact exposure |
| Local review readiness and Copilot gate | Current-HEAD review coverage and applicable gate pass | Stale coverage, unresolved blocking findings, or Copilot block |

These are manual command and GitHub observations, not a claimed deployed
dashboard or automated alert service. Ship records the evidence and the
operator responds when a threshold is crossed.

## Post-deploy checks

* Confirm the delivery merge used a merge commit and required CI is green
* Run installed harness verification in the merged checkout
* Confirm the configured orchestrator route and managed checksums still agree
* Confirm the Engram ignore harness and debug-helper absence checks pass
* Preserve unrelated stashes, generated state, and both P-021 follow-ups
* Complete shipment reconciliation and mandatory P-020 compaction
* Record the validation-window outcome as healthy, degraded, or rolled back

## Rollback trigger and procedure

Halt release progression on any required CI failure, any post-merge schema
blocker, any route/checksum mismatch, or unintended Engram runtime-state
exposure. A current-HEAD review or Copilot block halts merging rather than
authorizing a bypass.

Ship gathers the failing evidence and obtains explicit approval for rollback.
Prepare a bounded revert on a dedicated branch and submit a PR restoring the
affected delivery changes. Run the applicable harnesses, quality gates, review,
and CI before an approved merge commit. Never revert directly on main, rewrite
history, or delete generated runtime data. Re-run configuration verification
after rollback and record its outcome.

## Source artifact cleanup

Read-only `backlogit get 061-F` inspected all four provenance fields:
`source_stash_id`, `source_stash_ids`, `source_deliberation_id`, and
`source_deliberation_ids`. Only plural `source_stash_ids` is present.
The deduplicated retirement handoff is:

| Source stash ID | Observed current status | Stage action |
|---|---|---|
| `358A5E68` | Absent from active listing; direct get returned not found | Verify lifecycle; archive if still active, never remove |
| `0E67835A` | Absent from active listing; terminal state unverified | Verify lifecycle; archive if still active, never remove |
| `3FFE51B4` | Absent from active listing; terminal state unverified | Verify lifecycle; archive if still active, never remove |
| `1074A164` | Absent from active listing; terminal state unverified | Verify lifecycle; archive if still active, never remove |
| `C365AB98` | Absent from active listing; terminal state unverified | Verify lifecycle; archive if still active, never remove |
| `AF676684` | Absent from active listing; terminal state unverified | Verify lifecycle; archive if still active, never remove |
| `CCAC612D` | Absent from active listing; terminal state unverified | Verify lifecycle; archive if still active, never remove |

Source deliberation IDs: none in either provenance field. The feature references
`docs/decisions/2026-10-31-option-3-msrv-harness-repo-hygiene-deliberation.md`;
that durable document is not a backlog deliberation ID and is not marked for
removal. Ship performs no source archival, removal, or stash mutation.

## Follow-up handoff

Stage owns only the existing P-021 follow-ups `150A478A` (dependency audit
remediation) and `E4B2B0B3` (contained-scratch test isolation). Both remain
untouched. No new capture, triage, or follow-up item is created here.
The earlier bare-audit failure does not replace the required CI allowlist audit;
the contained-scratch failures do not override the default-environment pass.

## Releasability evidence

| Requirement | Disposition |
|---|---|
| Runtime profile healthy-signal evidence | Not applicable to this non-runtime diff; no probe pass claimed |
| Runtime profile external-client follow-up | Not applicable to this release unit; no client validation claimed |
| Monitoring, rollback, owner, validation window | Satisfied by the scoped procedures above |
| Source retirement handoff | Recorded; terminal source status requires Stage confirmation |
| Full build and current audit | Satisfied; current-session commands exited 0 |
| Local review and current-HEAD readiness | Prior-HEAD review passed; final corrected HEAD requires readiness verification |
| Required CI and applicable Copilot gate | Pending pre-merge verification |
| P-020 compaction status | Pending post-merge closure |

Readiness: `READY_WITH_CONDITIONS`. Build and audit passed. Merge must wait
for final-HEAD review/readiness, required CI, and applicable Copilot gate evidence.
Any failed mandatory gate changes the disposition to `BLOCKED`; this document
does not waive or pre-judge those results.
