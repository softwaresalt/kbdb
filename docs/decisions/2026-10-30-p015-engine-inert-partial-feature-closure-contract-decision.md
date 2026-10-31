---
title: "Stage decision: Choice A2 P-015 engine-inert terminal partial-feature closure contract amendment"
description: "Stage decision recording operator Choice A2 authorization to amend P-015, _ship.agent.md, and shipment-reconcile for engine-inert terminal partial-feature shipment closure, Step 2/3 Stage-dispositioned sibling exclusion, and H6 schema-path resolution"
doc_type: "decision"
topic: "Governing-contract amendment decision under .backlogit/reconcile/055-S-halt-20261030-083000.md Option 3 for final phased partial-feature shipment 055-S closure"
depth: "lightweight"
decision_status: "decided"
session_date: "2026-10-30"
agent: "stage"
backlog_refs:
  - "055-S"
  - "056-F"
  - "056.004-T"
  - "056.012-T"
  - "056.013-T"
  - "E5C4DFFC"
linked_artifacts:
  - ".backlogit/reconcile/055-S-halt-20261030-083000.md"
  - "docs/decisions/2026-10-30-055-s-corrective-baseline-disposition.md"
  - "docs/memory/2026-10-30-ship-055-s-closure-authority-blocked.md"
  - "docs/closure/2026-10-30-055-s-phase-3-final-docs-t4-post-merge-closure.md"
  - "docs/decisions/2026-10-29-056-f-phase-3-branch-disposition-and-mode-r-ratification.md"
  - "docs/decisions/2026-09-13-stage-056.026-T-disposition-not-needed.md"
tags:
  - "stage"
  - "055-s"
  - "056-f"
  - "shipment-reconcile"
  - "safe-close"
  - "p-010"
  - "p-015"
  - "p-017"
  - "choice-a2"
---

## Context and Operator Authorization

