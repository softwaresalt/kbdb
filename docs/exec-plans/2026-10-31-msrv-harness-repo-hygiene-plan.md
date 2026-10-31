---
title: "Implementation Plan: MSRV 1.88 Alignment, Harness Metadata Conformity, and Repository Hygiene (061-F / 056-S)"
description: "Structured implementation plan for Batch 1 (Option 3: Streams D + E) covering residual MSRV 1.88 declarations, subagent frontmatter conformity, model-routing reconciliation, backlogit schema docs, .gitignore dedup, and ad-hoc script removal"
source: "docs/decisions/2026-10-31-option-3-msrv-harness-repo-hygiene-deliberation.md"
stash_ids:
  - "358A5E68"
  - "0E67835A"
  - "3FFE51B4"
  - "1074A164"
  - "C365AB98"
  - "CCAC612D"
backlog_refs:
  - "061-F"
  - "061.001-T"
  - "061.002-T"
  - "061.003-T"
  - "061.004-T"
  - "061.005-T"
  - "061.006-T"
  - "061.007-T"
  - "056-S"
tags:
  - "msrv-1-88"
  - "harness-hygiene"
  - "model-routing"
  - "repo-hygiene"
  - "056-s"
---

## Problem Frame

Following the constitutional MSRV `1.88` amendment (`053-S`, PR #136) and the completion of Feature `056-F` (`055-S`), six actionable non-Rust hygiene and alignment gaps remain in the repository (`docs/decisions/2026-10-31-option-3-msrv-harness-repo-hygiene-deliberation.md`):

1. **Residual Rust `1.75` MSRV declarations (`358A5E68`)**: `docs/developer-guide.md` (lines 13 and 108), `.autoharness/workspace-profile.yaml` (line 6), `.autoharness/harness-manifest.yaml` (lines 804–805), `.github/instructions/rust-mcp-server.instructions.md` (line 698), and `.github/agents/subagents/rust-mcp-expert.agent.md` (line 429) still reference Rust `1.75` instead of the ratified `1.88` floor.
2. **Subagent frontmatter nonconformity (`0E67835A`)**: `.github/agents/subagents/rust-mcp-expert.agent.md` triggers `FM_MISSING_REQUIRED` (`max_subagent_tier`, `model_family`, `model_provider`, `reasoning_effort`) and `FM_UNKNOWN_KEY` (`model_routing`) in `autoharness verify-workspace`.
3. **Model-routing configuration, manifest, frontmatter, and prose drift (`3FFE51B4`)**:
   * `.autoharness/config.yaml` carries an operator-authored update setting `model_routing.orchestrator` to `gemini-4-argon` / `google` / `high` / `long_context`, while `.autoharness/harness-manifest.yaml` still records `ORCHESTRATOR_FAMILY: claude-sonnet-5.5`, `ORCHESTRATOR_PROVIDER: anthropic`, and `ORCHESTRATOR_REASONING_EFFORT: medium` (triggering 3 `ROUTE_VARIABLE_STALE` warnings in `verify-workspace`).
   * `.github/agents/_orchestrator.agent.md` frontmatter and `Configuration shape` block still declare `orchestrator` as `claude-sonnet-5.5` / `anthropic` / `medium` and `ship` in `Configuration shape` as `claude-sonnet-5.5` / `anthropic` / `medium` instead of `gpt-6.1-sol` / `openai` / `medium`.
   * `.github/instructions/adversarial-review.instructions.md` (lines 60–64) still states that `alt_provider` is `google` and `alt_family` is `gemini-2.5-pro`, contradicting `.autoharness/config.yaml` and `.github/agents/subagents/adversarial-review.agent.md` where `alt_review_provider` and `alt_review_family` are empty (`""`).
4. **Derived SQL schema documentation gap (`1074A164`)**: `.github/instructions/backlogit-sql-schema.instructions.md` (line 81) documents `stash_entries.kind` as accepting only 5 values (`feature`, `task`, `bug`, `epic`, `unknown`), omitting `spike`, `subtask`, `deliberation`, `review`, `shipment`, and workspace-configured WIT types such as `chore`.
5. **Duplicate `.engram/` blanket ignore in `.gitignore` (`C365AB98`)**: A second `.engram/` line under `# UE` (line 97) overrides earlier negations (`!.engram/.version`, `!.engram/.workspace-id`, `!.engram/config.toml`, `!.engram/registry.yaml`).
6. **Ad-hoc debugging scripts in `scripts/` (`CCAC612D`)**: `scripts/git_commands.py` and `scripts/run_git_commands.sh` hardcode `C:\Source\GitHub\graphtor` and one-off commit SHAs from an interactive debugging session.

*(Note: Stage-owned `.backlogit/queue/060-F.md` updates for `9A31F048`, `1FF1BDC0`, `55AC021B`, and `80083AF8` and `docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md` updates for `906BA4E3` were applied directly by Stage under P-010 because Ship is forbidden from modifying plan artifacts or backlog item planning fields.)*

## Requirements Trace

| Stash ID | Requirement | Implementation Unit(s) |
|---|---|---|
| `358A5E68` | Align remaining stale Rust `1.75` MSRV declarations to `1.88` across docs, profile, manifest, instructions, and subagent examples | Unit 1 (`061.001-T`), Unit 2 (`061.002-T`), Unit 4 (`061.004-T`), Unit 5 (`061.005-T`) |
| `0E67835A` | Repair `FM_MISSING_REQUIRED` and `FM_UNKNOWN_KEY` frontmatter in `.github/agents/subagents/rust-mcp-expert.agent.md` | Unit 2 (`061.002-T`) |
| `3FFE51B4` | Reconcile model-routing config, manifest variables/checksums, frontmatter, and prose across `.autoharness/config.yaml`, `.autoharness/harness-manifest.yaml`, `.github/agents/_orchestrator.agent.md`, and `.github/instructions/adversarial-review.instructions.md` | Unit 3 (`061.003-T`), Unit 5 (`061.005-T`) |
| `1074A164` | Document full CLI-accepted `stash_entries.kind` set and workspace-configured WIT types (`chore`) in `.github/instructions/backlogit-sql-schema.instructions.md` | Unit 4 (`061.004-T`), Unit 5 (`061.005-T`) |
| `C365AB98` | Remove duplicate `.engram/` entry under `# UE` in `.gitignore` so `.engram/` config negations work | Unit 6 (`061.006-T`) |
| `CCAC612D` | Remove ad-hoc debugging helper scripts `scripts/git_commands.py` and `scripts/run_git_commands.sh` | Unit 7 (`061.007-T`) |

## Implementation Units

Every unit satisfies the 2-Hour Rule (`1` or `2` files, strictly `< 3` files), 100% disjoint file ownership across all 7 units, and pure non-Rust width isolation.

### Unit 1: Align Rust 1.88 MSRV in Developer Guide and Rust MCP Server Instructions (`061.001-T`)

* **Domain / Width**: Documentation (`docs/`, `.github/instructions/`)
* **Size / Complexity**: `size: XS`, `complexity: trivial`
* **Execution Posture**: `characterization-first`
* **Files Affected (2)**:
  1. `docs/developer-guide.md`
  2. `.github/instructions/rust-mcp-server.instructions.md`
* **Changes**:
  * In `docs/developer-guide.md`: update line 13 (`| Rust toolchain | 1.75+ stable |` -> `| Rust toolchain | 1.88+ stable |`) and line 108 (`rust-version = "1.75"` -> `rust-version = "1.88"`).
  * In `.github/instructions/rust-mcp-server.instructions.md`: update line 698 (`FROM rust:1.75 as builder` -> `FROM rust:1.88 as builder`).
* **Verification**:
  * Confirm zero remaining `1.75` occurrences in `docs/developer-guide.md` and `.github/instructions/rust-mcp-server.instructions.md`.

### Unit 2: Repair Frontmatter Conformity and MSRV Example in Rust MCP Expert Subagent (`061.002-T`)

* **Domain / Width**: Prompt / Agent Metadata (`.github/agents/subagents/`)
* **Size / Complexity**: `size: XS`, `complexity: low`
* **Execution Posture**: `characterization-first`
* **Files Affected (1)**:
  1. `.github/agents/subagents/rust-mcp-expert.agent.md`
* **Changes**:
  * In YAML frontmatter: remove `model_routing: "Tier 2 (Standard)"` (`FM_UNKNOWN_KEY`) and add `max_subagent_tier: 2`, `reasoning_effort: "high"`, `model_provider: "anthropic"`, `model_family: "claude-sonnet-5.5"`, and `context_tier: "long_context"` (matching `.autoharness/config.yaml` Tier 2 and `.github/agents/subagents/language-engineer.agent.md`).
  * At line 429: update `FROM rust:1.75 as builder` to `FROM rust:1.88 as builder`.
  * At the end of the file: add `## Model Routing` (`Tier 2 (Standard) — specialist guidance for Rust MCP server implementation.`) and `## Subagent Depth` (`Maximum 2 hops.`) sections per `.github/instructions/prompt-builder.instructions.md`.
* **Verification**:
  * Run `autoharness verify-workspace --workspace . --json` and confirm `.github/agents/subagents/rust-mcp-expert.agent.md` produces zero `FM_MISSING_REQUIRED` or `FM_UNKNOWN_KEY` warnings.

### Unit 3: Reconcile Model-Routing Frontmatter and Prose in Orchestrator Agent and Adversarial Review Instructions (`061.003-T`)

* **Domain / Width**: Prompt / Instruction Metadata (`.github/agents/`, `.github/instructions/`)
* **Size / Complexity**: `size: S`, `complexity: low`
* **Execution Posture**: `characterization-first`
* **Files Affected (2)**:
  1. `.github/agents/_orchestrator.agent.md`
  2. `.github/instructions/adversarial-review.instructions.md`
* **Changes**:
  * In `.github/agents/_orchestrator.agent.md`:
    * Update frontmatter (lines 8–11) to `reasoning_effort: "high"`, `model_provider: "google"`, `model_family: "gemini-4-argon"`, `context_tier: "long_context"`.
    * Update the `Configuration shape` block (lines 515–540) so `orchestrator` shows `model: "gemini-4-argon"`, `model_family: "gemini-4-argon"`, `model_provider: "google"`, `reasoning_effort: "high"`, `context_tier: "long_context"`, and `ship` shows `model_family: "gpt-6.1-sol"`, `model_provider: "openai"`, `reasoning_effort: "medium"`, `context_tier: "long_context"`.
  * In `.github/instructions/adversarial-review.instructions.md`:
    * Update the `## Alternate Model Provider Support` section (lines 55–64) to remove the stale claim that `alt_provider` is `google` and `alt_family` is `gemini-2.5-pro`, stating instead that `alt_provider` and `alt_family` are currently unconfigured (`""`) in `.autoharness/config.yaml` and `.github/agents/subagents/adversarial-review.agent.md`, so Reviewer-B uses the standard Tier 2 route unless configured.
* **Verification**:
  * Confirm frontmatter and prose in `.github/agents/_orchestrator.agent.md` and `.github/instructions/adversarial-review.instructions.md` match `.autoharness/config.yaml` and `.github/agents/subagents/adversarial-review.agent.md`.

### Unit 4: Update Backlogit SQL Schema Kind Documentation and Workspace Profile MSRV (`061.004-T`)

* **Domain / Width**: Harness Instructions & Profile Metadata (`.github/instructions/`, `.autoharness/`)
* **Size / Complexity**: `size: XS`, `complexity: trivial`
* **Execution Posture**: `characterization-first`
* **Files Affected (2)**:
  1. `.github/instructions/backlogit-sql-schema.instructions.md`
  2. `.autoharness/workspace-profile.yaml`
* **Changes**:
  * In `.github/instructions/backlogit-sql-schema.instructions.md` (`stash_entries` table, line 81): update the `kind` column note from `` `feature`, `task`, `bug`, `epic`, `unknown` `` to `` `feature`, `task`, `bug`, `epic`, `unknown`, `spike`, `subtask`, `deliberation`, `review`, `shipment`, plus workspace-configured WIT types in `.backlogit/config.yaml` (such as `chore`) ``.
  * In `.autoharness/workspace-profile.yaml` (line 6): update `version: edition 2021, rust-version 1.75` to `version: edition 2021, rust-version 1.88`.
* **Verification**:
  * Confirm `.autoharness/workspace-profile.yaml` contains zero `1.75` references and `.github/instructions/backlogit-sql-schema.instructions.md` documents workspace-configured WIT types (`chore`).

### Unit 5: Synchronize Harness Config and Manifest Variables and Checksums (`061.005-T`)

* **Domain / Width**: Harness Configuration & Manifest (`.autoharness/`)
* **Size / Complexity**: `size: S`, `complexity: low`
* **Execution Posture**: `characterization-first`
* **Dependencies**: `061.002-T`, `061.003-T`, `061.004-T`
* **Files Affected (2)**:
  1. `.autoharness/config.yaml`
  2. `.autoharness/harness-manifest.yaml`
* **Changes**:
  * In `.autoharness/config.yaml`: apply/commit the operator's `model_routing.orchestrator` route (`model_family: "gemini-4-argon"`, `model_provider: "google"`, `reasoning_effort: "high"`, `context_tier: "long_context"`) and `tier3` key ordering.
  * In `.autoharness/harness-manifest.yaml`:
    * Update `LANGUAGE_VERSION: edition 2021, rust-version 1.88` and `LANGUAGE_VERSION_DETAIL: Rust 2021 edition, rust-version 1.88` (lines 804–805).
    * Update `ORCHESTRATOR_FAMILY: gemini-4-argon`, `ORCHESTRATOR_PROVIDER: google`, and `ORCHESTRATOR_REASONING_EFFORT: high` (lines 844–846).
    * Recompute and update the SHA-256 `checksum` entries for `.autoharness/config.yaml`, `.github/agents/_orchestrator.agent.md`, `.github/instructions/adversarial-review.instructions.md`, and `.github/instructions/backlogit-sql-schema.instructions.md`.
* **Verification**:
  * Run `autoharness verify-workspace --workspace . --json` and confirm `strict_schema_blockers: []`, `blockers: []`, `warnings: []`, and `warning_instances: 0`.
  * Run `autoharness routing resolve --workspace . --site orchestrator --json` and confirm `gemini-4-argon` / `google` / `high` / `long_context`.

### Unit 6: Remove Duplicate Blanket `.engram/` Ignore in `.gitignore` (`061.006-T`)

* **Domain / Width**: Repository Git Configuration (`.gitignore`)
* **Size / Complexity**: `size: XS`, `complexity: trivial`
* **Execution Posture**: `test-first` (verify `git check-ignore -v .engram/config.toml` before and after)
* **Files Affected (1)**:
  1. `.gitignore`
* **Changes**:
  * Remove the duplicate `.engram/` line under `# UE` (around line 97) while preserving the earlier `# Engram runtime data` block (`.engram/` followed by `!.engram/.version`, `!.engram/.workspace-id`, `!.engram/config.toml`, `!.engram/registry.yaml`).
* **Verification**:
  * Run `git check-ignore -v .engram/config.toml` and `git check-ignore -v .engram/registry.yaml` and confirm both match the `!` negation lines (exit code 0 with `!` prefix) rather than being ignored by line 97, while `.engram/db` remains ignored.

### Unit 7: Remove Ad-Hoc Debugging Helper Scripts (`061.007-T`)

* **Domain / Width**: Repository Scripts Hygiene (`scripts/`)
* **Size / Complexity**: `size: XS`, `complexity: trivial`
* **Execution Posture**: `characterization-first`
* **Files Affected (2)**:
  1. `scripts/git_commands.py` (delete)
  2. `scripts/run_git_commands.sh` (delete)
* **Changes**:
  * Remove `scripts/git_commands.py` and `scripts/run_git_commands.sh` via `git rm`.
* **Verification**:
  * Verify neither file exists on disk or in `git ls-files scripts/`, and confirm zero references to `git_commands.py` or `run_git_commands.sh` exist in `.github/workflows/`, `scripts/`, or `Cargo.toml`.

## Dependency Graph

* `061.001-T` (independent)
* `061.002-T` (independent)
* `061.003-T` (independent)
* `061.004-T` (independent)
* `061.005-T` depends on `061.002-T`, `061.003-T`, `061.004-T` (computes final SHA-256 checksums in `.autoharness/harness-manifest.yaml` after managed `.github/` files are updated and runs `autoharness verify-workspace`)
* `061.006-T` (independent)
* `061.007-T` (independent)

Recommended execution order: `061.001-T -> 061.002-T -> 061.003-T -> 061.004-T -> 061.005-T -> 061.006-T -> 061.007-T`.

## Decisions and Rationale

* **Use `--type feature` (`061-F`) for the covering release unit**: Per `docs/compound/backlogit-level1-id-collision-across-parent-types.md`, using `feature` (`061-F`) guarantees zero `{NNN}` prefix collision across `feature`, `chore`, and `spike` items in `.backlogit/queue/` and `.backlogit/archive/`.
* **Centralize `.autoharness/harness-manifest.yaml` edits in `061.005-T`**: Gives every task 100% disjoint file ownership (`< 3` files per task) and ensures SHA-256 checksums for `.github/agents/_orchestrator.agent.md`, `.github/instructions/adversarial-review.instructions.md`, and `.github/instructions/backlogit-sql-schema.instructions.md` are computed once after `061.003-T` and `061.004-T` complete.
* **Keep `056-S` 100% non-Rust**: No files under `src/`, `tests/`, `tools/`, `Cargo.toml`, or `Cargo.lock` are touched.

## Risks and Caveats

* **Dirty `.autoharness/config.yaml` working-tree edit at Ship branch creation (P-011)**:
  * Stage leaves `.autoharness/config.yaml` un-staged on `main` (committing only Stage-owned paths). Before Ship runs its P-011 Branch Creation Gate, Orchestrator or Ship should stash or carry the `.autoharness/config.yaml` working-tree diff onto the feature branch where `061.005-T` commits it.

## Plan Hardening Signals (REQUIRED)

* **public API, schema, or contract change**: absent — no Rust code, CLI surface, MCP tool schema, or config schema changes.
* **security, auth, permission, or compliance-sensitive behavior**: absent — no auth, containment, or permission changes.
* **migration, backfill, destructive data/config action, or irreversible step**: present (narrow) — `061.007-T` deletes two tracked ad-hoc debugging scripts (`scripts/git_commands.py`, `scripts/run_git_commands.sh`) via `git rm` (reversible via git history, explicitly authorized by operator Batch 1 scope).
* **external integration, operator checkpoint, or external dependency**: absent — all verification is local (`autoharness verify-workspace`, `git check-ignore`).
* **high runtime, rollout, or rollback risk**: absent — 100% non-Rust documentation, harness metadata, `.gitignore`, and ad-hoc script cleanup.

Requires plan hardening: yes

## Plan Hardening

* **Why hardening was invoked**: `strict_safety.enabled: true` is active in `.autoharness/config.yaml`, and Unit 7 (`061.007-T`) deletes two tracked files (`scripts/git_commands.py`, `scripts/run_git_commands.sh`).
* **Consulted learnings and instructions**:
  * `docs/compound/backlogit-level1-id-collision-across-parent-types.md`
  * `docs/compound/workflow-issues/harness-manifest-stale-paths-hide-drift-2026-07-09.md`
  * `docs/compound/workflow-issues/post-merge-branch-preserve-dirty-file-2026-08-29.md`
  * `.github/instructions/prompt-builder.instructions.md`
* **Risky Action Classification (`strict-safety`)**:
  * `ProposedAction` (`061.007-T` — delete ad-hoc debug scripts):
    * `targets`: `scripts/git_commands.py`, `scripts/run_git_commands.sh`
    * `change_kind`: file removal (`git rm`)
    * `ActionRisk`: `low` (reversible git-tracked removal of unused one-off diagnostic scripts that hardcode `C:\Source\GitHub\graphtor`; explicitly authorized in operator Batch 1 scope)
    * `rollback`: `git revert <commit>` or `git checkout HEAD~1 -- scripts/git_commands.py scripts/run_git_commands.sh`
    * `approval_required`: satisfied by operator Batch 1 prompt directive (`CCAC612D: Remove the ad-hoc debugging helper scripts scripts/git_commands.py and scripts/run_git_commands.sh`)
    * `ActionResult`: `planned`
* **Review-gate capability notes**: Under P-012, `plan-review` must emit literal `dispatch_mode:` and `decision:` markers and evaluate all applicable personas from the Persona Rubric Adapter.

## Runtime Verification and Closure

* **Runtime surface impact**: None. No Rust source (`src/`), binary, CLI command, or MCP server behavior is modified by any unit in `056-S`.
* **Verification**:
  * `autoharness verify-workspace --workspace . --json` (`strict_schema_blockers: []`, `blockers: []`, `warning_instances: 0`)
  * `autoharness routing resolve --workspace . --site orchestrator --json`
  * `git check-ignore -v .engram/config.toml` and `git check-ignore -v .engram/registry.yaml`
* **Operational closure expectations**: Post-merge closure (`operational-closure` skill) records `056-S` as a non-runtime documentation/harness/hygiene shipment with immediate validation completion upon `verify-workspace` zero-warning confirmation and `git revert` as the rollback path.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* **Capability declaration (P-012)**: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
  * **Rationale**: Stage's runtime tool contract (`<tools><task>`) mandates handling reviews whose total evidence fits a direct read inline without delegating by persona/angle. Per `.github/skills/plan-review/SKILL.md` (`## Dispatch Capability and Declared Degradation`, Step 2), Stage applies every triggered persona rubric inline and records `dispatch_mode: single-agent-declared-degradation`.
* **Hardening check (P-006 / strict-safety)**: `Requires plan hardening: yes` is present, and `## Plan Hardening` classifies the `061.007-T` script removal with `ProposedAction` / `ActionRisk` / `ActionResult` metadata and rollback instructions.

### Persona Coverage Table

| Persona | Trigger Status | Mode | Findings |
|---|---|---|---|
| Constitution Reviewer | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Rust Reviewer | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Scope Boundary Auditor | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Learnings Researcher | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Architecture Strategist | Cross-model (Always) | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Agent-Native Parity Reviewer | Triggered (agent/instruction metadata) | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Security Lens Reviewer | Not triggered (no auth/API/trust boundary) | N/A (verified non-applicable) | 0 |

### Per-Persona Findings

* **Constitution Reviewer**: `0` findings. All 7 units respect P-010 Role Boundaries (Stage already applied the Stage-owned `060-F.md` and `docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md` edits directly; Ship owns the 7 repo/config/harness tasks), P-003 granularity (`1–2` files per task), and the ratified MSRV `1.88` amendment.
* **Rust Reviewer**: `0` findings. The shipment is 100% non-Rust and aligns remaining documentation/Docker/profile/manifest MSRV references to `1.88` while leaving standalone `tools/mcp-probe` at `1.75`.
* **Scope Boundary Auditor**: `0` findings. Excluded streams (Stream A: `0BD7D83C`, `6187B1EE`, `578B8678`; Stream B: `059-F` family; Stream C: `ECD56875`, `AC2E02C0`, `787C92F9`, `8EFB7D92`, `FF798FA3`; blocked `013.008-T` and `060-F` status) are untouched.
* **Learnings Researcher**: `0` findings. Incorporates `backlogit-level1-id-collision-across-parent-types.md` (using `061-F`), `harness-manifest-stale-paths-hide-drift-2026-07-09.md` (manifest checksum sync in `061.005-T`), and `post-merge-branch-preserve-dirty-file-2026-08-29.md` (preserving dirty `.autoharness/config.yaml`).
* **Architecture Strategist**: `0` findings. File ownership across `061.001-T`..`061.007-T` is 100% disjoint, and `061.005-T` depends on `061.002-T`, `061.003-T`, and `061.004-T` so manifest checksums are computed once.
* **Agent-Native Parity Reviewer**: `0` findings. Updating `.github/agents/subagents/rust-mcp-expert.agent.md`, `.github/agents/_orchestrator.agent.md`, `.github/instructions/adversarial-review.instructions.md`, and `.github/instructions/backlogit-sql-schema.instructions.md` restores full parity between `.autoharness/config.yaml`, `autoharness verify-workspace`, and agent-facing instructions.

### Gate Verdict

* **Merged counts**: `0 P0, 0 P1, 0 P2, 0 P3`
* **Gate decision**: `PASS` — ready for `harvest` into `061-F` and `061.001-T`..`061.007-T` and Mode H shipment assembly into `056-S`.
