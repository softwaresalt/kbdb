---
title: "Option 3 Deliberation: MSRV 1.88 Alignment, Harness Metadata Conformity, and Repository Hygiene (Batch 1)"
description: "P-021 C6 deliberation and disposition for Stream D and Stream E stash entries, abandonment of F1CE20EC, and retirement of 003-DL and 004-DL"
topic: "MSRV 1.88 declaration alignment, autoharness model-routing and frontmatter conformity, and repository hygiene (Option 3 / Batch 1)"
depth: "standard"
decision_status: "decided"
promoted_to: "plan"
linked_artifacts:
  - "docs/exec-plans/2026-10-31-msrv-harness-repo-hygiene-plan.md"
  - ".backlogit/queue/061-F.md"
  - ".backlogit/queue/056-S.md"
  - ".backlogit/queue/060-F.md"
  - ".backlogit/archive/003-DL.md"
  - ".backlogit/archive/004-DL.md"
tags:
  - "msrv-1-88"
  - "harness-hygiene"
  - "model-routing"
  - "p-021-c6"
  - "dark-factory"
---

## Problem Frame

Following the completion and archival of Feature `056-F` (`c70e59d8711b8f728398e11089240361fed38b93`) and its shipment chain (`049-S`, `054-S`, `053-S`, `052-S`, `055-S`), the backlog stash contains 36 active entries across five thematic streams, plus two completed deliberation items (`003-DL`, `004-DL`) in `.backlogit/queue/`. Under P-017 Dark Factory Mode (`DARK_MODE_ACTIVE = true`), the operator authorized Sequence Step 1 (**Batch 1: Option 3 — Streams D + E + Abandon `F1CE20EC`**), reserving Stream A (`0BD7D83C`, `6187B1EE`, `578B8678`) for Batch 2 and excluding Stream B (`059-F` and `059.001-T`..`059.014-T`), Stream C (`ECD56875`, `AC2E02C0`, `787C92F9`, `8EFB7D92`, `FF798FA3`), and externally blocked trackers (`013.008-T`, `060-F` status).

Twenty-two of the 27 Stream D and Stream E stash entries carry the `DEFERRED SCOPE EXPANSION` token captured by Ship under P-021 C2. Under P-021 C6, every `DEFERRED SCOPE EXPANSION` entry must pass through Stage duplicate detection, mandatory late-identifier reconciliation, and durable deliberation before any planning or archival disposition occurs. We must also enforce strict P-010 Role Boundary separation (Stage owns `.backlogit/queue/060-F.md` planning fields and `docs/exec-plans/*.md` plan artifacts, which Ship is forbidden from modifying) and 100% non-Rust artifact-class isolation for the resulting shipment `056-S`.

## Research Findings

### Prior Learnings (`docs/compound/`)

* **Level-1 ID collision prevention (`docs/compound/backlogit-level1-id-collision-across-parent-types.md`)**: `backlogit` shares the `{NNN}` prefix across `feature` and `chore` parents that spawn `{NNN}.{nnn}-T` children. Because `max(feature) = 060` (`060-F`) exceeds `max(chore) = 043` (`043-C`), creating a task-spawning parent with `--type feature` (`061-F`) guarantees zero `{NNN}` collision across queue and archive.
* **Harness manifest drift and checksums (`docs/compound/workflow-issues/harness-manifest-stale-paths-hide-drift-2026-07-09.md`)**: `.autoharness/harness-manifest.yaml` records both template variables (`LANGUAGE_VERSION`, `LANGUAGE_VERSION_DETAIL`, `ORCHESTRATOR_*`) and per-file SHA-256 checksums for rendered artifacts. Updating managed files requires refreshing their checksums in `.autoharness/harness-manifest.yaml` so `autoharness verify-workspace` stays clean.
* **Dirty working-tree preservation (`docs/compound/workflow-issues/post-merge-branch-preserve-dirty-file-2026-08-29.md`)**: `.autoharness/config.yaml` currently carries an intentional uncommitted operator edit setting `model_routing.orchestrator` to `gemini-4-argon` / `google` / `high` / `long_context`. Stage must not stage or commit `.autoharness/config.yaml` on `main` (P-010 Role Boundary); instead, Stage commits only Stage-owned paths and documents the exact target config diff for Ship's `3FFE51B4` task (`061.005-T`).