At `2026-10-31T01:25:35Z`, following `_Ship`'s
fail-closed P-010/P-015 halt on Choice A1
(`docs/memory/2026-10-30-ship-055-s-closure-authority-blocked.md`), the operator
authorized **`"Confirm Choice A2 in dark factory mode"`**
(`merge_approval_pre_authorized = true`, `admin_fallback_pre_authorized = true`,
and inclusion of `M .autoharness/config.yaml`), selecting Option 3 of
`.backlogit/reconcile/055-S-halt-20261030-083000.md` (*"3. Separately change the
governing contract (P-015 or the safe-close skill) and record that decision
before any resumption"*).

This Stage decision artifact satisfies the Option 3 decision-recording
prerequisite within Stage's `Planning` and `Git` role boundaries before Ship
implements and merges the governing-contract amendment in Pass 1
(`post-merge/055-s-closure-contract-amendment`) and resumes `055-S` closure in
Pass 2.

## Root Cause and Multi-Shipment Final Closure Gap

* **Phased multi-shipment delivery of `056-F`**: Feature `056-F` (33 tasks `056.001-T`..`056.033-T`) was delivered across five phased task-only shipments (`049-S`, `054-S`, `053-S`, `052-S`, and final Phase 3 shipment `055-S` `[056.012-T, 056.013-T, 056.004-T]`), plus 15 Stage-ratified `done`/`selection:not-needed` tasks (`docs/decisions/2026-09-13-stage-056.026-T-disposition-not-needed.md` and `docs/decisions/2026-10-29-056-f-phase-3-branch-disposition-and-mode-r-ratification.md`).
* **All 33 descendants terminal and archived**: Prior to the Post-PR #145 Addendum below, 18 delivered tasks of `056-F` were already `status: archived` (`archived_status: done`) in `.backlogit/archive/`, while the 15 Stage-ratified `selection:not-needed` tasks had been moved to `.backlogit/archive/056.0XX-T.md` via `backlogit move <id> --status done` (in PR #122 and PR #140) with frontmatter still declaring `status: done`. Following Stage's Step A2.2b deliberation of `E5C4DFFC` and execution of `backlogit archive <id>` on those 15 `selection:not-needed` siblings (see the Post-PR #145 Addendum below), every single one of the 33 tasks of `056-F` genuinely declares `status: archived` (`archived_status: done`) in `.backlogit/archive/` with `parent_id: 056-F` intact (`docs/decisions/2026-10-30-055-s-corrective-baseline-disposition.md`).
* **Engine refusal of direct status move and cross-shipment membership**: Installed `backlogit 1.12.0` rejects `backlogit move 055-S --status shipped` (`exit 9: shipment must be shipped via ShipShipment`), and `backlogit shipment add` refuses items already assigned to prior shipments (`049-S`/`054-S`/`053-S`/`052-S`), so `055-S` cannot list all 33 tasks in its own manifest to satisfy the existing single-manifest Verified Fully-Covered-Root Exception.
* **Verified engine-inert `ShipShipment` behavior on `1.11` / `1.12`**: In `backlogit 1.11` and `1.12` (the verified engine minor lines in `autoharness.gates.shipment_closure.VERIFIED_CASCADE_ENGINE_MINOR_LINES`), `ShipShipment` (`backlogit shipment ship`) selects archive candidates from the flat manifest (`custom_fields.items`) and leaves the non-member covering feature (`056-F`) and already-`status: archived` (engine-inert) out-of-manifest descendants untouched (`archived_ids: ["055-S"]`, `returned_ids: []`).

## Ratified Governing-Contract Amendments

The following three governing-contract amendments are ratified for implementation
and merge by `_Ship` in Pass 1 PR `post-merge/055-s-closure-contract-amendment`
**before** resuming `055-S` closure in Pass 2:

### 1. P-015 Engine-Inert Terminal Partial-Feature Exception

Target surfaces: `.github/policies/workflow-policies.md` (P-010 and P-015),
`.github/agents/_ship.agent.md` (Mutation Classification row
`backlogit_ship_shipment` and Step 6.1.b), and
`.github/skills/shipment-reconcile/SKILL.md` (Safe-Close Mode Step 0 and Step 8).

In addition to the Verified Fully-Covered-Root Exception,
`backlogit_ship_shipment` (`backlogit shipment ship <shipment_id> --sha <merge_commit_sha>`)
is an **Allowed, classified `_Ship` operation** when closing a partial-feature
shipment whose non-cascading `backlogit move <shipment_id> --status shipped` is
refused by the installed engine (`exit 9`), provided ALL of the following
machine-checkable preconditions hold before invocation:

* **(i) All manifest items pre-archived with verified commit provenance**: Every item in the shipment's `custom_fields.items` is already `status: archived` (`archived_status: done` or `accepted`) in `.backlogit/archive/` carrying the verified delivered-work `commit` SHA on `origin/main`.
* **(ii) Engine-inertness of all out-of-manifest descendants (`INV-6`)**: Every out-of-manifest descendant of the covering feature (at every depth, enumerated across `.backlogit/queue/` and `.backlogit/archive/`) has parsed frontmatter `status: "archived"` in `.backlogit/archive/` (no non-archived descendant remains in `.backlogit/queue/`), and no descendant ID is torn/duplicated across `queue/` and `archive/`.
* **(iii) Verified engine minor line and canonical lock**: The probed `backlogit` CLI is on a verified release minor line (`1.11` or `1.12`), the canonical logical shipment lock `.backlogit/queue/.{shipment_id}.md.lock` is held across the invocation, and a pre-close SHA-256 baseline snapshot of the covering feature (`.backlogit/queue/{feature_id}.md`) and all descendants is captured before invocation.
* **(iv) Post-close invariance gate (`INV-7` / `INV-10`)**: Immediately after `backlogit shipment ship <shipment_id> --sha <merge_commit_sha>`, `returned_ids` MUST be `[]`, `archived_ids` MUST be `["<shipment_id>"]`, `.backlogit/archive/<shipment_id>.md` MUST record `status: archived`, `archived_status: shipped`, and `commit: <merge_commit_sha>`, and the covering feature plus every descendant MUST be byte-identical to the pre-close SHA-256 baseline snapshot (`0` diff).

### 2. Safe-Close Step 2/3 Exclusion Alignment

Target surface: `.github/skills/shipment-reconcile/SKILL.md` (Safe-Close Mode
Step 2 and Step 3).

Extend Step 2's sequence-aware exclusion so out-of-manifest sibling tasks that
are already `status: archived` (`archived_status: done`) in
`.backlogit/archive/` through verified Stage-ratified `done` +
`selection:not-needed` provenance (cited to a merged Stage decision artifact on
`origin/main`) are excluded from the live-queue presence requirement in Step 3
and instead guarded by pre/post byte-identity (baseline invariance, `INV-7`).

### 3. H6 Session-Start Dynamic Reload Schema Path Clarification

Target surfaces: `.github/agents/_ship.agent.md`,
`.github/agents/_stage.agent.md`, and `.autoharness/harness-manifest.yaml`.

Align the Session-Start Dynamic Reload (H6) prose in `_ship.agent.md` and
`_stage.agent.md` with `_orchestrator.agent.md` (lines 472-482) so both agents
explicitly resolve `{autoharness_home}/schemas/harness-config.schema.json` via
`autoharness home` and `autoharness verify-workspace --workspace {workspace_path} --autoharness-home {autoharness_home} --json`,
plus align `_ship.agent.md` frontmatter and `.autoharness/harness-manifest.yaml`
with the operator's `.autoharness/config.yaml` `ship` route (`gpt-6.1-sol` /
`openai` / `medium`).

