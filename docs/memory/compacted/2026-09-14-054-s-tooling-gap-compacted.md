---
type: compacted-memory
date: 2026-09-14
compacted_on: 2026-10-29
scope: 054-S shipment-close tooling gap (continuation, Stage disposition, publication PRs 128-131)
sources:
  - docs/archive/memory/2026-09-14/ship-054s-continuation-tooling-gap-capture-memory.md
  - docs/archive/memory/2026-09-14/stage-054s-tooling-gap-reconcile-disposition-memory.md
  - docs/archive/memory/2026-09-14/ship-3075d00-publication-memory.md
  - docs/archive/memory/2026-09-14/stage-060f-upstream-issue-memory.md
  - docs/archive/memory/2026-09-14/ship-d802716-publication-memory.md
status: resolved
---

# Compacted Memory: 054-S Shipment-Close Tooling Gap

## Problem

The installed backlogit CLI refuses `move`/`update --status shipped` on a
shipment record (`shipment_shipped_requires_envelope`). Only the cascade
`backlogit shipment ship` performs the transition, and it is P-015-forbidden
for the task-only, partial-feature manifest of `054-S` (`[056.028-T]`,
covering feature `056-F` excluded). Shipment `054-S` therefore stayed
`active` and blocked `053-S` and `052-S` on the dependency DAG.

## Decisions and Outcomes

* Ship re-verified the refusal non-destructively and captured the gap as
  P-021 C2 stash `7BBDE07A`; an earlier truncated duplicate was `1C9CD261`.
* Stage reconciled the duplicates (survivor `1C9CD261`, repaired in place
  and archived; `7BBDE07A` archived), created deliberation `004-DL` and the
  blocked upstream-owned tracker `060-F`.
* Stage filed upstream issue `softwaresalt/backlogit#443` (non-cascading,
  manifest-scoped close for a live partial-feature shipment).
* Ship published the Stage commits through ordinary merge-commit PRs
  #128, #129, #130, #131. Each Copilot finding on those publication PRs
  failed the P-021 C1 test and was captured as a deferred entry.
* The operator later authorized the one-time cascade (`004-DL` Option B);
  the shipment record was closed in the `post-merge/054-s-close-shipment-record`
  closure PR.

## Deferred Entries Pending Stage Triage

`9A31F048`, `84CA0D08`, `1FF1BDC0`, `D9CB4ACF`, `2EFFA000`, `80083AF8`,
`55AC021B`, `8C8491A4` (all P-021 C2 captures, clerical or provenance
wording findings on Stage-authored content).

## Durable Lessons

* Commit P-021 captures to the PR branch before the PR merges, or they
  strand as uncommitted working-tree lines.
* In PowerShell, a backtick followed by `n t r f b a v 0` inside a
  double-quoted string is consumed as an escape. Use single-quoted
  here-strings (`@'...'@`) for CLI text arguments.
* Every push re-arms Copilot review; a fix commit can surface a new finding.
* `mergeStateStatus` can read `UNSTABLE` when a non-required check fails.
  `mergeable: MERGEABLE` only reports the absence of conflicts; it does not
  prove readiness. Merge readiness still requires the independent required
  checks, the current-HEAD local review gate, and the P-018 gate.