### Codebase and Verification Evidence

* **`autoharness verify-workspace --workspace C:\Source\GitHub\kbdb --json`**:
  * Reports `strict_schema_blockers: []`, `blockers: []`, and exactly 4 `warnings`:
    1. `ROUTE_VARIABLE_STALE: ORCHESTRATOR_FAMILY recorded=claude-sonnet-5.5 config=gemini-4-argon` in `.autoharness/harness-manifest.yaml`
    2. `ROUTE_VARIABLE_STALE: ORCHESTRATOR_PROVIDER recorded=anthropic config=google` in `.autoharness/harness-manifest.yaml`
    3. `ROUTE_VARIABLE_STALE: ORCHESTRATOR_REASONING_EFFORT recorded=medium config=high` in `.autoharness/harness-manifest.yaml`
    4. `frontmatter-conformity`: `.github/agents/subagents/rust-mcp-expert.agent.md` (`FM_MISSING_REQUIRED` for `max_subagent_tier`, `model_family`, `model_provider`, `reasoning_effort`, plus `FM_UNKNOWN_KEY` on `model_routing`)
* **MSRV 1.88 residual audit (`358A5E68`, `906BA4E3`)**:
  * `docs/developer-guide.md` still declares `1.75+ stable` (line 13) and `rust-version = "1.75"` (line 108).
  * `.autoharness/workspace-profile.yaml` (line 6) and `.autoharness/harness-manifest.yaml` (lines 804–805) still record `edition 2021, rust-version 1.75`.
  * `.github/instructions/rust-mcp-server.instructions.md` (line 698) and `.github/agents/subagents/rust-mcp-expert.agent.md` (line 429) still use `FROM rust:1.75 as builder`.
  * In `docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md` (`906BA4E3`), Stage commit `c5992c2` already aligned the primary H3-A and root MSRV references to `1.88`. Because Ship is forbidden by P-010 (`Planning: Create or modify deliberation, spike, plan, or review artifacts -> Forbidden`) from editing `docs/exec-plans/*.md`, Stage directly aligned the 5 remaining non-historical root-workspace `1.75` occurrences (lines 199, 1264, 1408, 2180, 2418) to `1.88` during this Stage session while preserving all standalone `tools/mcp-probe` `1.75` requirements and historical review sections.
* **Shipment ID `056-S` availability**: Verified zero prior allocation of `056-S` across `.backlogit/queue/`, `.backlogit/archive/`, `.backlogit/logs/`, and `.backlogit/hooks_queue.jsonl` (`055-S` is the highest allocated shipment ID).

## P-021 C5 and C6 Triage Obligations

### Unconditional Duplicate Detection Scan — Obligation A

Stage scanned all 36 active stash entries in `.backlogit/stash.jsonl` and all 58 archived stash entries in `.backlogit/archive/stash.jsonl`. Every one of the 22 `DEFERRED SCOPE EXPANSION` entries in Stream D and Stream E describes a distinct expansion:

* `BAD41DF2` (`scripts/start.ps1.tmpl`) and `8AFB7B3A` (`scripts/start.sh.tmpl`) are sibling captures for distinct external template files, not duplicates.
* `9A31F048`, `84CA0D08`, `1FF1BDC0`, `D9CB4ACF`, `2EFFA000`, `80083AF8`, `55AC021B`, and `8C8491A4` are distinct per-thread captures from PRs #128–#131 targeting separate metadata fields, wording claims, and source-reference lines.
* **Outcome**: **CLEAN DUPLICATE SCAN** across all 22 `DEFERRED SCOPE EXPANSION` entries in Batch 1 (zero duplicate entries found).

### Mandatory Late-Identifier Reconciliation — Obligation B

For every `DEFERRED SCOPE EXPANSION` entry in Batch 1 carrying one or more `N/A` source-reference fields, Stage searched the Ship-owned closure and residual-risk records (`docs/closure/`, `docs/memory/compacted/`) and recorded the reconciliation outcome:

| Stash ID | Captured `N/A` Fields | Reconciled Identifiers & Source Record | Terminal Disposition |
|---|---|---|---|
| `CCAC612D` | `task_id`, `feature_id`, `shipment_id`, `pr_number`, `review_thread_id` | Recovered `pr_number=118` from `docs/closure/2026-09-04-pr-118-startup-checkpoint-recovery-post-merge-closure.md` (round 1 `3080dc8`); chore-branch session had no shipment/feature/task and no late thread ID | `pr_number=118` reconciled; remaining `N/A` fields stand as truthful terminal record |
| `BAD41DF2` | `task_id`, `feature_id`, `shipment_id` | Standalone chore-branch PR `#118` (`PRRT_kwDORiB5E86fdy0_`); no shipment, feature, or task existed | No late identifier found; `N/A` stands as truthful terminal record |
| `8AFB7B3A` | `task_id`, `feature_id`, `shipment_id` | Standalone chore-branch PR `#118` (`PRRT_kwDORiB5E86fdy1O`); no shipment, feature, or task existed | No late identifier found; `N/A` stands as truthful terminal record |
| `67BA0629` | `task_id`, `feature_id`, `shipment_id` | Standalone closure PR `#119` (`PRRT_kwDORiB5E86ff2Hy`); no shipment, feature, or task existed | No late identifier found; `N/A` stands as truthful terminal record |
| `1074A164` | `task_id` | Cross-cutting `.backlogit/stash.jsonl` schema-doc finding on `049-S` / `056-F` / PR `#120` (`PRRT_kwDORiB5E86h2Rno`); not scoped to a single task | No late task identifier found; `task_id=N/A` stands |
| `D948EC0B` | `review_thread_id` | Surfaced only in Copilot review summary narrative on PR `#125` (`054-S` / `056.028-T`), never posted as an inline thread | Genuine threadless finding; `review_thread_id=N/A` stands |
| `9A31F048` | `task_id`, `feature_id`, `shipment_id` | Reconciled `feature_id=060-F`, `deliberation_id=004-DL`, `shipment_id=054-S` from `D9CB4ACF` and `docs/memory/compacted/2026-09-14-054-s-tooling-gap-compacted.md` | `feature_id=060-F`, `shipment_id=054-S` reconciled; `task_id=N/A` stands |
| `84CA0D08` | `task_id`, `feature_id`, `shipment_id` | Reconciled `feature_id=060-F`, `deliberation_id=004-DL`, `shipment_id=054-S` from `D9CB4ACF` and `docs/memory/compacted/2026-09-14-054-s-tooling-gap-compacted.md` | `feature_id=060-F`, `shipment_id=054-S` reconciled; `task_id=N/A` stands |
| `1FF1BDC0` | `task_id`, `feature_id`, `shipment_id` | Reconciled `feature_id=060-F`, `deliberation_id=004-DL`, `shipment_id=054-S` from `D9CB4ACF` and `docs/memory/compacted/2026-09-14-054-s-tooling-gap-compacted.md` (`requires deliberation: true` per `2EFFA000`) | `feature_id=060-F`, `shipment_id=054-S` reconciled; `task_id=N/A` stands |
| `D9CB4ACF` | `task_id` | PR `#129` (`060-F` / `054-S`, `PRRT_kwDORiB5E86iCT1B`); no task existed | No late task identifier found; `task_id=N/A` stands |
| `2EFFA000` | `task_id` | PR `#129` (`060-F` / `054-S`, `PRRT_kwDORiB5E86iCZUw`); no task existed | No late task identifier found; `task_id=N/A` stands |
| `80083AF8` | `shipment_id` (`task_id=004-DL` misclassified) | Reconciled `deliberation_id=004-DL`, `task_id=N/A`, `shipment_id=054-S` per `8C8491A4` and `004-DL` provenance | `deliberation_id=004-DL`, `shipment_id=054-S` reconciled; `task_id=N/A` stands |
| `55AC021B` | `shipment_id` (`task_id=004-DL` misclassified) | Reconciled `deliberation_id=004-DL`, `task_id=N/A`, `shipment_id=054-S` per `8C8491A4` and `004-DL` provenance | `deliberation_id=004-DL`, `shipment_id=054-S` reconciled; `task_id=N/A` stands |
| `8C8491A4` | `task_id` | PR `#131` (`004-DL` / `060-F` / `054-S`, `PRRT_kwDORiB5E86iC8Np`); no task existed | No late task identifier found; `task_id=N/A` stands |
| `890D4468` | `task_id`, `feature_id` | Reconciled `feature_id=056-F` from `049-S` / `053-S` closure context on PR `#135` (`PRRT_kwDORiB5E86xwC0a`) | `feature_id=056-F` reconciled; `task_id=N/A` stands |
| `358A5E68` | `pr_number`, `review_thread_id` | Reconciled `pr_number=136` from `053-S` delivery PR; pre-PR local review finding had no GitHub review thread | `pr_number=136` reconciled; `review_thread_id=N/A` stands |
| `0E67835A` | `pr_number`, `review_thread_id` | Reconciled `pr_number=145` from `055-S` Pass 1 closure context (`E5C4DFFC`); local `verify-workspace` finding had no review thread | `pr_number=145` reconciled; `review_thread_id=N/A` stands |

