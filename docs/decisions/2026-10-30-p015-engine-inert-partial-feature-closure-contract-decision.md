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

At `2026-10-30T18:25:35.061-07:00` (`2026-10-31T01:25:35Z`), following `_Ship`'s
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
* **All 33 descendants terminal and archived**: Every single one of the 33 tasks of `056-F` is now `status: archived` (`archived_status: done`) in `.backlogit/archive/` with `parent_id: 056-F` intact (`docs/decisions/2026-10-30-055-s-corrective-baseline-disposition.md`).
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
* **Step A2.3 (Ship Pass 2 `055-S` closure PR)**: With the amended contract live on `origin/main`, Ship executes `shipment-reconcile` (`safe-close` + `post`) on `055-S`, verifies post-close invariance (`0` diff on `056-F` and all 33 tasks), resolves `.backlogit/reconcile/055-S-halt-20261030-083000.md` and `checkpoint-20261030-215208.json`, and merges the `055-S` closure PR.
* **Step A2.4 (Stage post-closure retirement)**: After `055-S` is genuinely `archived_status: shipped` on `origin/main`, Stage retires covering feature `056-F` to `done` (archived) and archives consumed source stash entry `7BF1961D`.

## Inline Review Note (Declared Fallback, P-012)

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* **Capability declaration**: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass` (per `.github/skills/plan-review/SKILL.md` Step 2; evaluated inline by Stage `gemini-4-argon` and not counted as independent multi-agent review).
* **Findings**: `0 P0, 0 P1, 0 P2, 0 P3`. Role separation (P-010), pre-close/post-close protected-set invariance (P-015 `INV-6`/`INV-7`/`INV-10`), dark-factory governance provenance (P-017), and two-pass merge ordering before `055-S` resumption are preserved.