## Two-Pass Execution Sequence and Role Boundaries

* **Step A2.1 (this Stage commit on local `main`)**: Record the Stage decision artifact and Stage session memory without mutating `.github/`, `.autoharness/config.yaml`, `.backlogit/queue/055-S.md`, `.backlogit/queue/056-F.md`, `.backlogit/reconcile/055-S-halt-20261030-083000.md`, or Ship's active checkpoint `checkpoint-20261030-215208.json`.
* **Step A2.2 (Ship Pass 1 PR `post-merge/055-s-closure-contract-amendment`)**: Ship branches from local `main` (carrying this Stage commit, `M .autoharness/config.yaml`, and `docs/memory/2026-10-30-ship-055-s-closure-authority-blocked.md`), applies the three ratified harness/policy/skill amendments above, and merges Pass 1 to `origin/main` before any `055-S` closure mutation runs.
* **Step A2.2b (Stage Post-PR #145 Resolution of `E5C4DFFC`)**: Following Pass 1 PR #145 (`bb1a2bcef4515d0039cd9e66d2bcd2e57ede1d6c`), Stage deliberates P-021 C2 stash `E5C4DFFC` (thread `PRRT_kwDORiB5E86yMf7b`), executes `backlogit archive <id>` on the 15 Stage-owned `selection:not-needed` sibling tasks of `056-F` so all 33 descendants declare `status: archived` (`archived_status: done`), archives consumed stash `E5C4DFFC`, and records this addendum on local `main`.
* **Step A2.3 (Ship Pass 2 `055-S` closure PR)**: With the amended contract live on `origin/main` and all 33 `056-F` descendants verified `status: archived` (`archived_status: done`), Ship executes `shipment-reconcile` (`safe-close` + `post`) on `055-S`, verifies post-close invariance (`0` diff on `056-F` and all 33 tasks), resolves `.backlogit/reconcile/055-S-halt-20261030-083000.md` and `checkpoint-20261030-215208.json`, and merges the `055-S` closure PR.
* **Step A2.4 (Stage post-closure retirement)**: After `055-S` is genuinely `archived_status: shipped` on `origin/main`, Stage retires covering feature `056-F` to `done` (archived) and archives consumed source stash entry `7BF1961D`.

## Post-PR #145 Addendum: Stage Deliberation and Resolution of E5C4DFFC (15 selection:not-needed Siblings Finalized to status: archived)

During Pass 1 PR #145 (merged to `origin/main` at `bb1a2bcef4515d0039cd9e66d2bcd2e57ede1d6c`), Copilot review thread `PRRT_kwDORiB5E86yMf7b` (`review_id: 5720500934`) identified that the 15 Stage-ratified `selection:not-needed` sibling tasks of `056-F` (`056.005-T`, `056.006-T`, `056.007-T`, `056.008-T`, `056.009-T`, `056.010-T`, `056.014-T`, `056.015-T`, `056.016-T`, `056.017-T`, `056.018-T`, `056.024-T`, `056.025-T`, `056.026-T`, `056.027-T`) had been moved into `.backlogit/archive/056.0XX-T.md` when Stage ran `backlogit move <id> --status done` (in PR #122 and PR #140), but Stage had not subsequently run `backlogit archive <id>` on them. Consequently, their YAML frontmatter still declared `status: done` rather than `status: archived` (`archived_status: done`), which would block Pass 2 (`055-S` closure) at the `INV-6` precondition check (`SELECT id, status FROM items WHERE parent_id = '056-F' AND status != 'archived'`).

Because modifying Stage decision artifacts and finalizing Stage-owned out-of-manifest backlog items is outside Ship's P-010 role boundary and outside the Pass 1 governing-contract amendment scope (P-021 C1), Ship captured this Stage-only prerequisite as P-021 C2 deferred-scope-expansion stash entry **`E5C4DFFC`** before merging PR #145 and held Pass 2 until Stage deliberated and resolved `E5C4DFFC`.

### P-021 C5/C6 Intake and Triage Obligations

* **Precedence classification (P-021 C6)**: Entry `E5C4DFFC` begins with the literal `DEFERRED SCOPE EXPANSION` token, forcing the Step 2 `deliberate` route before any backlog or decision mutation.
* **Source references carried forward**: `stash_id=E5C4DFFC`, `pr_number=145` (`bb1a2bcef4515d0039cd9e66d2bcd2e57ede1d6c`), `review_thread_id=PRRT_kwDORiB5E86yMf7b`, `review_id=5720500934`, `task_id=056.004-T` (closure context), `feature_id=056-F`, `shipment_id=055-S`, `decision=docs/decisions/2026-10-30-p015-engine-inert-partial-feature-closure-contract-decision.md`.
* **(A) Unconditional duplicate detection**: Executed `SELECT stash_id, priority, kind, state, text FROM stash_entries WHERE stash_id = 'E5C4DFFC' OR text LIKE '%PRRT_kwDORiB5E86yMf7b%' OR text LIKE '%selection:not-needed%'` across all stash states. Outcome: **CLEAN DUPLICATE SCAN** — `E5C4DFFC` is the sole entry describing this expansion (`0E67835A` is an unrelated frontmatter-conformity follow-up).
* **(B) Late-identifier reconciliation**: All source-ref fields (`pr_number`, `review_thread_id`, `review_id`, `task_id`, `feature_id`, `shipment_id`) were concretely populated at capture time with zero `N/A` fields; reconciliation completed as a no-op with all concrete identifiers preserved.

### Deliberation Options and Selected Direction (P-021 C6)

* **Option 1 (Selected — Execute Stage-owned `backlogit archive <id>` on all 15 `selection:not-needed` tasks)**: Under `.github/agents/_stage.agent.md` line 66 (`Mutation Classification` table), `backlogit_archive_item` (`backlogit archive <id>`) is explicitly classified as **Allowed** for Stage to *"archive a Stage-owned backlog work item that was superseded or withdrawn before shipment. Never a shipment manifest (closure and archival of shipments are Ship's, P-010) and never an item Ship's current shipment owns."* All 15 tasks (`056.005-T`..`056.010-T`, `056.014-T`..`056.018-T`, `056.024-T`..`056.027-T`) are Stage-owned work items previously dispositioned `selection:not-needed` (superseded/withdrawn before shipment in PR #122 and PR #140) and none are in `055-S`'s manifest (`["056.012-T", "056.013-T", "056.004-T"]`). Running `backlogit archive <id>` on each transitions its frontmatter in `.backlogit/archive/056.0XX-T.md` from `status: done` to `status: archived` (`archived_status: done`, `archived_from: .backlogit/queue/056.0XX-T.md`) with `parent_id: 056-F` intact, satisfying `INV-6` so Pass 2 (`055-S` closure) can proceed cleanly.
* **Option 2 (Rejected — Leave Pass 2 held indefinitely)**: Maintain the Pass 2 hold without archiving the 15 `selection:not-needed` siblings. Rejected because leaving already-completed, archive-routed `selection:not-needed` tasks at `status: done` permanently blocks `055-S` closure and `056-F` retirement despite Stage holding explicit P-010 authority to complete their lifecycle archival.

### Resolution and Verification Evidence

1. **Lifecycle archival executed**: Stage ran `backlogit archive <id>` for all 15 `selection:not-needed` tasks (`056.005-T`, `056.006-T`, `056.007-T`, `056.008-T`, `056.009-T`, `056.010-T`, `056.014-T`, `056.015-T`, `056.016-T`, `056.017-T`, `056.018-T`, `056.024-T`, `056.025-T`, `056.026-T`, `056.027-T`), followed by `backlogit sync`.
2. **All 33 `056-F` descendants verified `status: archived`**:
   * `backlogit query "SELECT id, status FROM items WHERE parent_id = '056-F' AND status != 'archived'"` returned `[]` (empty array — 0 non-archived descendants remain).
   * `backlogit query "SELECT COUNT(*) AS archived_count FROM items WHERE parent_id = '056-F' AND status = 'archived'"` confirmed all 33 child tasks (`056.001-T`..`056.033-T`) declare `status: archived`.
   * Spot-checked `.backlogit/archive/056.005-T.md` and `.backlogit/archive/056.026-T.md`, confirming `status: archived`, `archived_status: done`, and `parent_id: 056-F` are present in YAML frontmatter.
3. **Consumed stash retired**: Archived `E5C4DFFC` via `backlogit stash archive E5C4DFFC` and synced the index (`0E67835A` left active in stash as unrelated scope).

## Inline Review Note (Declared Fallback, P-012)

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* **Capability declaration**: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass` (per `.github/skills/plan-review/SKILL.md` Step 2; evaluated inline by Stage `gemini-4-argon` and not counted as independent multi-agent review).
* **Findings**: `0 P0, 0 P1, 0 P2, 0 P3`. Role separation (P-010), pre-close/post-close protected-set invariance (P-015 `INV-6`/`INV-7`/`INV-10`), dark-factory governance provenance (P-017), and two-pass merge ordering before `055-S` resumption are preserved.