*(Note: `7A883184`, `8E8C6272`, `81588CD4`, and `906BA4E3` already had all five source-ref fields populated at capture time.)*

## Options Evaluated

### Option A: Cohesive Non-Rust Hygiene Shipment (`056-S`) + Direct Stage Disposition of Moot/Stage-Owned Captures (Recommended)

* **Description**:
  1. Abandon `F1CE20EC` via `backlogit stash archive F1CE20EC` per explicit operator directive.
  2. Retire completed deliberations `003-DL` and `004-DL` (`queued -> active -> done -> archived`).
  3. Apply Stage-owned planning/backlog hygiene directly in Stage where Ship is forbidden by P-010 (`docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md` for `906BA4E3` and `.backlogit/queue/060-F.md` for `9A31F048`, `1FF1BDC0`, `55AC021B`, `80083AF8`).
  4. Disposition and archive moot, historical, external-repo, and optional Rust-source cosmetic captures (`7A883184`, `8E8C6272`, `81588CD4`, `D948EC0B`, `BAD41DF2`, `8AFB7B3A`, `890D4468`, `84CA0D08`, `D9CB4ACF`, `2EFFA000`, `8C8491A4`, `8C2E313D`, `67BA0629`, `CCF0F0CE`, `B883681D`, `B8C0851E`) via `backlogit stash archive`.
  5. Plan, review, harvest, and assemble the 6 actionable non-Rust hygiene entries (`358A5E68`, `0E67835A`, `3FFE51B4`, `1074A164`, `C365AB98`, `CCAC612D`) into covering feature `061-F` and fully-covered-root shipment `056-S`.
* **Pros**: Preserves 100% non-Rust artifact-class isolation, respects P-010 Role Boundary constraints for both Stage and Ship, resolves all 4 `autoharness verify-workspace` warnings, and leaves only the 8 excluded Stream A + Stream C stash entries active.
* **Cons**: Requires careful coordination of the uncommitted `.autoharness/config.yaml` operator edit across the Stage-to-Ship handoff.
* **Effort estimate**: Low–Medium (7 width-isolated tasks, `<2h` each).
* **Fit**: Complete alignment with operator directives and P-010/P-015/P-017/P-021 governance.

### Option B: Include Optional Rust-Source F6 Doc Comment Edits (`B883681D`, `B8C0851E`) and Historical Closure Rewrites in `056-S`

* **Description**: Fold `src/main.rs` and `src/db/store.rs` doc-comment wording tweaks (`B883681D`, `B8C0851E`) and edits to compacted/historical closure and memory artifacts (`8C2E313D`, `67BA0629`, `CCF0F0CE`) into `056-S`.
* **Pros**:Touches every low-priority cosmetic suggestion from `047-S` and `048-S`.
* **Cons**: Violates artifact-class isolation by mixing Rust source (`src/main.rs`, `src/db/store.rs`) into a docs/config/harness hygiene shipment, forces full Rust CI/test/audit gates on a metadata shipment, violates P-010 if Ship or Stage mutates another agent's historical memory (`CCF0F0CE`), and churns already-compacted closure artifacts.
* **Effort estimate**: Medium–High.
* **Fit**: Poor — contradicts explicit operator guidance to keep `056-S` 100% non-Rust and avoid historical artifact churn.

## Trade-off Comparison

| Criterion | Option A (Non-Rust Hygiene + Stage Direct Disposition) | Option B (Include Rust Cosmetic + Historical Rewrites) |
|---|---|---|
| Artifact-class isolation | 100% non-Rust (docs, config, `.gitignore`, `.github/`, `.autoharness/`, `scripts/`) | Mixed Rust source (`src/`) + docs/config |
| P-010 Role Boundary compliance | Strictly compliant (Stage handles `060-F.md` and `docs/exec-plans/`; Ship handles repo/harness files) | High risk of P-010 violation on plan/backlog/memory files |
| `verify-workspace` warning count | Reduced from 4 to 0 | Reduced from 4 to 0 |
| Historical artifact stability | Preserves compacted closure/memory records intact | Rewrites historical/compacted records |

## Decision

We adopt **Option A**.

### Per-Entry Disposition Matrix (Batch 1: 28 Stash Entries + 2 Queue Deliberations)

| ID | Category | Disposition & Rationale | Action |
|---|---|---|---|
| `F1CE20EC` | Operator Abandonment | Explicitly abandoned by operator directive; multi-process shared external DB serving is not pursued | Archived via `backlogit stash archive F1CE20EC` |
| `003-DL` | Queue Deliberation | Informed `057-F`, delivered and archived in `050-S` (PR #109) | Comment added, moved `queued -> active -> done`, archived (`003-DL`) |
| `004-DL` | Queue Deliberation | Informed `060-F` (`softwaresalt/backlogit#443`); `054-S -> 053-S -> 052-S -> 055-S` chain is fully shipped and archived | Comment added, moved `queued -> active -> done`, archived (`004-DL`) |
| `7A883184` | Moot Historical (`054-S`) | Historical `054-S` ID-reuse finding from PR #124; `054-S`, `053-S`, `052-S`, and `055-S` are all shipped and archived, and reallocating `054-S` now would corrupt archived closure provenance | Archive via `backlogit stash archive 7A883184` |
| `8E8C6272` | Moot Historical (`054-S`) | Historical `053-S -> 054-S` shipment dependency-edge finding from PR #124; both shipments are now shipped and archived | Archive via `backlogit stash archive 8E8C6272` |
| `81588CD4` | Moot Historical (`054-S`) | Historical `054-S` Mode R memory citation finding from PR #124; `054-S` is shipped and archived and its memory is compacted | Archive via `backlogit stash archive 81588CD4` |
| `D948EC0B` | External Tool (`backlogit`) | Upstream `backlogit` internal `hooks_queue.jsonl` `status_delta` generation behavior; owned in external `backlogit` binary, not `kbdb` source | Archive via `backlogit stash archive D948EC0B` |
| `BAD41DF2` | External Tool (`autoharness`) | External `autoharness` package template `scripts/start.ps1.tmpl` is not tracked in this repo; local `start.ps1` already carries the fix | Archive via `backlogit stash archive BAD41DF2` |
| `8AFB7B3A` | External Tool (`autoharness`) | External `autoharness` package template `scripts/start.sh.tmpl` is not tracked in this repo; local `start.sh` already carries the fix | Archive via `backlogit stash archive 8AFB7B3A` |
| `890D4468` | Moot Gate Semantics | Question whether `049-S` closure `mcp-client-smoke` should block `053-S` `pre_claim`; `053-S`, `052-S`, and `055-S` (including T4 live interactive `/mcp show` smoke verification in `056.004-T`) have all completed and shipped | Archive via `backlogit stash archive 890D4468` |
| `9A31F048` | Stage-Owned Backlog Hygiene | Added `source_stash_id: 1C9CD261` and `source_deliberation_id: 004-DL` to `.backlogit/queue/060-F.md` frontmatter `custom_fields` directly in Stage (P-010 Stage authority; `060-F` stays `blocked`) | Applied in Stage; archive via `backlogit stash archive 9A31F048` |
| `1FF1BDC0` | Stage-Owned Backlog Hygiene | Narrowed `.backlogit/queue/060-F.md` ownership claim to state that no local crate (`graphtor-core`, `graphtor-docs` / `kbdb`, or `tools/mcp-probe`) contains `backlogit`'s shipment state machine; paired Stage memory is already compacted/archived | Applied in Stage; archive via `backlogit stash archive 1FF1BDC0` |
| `55AC021B` | Stage-Owned Backlog Hygiene | Updated `.backlogit/queue/060-F.md` to describe `softwaresalt/backlogit#443` as an adapted summary of `060-F`'s five acceptance criteria; paired Stage memory is already compacted/archived | Applied in Stage; archive via `backlogit stash archive 55AC021B` |
| `80083AF8` | Stage-Owned Backlog Hygiene | Regenerated system-managed `updated_at` on `004-DL` (via Stage closure/archival) and `060-F` (via `backlogit comment add` + `backlogit update 060-F --priority high`) | Applied in Stage; archive via `backlogit stash archive 80083AF8` |
| `84CA0D08` | Moot P-021 Meta-Capture | Historical `.backlogit/archive/stash.jsonl` `reason` field note for `1C9CD261`; `060-F.md` now carries machine-readable `custom_fields.source_stash_id: 1C9CD261` (`9A31F048`), providing forward/reverse provenance without hand-editing archived JSONL | Archive via `backlogit stash archive 84CA0D08` |
| `D9CB4ACF` | Moot P-021 Meta-Capture | Self-referential source-ref note on `9A31F048`, `84CA0D08`, `1FF1BDC0`; reconciled in Obligation B above and parent entries are now resolved/archived | Archive via `backlogit stash archive D9CB4ACF` |
| `2EFFA000` | Moot P-021 Meta-Capture | Self-referential `requires deliberation: true` note on `1FF1BDC0`; honored by routing `1FF1BDC0` through this P-021 C6 deliberation | Archive via `backlogit stash archive 2EFFA000` |
| `8C8491A4` | Moot P-021 Meta-Capture | Self-referential source-ref note on `80083AF8` and `55AC021B`; reconciled in Obligation B above and parent entries are now resolved/archived | Archive via `backlogit stash archive 8C8491A4` |
| `906BA4E3` | Stage-Owned Plan Hygiene | Ship is forbidden by P-010 from modifying `docs/exec-plans/*.md`. Stage commit `c5992c2` aligned primary H3-A/root MSRV references to `1.88`, and this Stage pass aligned the remaining 5 non-historical root-workspace `1.75` occurrences (lines 199, 1264, 1408, 2180, 2418) in `docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md` to `1.88` while preserving `tools/mcp-probe` `1.75` requirements | Applied in Stage; archive via `backlogit stash archive 906BA4E3` |
| `8C2E313D` | Elapsed Observation Window | Post-deploy observation window for `048-S` (merged 2026-08-17, compacted 2026-09-01) has long elapsed (>70 days) and `serve` posture classification was verified healthy across `049-S`..`055-S` with zero rollback triggered | Dispositioned healthy; archive via `backlogit stash archive 8C2E313D` |
| `67BA0629` | Elapsed Observation Window | Post-deploy 14-day validation window for PR #118 (merged 2026-09-05) has long elapsed (>55 days) regardless of anchor date, and `mcp-client-smoke` was completed in `055-S` (`056.004-T`); mutating historical PR #118 closure is unnecessary churn | Dispositioned satisfied; archive via `backlogit stash archive 67BA0629` |
| `CCF0F0CE` | Historical Ship Memory | Optional pass-count wording note on Ship-authored `docs/memory/2026-08-17/047-s-session-closure-memory.md`; Stage is forbidden by P-010 from mutating Ship's memory and `047-S` is long closed/compacted | Dispositioned not-needed; archive via `backlogit stash archive CCF0F0CE` |
| `B883681D` | Optional Rust Cosmetic | Optional cosmetic F6 cross-reference in `src/main.rs` doc comment; F6 is already documented across 5 surfaces and touching `src/main.rs` would violate 100% non-Rust artifact-class isolation | Dispositioned not-needed; archive via `backlogit stash archive B883681D` |
| `B8C0851E` | Optional Rust Cosmetic | Optional F6 "overlapping guard lifetimes" wording across `src/db/store.rs` and design doc; explicitly noted in `047-S` closure as non-convergent diminishing returns for a documented best-effort residual and would touch Rust source | Dispositioned not-needed; archive via `backlogit stash archive B8C0851E` |
| `358A5E68` | Actionable Scope (`056-S`) | Align stale Rust `1.75` MSRV declarations to `1.88` in `docs/developer-guide.md`, `.autoharness/workspace-profile.yaml`, `.autoharness/harness-manifest.yaml`, `.github/instructions/rust-mcp-server.instructions.md`, and `.github/agents/subagents/rust-mcp-expert.agent.md` | Promote to Plan (`061.001-T`, `061.002-T`, `061.004-T`, `061.005-T`) |
| `0E67835A` | Actionable Scope (`056-S`) | Complete missing required frontmatter (`max_subagent_tier`, `model_family`, `model_provider`, `reasoning_effort`, `context_tier`) and replace unknown `model_routing` key with `## Model Routing` section in `.github/agents/subagents/rust-mcp-expert.agent.md` | Promote to Plan (`061.002-T`) |
| `3FFE51B4` | Actionable Scope (`056-S`) | Reconcile model-routing config, manifest variables (`ORCHESTRATOR_*`), frontmatter, and prose across `.autoharness/config.yaml`, `.autoharness/harness-manifest.yaml`, `.github/agents/_orchestrator.agent.md`, and `.github/instructions/adversarial-review.instructions.md` | Promote to Plan (`061.003-T`, `061.005-T`) |
| `1074A164` | Actionable Scope (`056-S`) | Update `.github/instructions/backlogit-sql-schema.instructions.md` (`stash_entries.kind` table note) to document all CLI-accepted kinds plus workspace-configured WIT types (`chore`), and update its manifest checksum in `.autoharness/harness-manifest.yaml` | Promote to Plan (`061.004-T`, `061.005-T`) |
| `C365AB98` | Actionable Scope (`056-S`) | Remove duplicate blanket `.engram/` entry in `.gitignore` (`# UE` section) that overrides earlier `!.engram/*` negations | Promote to Plan (`061.006-T`) |
| `CCAC612D` | Actionable Scope (`056-S`) | Delete ad-hoc debugging helper scripts `scripts/git_commands.py` and `scripts/run_git_commands.sh` | Promote to Plan (`061.007-T`) |

## Rejected Alternatives

* **Option B (Mixing Rust source doc-comment edits and historical memory/closure edits into `056-S`)**: Rejected because it breaks non-Rust artifact-class isolation, triggers unnecessary full Rust build/test/audit gates for cosmetic comments, and risks P-010 Role Boundary violations on Ship-authored memory files.
* **Delegating `906BA4E3` (`docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md`) or `060-F.md` edits to Ship**: Rejected because Ship's P-010 Role Boundary explicitly forbids Ship from modifying plan artifacts (`docs/exec-plans/*.md`) or backlog item planning fields (`.backlogit/queue/060-F.md`).

## Unresolved Questions

None. All 28 in-scope stash entries and 2 completed deliberations have deterministic dispositions grounded in repository evidence.

## Risks and Mitigations

* **Risk 1 — Dirty `.autoharness/config.yaml` working-tree file during Ship branch creation (P-011)**:
  * *Mitigation*: Stage commits only Stage-owned paths (`.backlogit/`, `docs/decisions/`, `docs/exec-plans/`, `docs/memory/`) on `main` and leaves `.autoharness/config.yaml` untouched in the working tree. Task `061.005-T` records the exact target `.autoharness/config.yaml` diff (`orchestrator: gemini-4-argon / google / high / long_context`) so Orchestrator/Ship can either stash-and-pop `.autoharness/config.yaml` onto the feature branch or revert-and-reapply it on the feature branch to satisfy P-011 cleanly.
* **Risk 2 — `.autoharness/harness-manifest.yaml` checksum drift after editing managed `.github/` or `.autoharness/` files**:
  * *Mitigation*: Task `061.005-T` (which depends on `061.002-T`, `061.003-T`, and `061.004-T`) owns `.autoharness/harness-manifest.yaml`, updates the SHA-256 checksums for all modified manifest-tracked files (`.autoharness/config.yaml`, `.github/agents/_orchestrator.agent.md`, `.github/instructions/adversarial-review.instructions.md`, and `.github/instructions/backlogit-sql-schema.instructions.md`), and runs `autoharness verify-workspace --workspace C:\Source\GitHub\kbdb --json` to prove `strict_schema_blockers: []`, `blockers: []`, and `warning_instances: 0`.
