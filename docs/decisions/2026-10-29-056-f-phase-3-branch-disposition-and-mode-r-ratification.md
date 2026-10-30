---
title: "Stage ratification: 056-F Phase 2 conditional branch disposition and Phase 3 Mode R shipment authorization"
description: "Authoritative Stage decision evaluating all 14 remaining selection:pending Phase 2 conditional tasks of 056-F against completed T0, H3-B, E1, discriminator, and H3-A evidence, dispositioning unselected branches as done/selection:not-needed, aligning 056-F planning surfaces to the ratified Rust 1.88 root MSRV floor, and issuing the durable Step 5.5 Mode R authorization for the Phase 3 task-only shipment [056.012-T, 056.013-T, 056.004-T]"
doc_type: "decision"
topic: "Evidence-based completion path, conditional branch disposition, MSRV 1.88 planning reconciliation, and Phase 3 Mode R shipment assembly for feature 056-F"
depth: "standard"
decision_status: "decided"
session_date: "2026-10-29"
agent: "stage"
promoted_to: "docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md"
stash_ids:
  - "7BF1961D"
backlog_refs:
  - "056-F"
  - "049-S"
  - "054-S"
  - "053-S"
  - "052-S"
  - "055-S"
  - "056.001-T"
  - "056.002-T"
  - "056.003-T"
  - "056.004-T"
  - "056.005-T"
  - "056.006-T"
  - "056.007-T"
  - "056.008-T"
  - "056.009-T"
  - "056.010-T"
  - "056.011-T"
  - "056.012-T"
  - "056.013-T"
  - "056.014-T"
  - "056.015-T"
  - "056.016-T"
  - "056.017-T"
  - "056.018-T"
  - "056.019-T"
  - "056.020-T"
  - "056.021-T"
  - "056.022-T"
  - "056.023-T"
  - "056.024-T"
  - "056.025-T"
  - "056.026-T"
  - "056.027-T"
  - "056.028-T"
  - "056.029-T"
  - "056.030-T"
  - "056.031-T"
  - "056.032-T"
  - "056.033-T"
linked_artifacts:
  - "docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md"
  - "docs/decisions/2026-08-21-mcp-serve-initialize-os-error-232-deliberation.md"
  - "docs/decisions/2026-08-29-mcp-serve-discover-preinitialize-evidence.md"
  - "docs/decisions/2026-09-13-stage-056.026-T-disposition-not-needed.md"
  - "docs/decisions/2026-10-29-rust-1-75-rmcp-dependency-compatibility-decision.md"
  - "docs/decisions/2026-10-29-mcp-serve-discover-compat-exact-client-evidence.md"
  - "docs/closure/2026-09-13-049-s-mcp-serve-handshake-post-merge-closure.md"
  - "docs/closure/2026-09-14-054-s-mcp-probe-ci-post-merge-closure.md"
  - "docs/closure/2026-10-29-053-s-rust-1-88-msrv-post-merge-closure.md"
  - "docs/closure/2026-10-29-052-s-h3-a-discover-compat-post-merge-closure.md"
tags:
  - "stage"
  - "056-f"
  - "mode-r"
  - "selection-gate"
  - "dark-factory"
  - "msrv-1-88"
  - "phase-3"
---

## P-017 Dark-Factory Context (Stage Session Scope Only)

This artifact records the bounded Stage deliberation, conditional-branch
disposition, planning alignment, and Step 5.5 Mode R shipment ratification
executed under the operator's dark-factory activation of
`2026-10-29T21:54:35-07:00` (`2026-10-30T04:54:35Z`, persisted in parent SQLite
and `.backlogit/memories.json` key `dark-factory-2026-10-30-0e2b21f0`):

* **Operator instruction**: `"Implement the recommended order: Run the pipeline in dark factory mode."`
* **Bounded current capability**: `056-F` completion only (`phase: stage-first-release-unit`). Later capabilities (`0BD7D83C`, `6187B1EE`, `578B8678`) remain deferred until `056-F` closes sequentially. Adjacent stashes (`906BA4E3`, `358A5E68`), `059-F`, and `060-F` are excluded from this invocation.
* **Approval boundaries**: `merge_approval_pre_authorized = false`, `admin_fallback_pre_authorized = false`, destructive/cascade exceptions = `false`. This Stage record governs only Stage-allowed planning, backlog disposition, review, and queued shipment assembly; it does not grant or transfer PR merge approval or P-015 cascade authority.
* **Visibility**: Copilot CLI (`agent-intercom` not installed).
* **Stop conditions**: P-001, P-009, P-014, P-016, P-017, P-021 violations, scope expansion, unavailable required tool without fallback, unresolved P0/P1 findings, failed required gates, unsafe destructive action, or missing/ambiguous approval.

## Problem Frame

Shipment `052-S` (`056.011-T`, pre-initialize `server/discover` transport
compatibility for H3-A) merged to `main` in PR #138
(`9d5621a19f7706eeca187b56bbb99f8fc424f251`), and its post-merge closure
(`docs/closure/2026-10-29-052-s-h3-a-discover-compat-post-merge-closure.md`,
merged in PR #139 at `db2d012ba10bb5a65b600179b8d5917eeaf4d385`) is `READY`
with `compaction_status: done`. Across the 33 tasks of feature `056-F`
(`056.001-T` through `056.033-T`):

* **16 tasks are `archived` (`archived_status: done`) across four shipped release units**:
  * Phase 1 evidence foundation `049-S` (`98f8fc63024095b0b8697545986646a564677917`): `056.001-T`, `056.002-T`, `056.003-T`, `056.019-T`, `056.020-T`, `056.021-T`, `056.022-T`, `056.023-T`
  * Phase 1.5 standalone-probe CI `054-S` (`2872de3379589c2b5a91a879861bbbb345e9171c`): `056.028-T`
  * Phase 1.6 Rust 1.88 MSRV alignment `053-S` (`99464f7727e7714f5156a3b25a7de2ff484112e6`): `056.029-T`, `056.030-T`, `056.031-T`, `056.032-T`, `056.033-T`
  * Phase 2 selected H3-A remedy `052-S` (`9d5621a19f7706eeca187b56bbb99f8fc424f251`): `056.011-T`
* **1 task is already dispositioned `done` (`selection:not-needed`) in `.backlogit/archive/056.026-T.md`**:
  * `056.026-T` (`Reconcile generated MCP config type/transport discriminator (unconditional)`), ratified by Stage in `docs/decisions/2026-09-13-stage-056.026-T-disposition-not-needed.md` (`F1 = NOT PROVEN`).
* **14 Phase 2 conditional remedy tasks remain in `.backlogit/queue/` with `status: queued` and `selection:pending`**:
  * `056.005-T`, `056.006-T`, `056.007-T`, `056.008-T`, `056.009-T`, `056.010-T`, `056.014-T`, `056.015-T`, `056.016-T`, `056.017-T`, `056.018-T`, `056.024-T`, `056.025-T`, `056.027-T`
* **3 Phase 3 final documentation and acceptance tasks remain in `.backlogit/queue/` with `status: queued` (`labels: ["phase:final"]`)**:
  * `056.012-T` (`Document serve diagnostics and evidence-selected remediation`)
  * `056.013-T` (`Document managed MCP launch and compatibility contracts`)
  * `056.004-T` (`Runtime verification against newest CLI + rollback/observation window`, T4)

Because `056.012-T` depends on every cause-family leaf (`056.006-T`, `056.007-T`,
`056.009-T`, `056.010-T`, `056.011-T`, `056.015-T`), `056.013-T` depends on
`056.012-T` and `056.027-T`, and `056.004-T` (T4) has direct fan-in from all 32
other `056.*-T` tasks, Phase 3 cannot become eligible until Stage executes the
plan's **Final Assembly Protocol**: evaluating each of the 14 remaining
conditional tasks against the authoritative T0 and exact-client evidence,
recording their supported `selected` or `not-needed` dispositions, aligning
stale `1.75` MSRV references on `056-F`'s live planning/task surfaces to the
approved `rust-version = "1.88"` floor, and assembling the next eligible
task-only shipment under Step 5.5 Mode R.

## Option Evaluation

### Option A: Evidence-Gated Phase 2 `not-needed` Disposition, Direct `056-F` MSRV 1.88 Alignment, and Phase 3 Mode R Shipment Assembly (Selected)

* **Description**: Evaluate each of the 14 `selection:pending` tasks strictly against its own documented activation predicate and the completed one-shot T0 (`056.001-T`), H3-B (`056.019-T`), discriminator (`056.026-T`), E1 (`2026-08-29`), and H3-A (`056.011-T`) evidence records. Disposition all 14 unselected tasks to valid terminal `status: done` with `selection:not-needed` and explicit audit comments (`not-needed: <rationale>`). Reconcile stale root-workspace `1.75` declarations in `.backlogit/queue/056-F.md`, `.backlogit/queue/056.004-T.md`, and `docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md` to the operator-approved `rust-version = "1.88"` floor (preserving `tools/mcp-probe` at `1.75`). Assemble the Phase 3 task-only shipment `[056.012-T, 056.013-T, 056.004-T]` under Step 5.5 Mode R for Ship execution.
* **Pros**: Honors the explicit selection gate (`dependency-ready != selected`), avoids overclaiming from treatment success, satisfies the full 32-task T4 fan-in with auditable `done` + `not-needed` records, removes impossible root `1.75` demands from `056.004-T` before Ship claims Phase 3, and preserves P-010/P-015 boundaries.
* **Cons**: Requires careful topological ordering when transitioning the 14 conditional tasks through `active` to `done` so every task's upstream dependencies are already terminal.
* **Effort estimate**: Low-Medium (Stage planning, backlog disposition, plan review, Mode R shipment assembly).
* **Fit**: Exact fit with `056-F` DoD, the implementation plan's Final Assembly Protocol, and P-010/P-015/P-017 constraints.

### Option B: Select and Ship Additional Phase 2 Remedy Branches Without Affirmative Evidence (Rejected)

* **Description**: Flip one or more of the remaining Phase 2 families (`H0a`, `H0b`, `H0c`, `H1`, `discriminator`, or `diagnostic-sink`) to `selection:selected` and assemble a Phase 2 code shipment before Phase 3.
* **Pros**: None supported by evidence.
* **Cons**: Directly violates the plan's selection gate (which forbids selecting a conditional remedy when T0 / exact-CLI evidence did not prove its activation predicate) and repeats the exact error rejected by the four-route adversarial review on `056.026-T` (`F1 = NOT PROVEN`).
* **Effort estimate**: High (unjustified production code churn across multiple subsystems).
* **Fit**: Fails Constitution Principle VI (YAGNI / scope discipline) and the `056-F` evidence-first contract.

### Option C: Treat `052-S` Diagnostic Treatment Runs as Satisfying `056.004-T` (T4) and Close `056-F` Immediately (Rejected)

* **Description**: Mark `056.012-T`, `056.013-T`, and `056.004-T` `done` in Stage based on `052-S`'s two connected `mcp-probe exact-cli` treatment runs.
* **Pros**: None.
* **Cons**: Violates `056.004-T`'s explicit prohibition on using the T0 diagnostic wrapper or temporary probe `.mcp.json` as restored-production evidence; skips the three required restored-production `/mcp show` sessions (including one gate-off run), the `scripts/verify_copilot_mcp_show.ps1` runner, the separate `056.002-T` read-only server-control check, and the required operator documentation updates in `056.012-T` and `056.013-T`; and violates P-010 by performing Ship-owned implementation/verification in Stage.
* **Effort estimate**: Low, but invalid.
* **Fit**: Forbidden by P-010 and `056.004-T` acceptance criteria.

### Trade-Off Comparison

| Criterion | Option A (Selected) | Option B (Rejected) | Option C (Rejected) |
|---|---|---|---|
| Evidence grounding | Strict per-predicate T0 / E1 / `056.019-T` / `056.026-T` verification | Speculative selection without proof | Conflates diagnostic wrapper runs with restored-production T4 acceptance |
| P-010 Role Boundary | Preserved (Stage dispositions unselected branches; Ship executes Phase 3 docs + T4) | Preserved, but dispatches unwarranted code work | Violated (Stage cannot execute docs or runtime verification) |
| T4 fan-in integrity | All 30 prerequisites reach `done` with explicit audit trail | Delays Phase 3 behind unproved branches | Falsifies Phase 3 completion |
| MSRV truthfulness | Aligns `056-F` and `056.004-T` to ratified root `1.88` (probe `1.75`) | Leaves stale `1.75` text or widens scope | Leaves stale `1.75` text |

## Evidence-Based Conditional Branch Evaluation (Anti-Fallacy Grounding)

### Methodological Guardrail: Why `052-S` Treatment Success Alone Does Not Disprove Other Causes

In `052-S` (`docs/decisions/2026-10-29-mcp-serve-discover-compat-exact-client-evidence.md`),
running `mcp-probe exact-cli` against `GitHub Copilot CLI 1.0.105` with the
`DiscoverCompat` `-32601` adapter (`after-056011` and `after2-056011`) produced
`last_mcp_status: "connected"` on the `treatment` leg across two runs. Stage
explicitly rejects two invalid inferences from those runs:

1. **No blanket negative inference from treatment success**: `mcp-probe exact-cli`'s `treatment` leg runs inside the isolated probe workspace (`logs/probe/<nonce>/treatment/.mcp.json`) with `"cwd"` explicitly set to the canonical repository root and the diagnostic `wrapper` interposed as `command`. Moreover, in `after-056011` and `after2-056011`, the wrapper was terminated by client session teardown before writing `evidence.json`, so post-fix frame-level `initialize_correlation` was not persisted on disk. Observing `last_mcp_status: "connected"` on a diagnostic `treatment` leg therefore does **not** by itself prove the universal absence of H0a, H0b, H0c, H1, or discriminator issues across arbitrary environments.
2. **No false-positive H0a inference from `control` failure in `mcp-probe`**: In `tools/mcp-probe/src/exact_cli.rs::run_leg`, the runner spawns `copilot.exe -C <leg_dir>`, where `<leg_dir>` for `control` is `logs/probe/<nonce>/control` — an empty scratch subdirectory created by `056.021-T` so Copilot CLI resolves the isolated `control/.mcp.json` without reading or mutating the repository-root `.mcp.json`. Because `logs/probe/<nonce>/control` contains no `.graphtor` (or `.kbdb`) database directory and `control/.mcp.json` omits `"cwd"`, an inner `serve` process spawned in `control` starts in `logs/probe/<nonce>/control` and exits preflight (`NoDatabasesToServe`). That `control` failure is a structural consequence of `-C logs/probe/<nonce>/control` in the isolated probe harness, **not** evidence that Copilot CLI launches `serve` in a foreign working directory when invoked from the project workspace. Indeed, `exact_cli.rs::classify_pass()` in both `049-S` (`exact-1789250503062413000-35436`) and `052-S` (`before-056011`, `after-056011`, `after2-056011`) never emitted `H0a (cwd-relative database discovery gap) retained`, and in E1 (`docs/decisions/2026-08-29-mcp-serve-discover-preinitialize-evidence.md`) the live client launch in the workspace completed preflight and database discovery (`starting MCP STDIO server`) without any `"cwd"` field in `.mcp.json`.

Accordingly, each conditional branch below is dispositioned strictly by testing
its own **affirmative activation predicate** against the authoritative evidence
records: under the `056-F` selection gate, a conditional remedy task transitions
to `selection:selected` **only** when controlled T0 / exact-client evidence
affirmatively proves its predicate; when the completed one-shot evidence does
not prove that predicate, the task's own acceptance criterion mandates moving it
to `status: done` with `selection:not-needed` and a `not-needed: <rationale>`
audit comment.

### Per-Family and Per-Task Disposition Table

| Task ID | Cause family label | Activation predicate (from task AC) | Authoritative evidence & evaluation | Ratified disposition |
|---|---|---|---|---|
| `056.006-T` | `cause:diagnostic-sink` | Select **only** when T0 proves child stderr unavailable **AND** env inheritance is proven; otherwise move to `done` with `not-needed: production sink not required or env inheritance not proven`. | In `049-S` T0 (`056.001-T`, commit `0bd8c92`), `sentinel_observation.observed = true` proved env inheritance, satisfying only the second conjunctive condition. The first condition ("T0 proves child stderr unavailable") is **not proven**: T0 did not show stderr unavailable, and `docs/decisions/2026-08-29-mcp-serve-discover-preinitialize-evidence.md` (E1) is directly captured live actual-client stderr (`starting MCP STDIO server` + rmcp `ExpectedInitializeRequest`). | `status: done`, `labels: ["phase:remedy","cause:diagnostic-sink","selection:not-needed"]`, comment: `not-needed: production sink not required or env inheritance not proven` |
| `056.010-T` | `cause:h0c-state-repair` | If T0 does not classify H0c, move to `done` with `not-needed: H0c not evidenced`. | `049-S` T0 (`056.001-T`, commit `0bd8c92`, `logs/probe/exact-1789250503062413000-35436/evidence.json`) emitted `unresolved` (`server/discover` captured at `id: 0` after preflight) and did **not** classify H0c (malformed `sources.yaml`, missing explicit `--config`, `PreV4Schema`, `DuplicateIntakeConflict`, or DB open failure). E1 (`2026-08-29`) likewise completed preflight and logged `starting MCP STDIO server`. | `status: done`, `labels: ["phase:remedy","cause:h0c-state-repair","selection:not-needed"]`, comment: `not-needed: H0c not evidenced` |
| `056.016-T` | `cause:lock-recovery` | If H0b is not evidenced by T0, move to `done` with `not-needed: H0b not evidenced`. | Neither `049-S` T0 (`056.001-T`, commit `0bd8c92`) nor E1 (`2026-08-29`) evidenced `DatabaseLocked` or stale-lock PID reuse on a Generation target; in both records, database open succeeded and execution entered `serve_server`. | `status: done`, `labels: ["phase:remedy","cause:lock-recovery","selection:not-needed"]`, comment: `not-needed: H0b not evidenced` |
| `056.007-T` | `cause:lock-recovery` | If H0b is not evidenced by T0, move to `done` with `not-needed: H0b not evidenced`; H0b requires a Generation target. | Same as `056.016-T`: H0b (`DatabaseLocked` / stale-lock PID reuse on a Generation target) was not evidenced by `049-S` T0 (`056.001-T`) or E1 (`2026-08-29`), and prerequisite `056.016-T` closes `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:lock-recovery","selection:not-needed"]`, comment: `not-needed: H0b not evidenced` |
| `056.014-T` | `cause:h1-model-lifecycle` | If H1 is not evidenced by T0, move to `done` with `not-needed: H1 not evidenced`. | In `049-S` T0 (`056.001-T`, commit `0bd8c92`) and `052-S` (`before-056011`), `timed_out: false` on all legs (no initialize timeout while child alive during eager model load), and E1 (`2026-08-29`) explicitly confirmed that `resolve_embedding_model` completed before `starting MCP STDIO server` was logged (`"The failure is not a pre-serve early exit (H0-family) and not an embedding-model lifecycle stall (H1)"`). | `status: done`, `labels: ["phase:remedy","cause:h1-model-lifecycle","selection:not-needed"]`, comment: `not-needed: H1 not evidenced` |
| `056.005-T` | `cause:h1-model-lifecycle` | If H1 is not evidenced by T0, move to `done` with `not-needed: H1 not evidenced`. | Same as `056.014-T`: H1 is not evidenced by T0 (`056.001-T`) or E1 (`2026-08-29`), and prerequisite `056.014-T` closes `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:h1-model-lifecycle","selection:not-needed"]`, comment: `not-needed: H1 not evidenced` |
| `056.025-T` | `cause:h1-model-lifecycle` | If H1 is not evidenced by T0, move to `done` with `not-needed: H1 not evidenced`. | Same as `056.014-T`/`056.005-T`: H1 is not evidenced by T0 (`056.001-T`) or E1 (`2026-08-29`), and prerequisite `056.005-T` closes `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:h1-model-lifecycle","selection:not-needed"]`, comment: `not-needed: H1 not evidenced` |
| `056.015-T` | `cause:h1-model-lifecycle` | If H1 is not evidenced by T0, move to `done` with `not-needed: H1 not evidenced`. | Same as `056.014-T`/`056.005-T`/`056.025-T`: H1 is not evidenced by T0 (`056.001-T`) or E1 (`2026-08-29`), and prerequisite `056.025-T` closes `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:h1-model-lifecycle","selection:not-needed"]`, comment: `not-needed: H1 not evidenced` |
| `056.017-T` | `cause:managed-config` | Run for an evidenced H0a prerequisite, an H3-B1 mechanism, OR a selected discriminator existing-install delivery (`056.027-T`); otherwise move to `done` with `not-needed: managed config mutation not selected`. | None of the three triggers is evidenced/selected: (1) `049-S` T0 (`056.001-T`, commit `0bd8c92`) emitted `unresolved` (both legs reached STDIO transport and captured `server/discover` `id: 0`) rather than `H0a-retained`, and E1 (`2026-08-29`) reached `starting MCP STDIO server` past `cwd`-relative database discovery without a `"cwd"` field in `.mcp.json`; (2) `056.019-T` (sole H3-B adjudicator, commit `2b187dc`) closed `done` with `not-needed: H3-B / isolated-config mechanism not evidenced` (`Gate 1 passed`, `h3_b_candidate: false`), so H3-B1 is not selected; (3) `056.026-T` closed `done`/`selection:not-needed` (`docs/decisions/2026-09-13-stage-056.026-T-disposition-not-needed.md`), so discriminator delivery `056.027-T` is not selected. | `status: done`, `labels: ["phase:remedy","cause:managed-config","selection:not-needed"]`, comment: `not-needed: managed config mutation not selected` |
| `056.024-T` | `cause:managed-config` | If T0/`056.019-T` evidence did NOT select any managed-config recovery/existing-install mutation (no H0a, no H3-B1, AND no selected `056.027-T`), move to `done` with `not-needed: managed config mutation/recovery not selected`. | Same three-trigger evaluation as `056.017-T`: no H0a prerequisite, no H3-B1 mechanism (`056.019-T` `done`/`not-needed`), and no selected discriminator delivery (`056.026-T` `done`/`not-needed`), with prerequisite `056.017-T` closing `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:managed-config","selection:not-needed"]`, comment: `not-needed: managed config mutation/recovery not selected` |
| `056.018-T` | `cause:managed-config` | Run for an evidenced H0a prerequisite, an H3-B1 mechanism, OR a selected discriminator existing-install delivery (`056.027-T`); otherwise move to `done` with `not-needed: managed config recovery not selected`. | Same three-trigger evaluation as `056.017-T`/`056.024-T`, with prerequisite `056.024-T` closing `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:managed-config","selection:not-needed"]`, comment: `not-needed: managed config recovery not selected` |
| `056.008-T` | `cause:managed-config` | Run only for an evidenced H0a prerequisite or H3-B1; otherwise move to `done` with `not-needed: managed cwd generation not selected`. | Neither H0a (`056.001-T` T0 did not emit `H0a-retained`; E1 reached `starting MCP STDIO server` without `"cwd"`) nor H3-B1 (`056.019-T` closed `done`/`not-needed`) is evidenced/selected, and prerequisite `056.017-T` closes `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:managed-config","selection:not-needed"]`, comment: `not-needed: managed cwd generation not selected` |
| `056.009-T` | `cause:managed-config` | Run only when `056.008-T` is selected; otherwise move to `done` with `not-needed: 056.008-T not selected`. | `056.008-T` and `056.018-T` both close `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:managed-config","selection:not-needed"]`, comment: `not-needed: 056.008-T not selected` |
| `056.027-T` | `cause:discriminator` | Run only when `056.026-T` is selected (a `type`/`transport` mismatch is evidenced) and existing installs need the reconciled discriminator; otherwise move to `done` with `not-needed: discriminator existing-install delivery not selected`. | `056.026-T` is already `status: done` with `selection:not-needed` (`docs/decisions/2026-09-13-stage-056.026-T-disposition-not-needed.md`, Section F1 and Section R3), and `056.018-T` closes `done`/`selection:not-needed`. | `status: done`, `labels: ["phase:remedy","cause:discriminator","selection:not-needed"]`, comment: `not-needed: discriminator existing-install delivery not selected` |

## Bounded `056-F` Planning Alignment for Ratified Root MSRV 1.88

In `053-S` (`docs/decisions/2026-10-29-rust-1-75-rmcp-dependency-compatibility-decision.md`,
merged in PR #136 at `99464f7727e7714f5156a3b25a7de2ff484112e6`), the operator
approved Option 1: a constitutional MSRV amendment raising the root workspace
`rust-version` from `"1.75"` to `"1.88"` (preserving `edition = "2021"`), while
the standalone diagnostic crate `tools/mcp-probe` retains its own separate
`Cargo.toml`/`Cargo.lock` at `rust-version = "1.75"`.

While `056.011-T` and `056.029-T`..`056.033-T` were updated in commit `e5cd0ad`,
three live `056-F` planning surfaces still contain stale root-workspace `1.75`
prose that would demand impossible root `1.75` evidence during Phase 3 (`056.004-T`):

1. **`.backlogit/queue/056.004-T.md`**:
   * Acceptance criteria bullet 3 still states that `056.029-T` must resolve the dependency graph at `"unchanged Rust 2021 / rust-version 1.75"`.
   * Implementation notes still state `"All validation remains at Rust/Cargo 1.75; no dynamically raised floor is valid evidence."`
2. **`.backlogit/queue/056-F.md`**:
   * `dod` bullets 6 and 11 and `description` still describe `056.029-T` and feature Cargo/CI gates as remaining at `rust-version 1.75`.
3. **`docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md`**:
   * Live sections outside the top amendment header (Goal/DoD root quality gates line 137, Likely Surfaces H3-A row line 176, `T-H3-A` line 1042, Issue and Dependency Graph PHASE 2/3 lines 1560 and 1588, Verification Commands step 4 line 1735, and Plan Hardening H3-A ProposedAction lines 2165/2174) still refer to root/H3-A `1.75` compatibility evidence, and the plan does not yet record the post-`052-S` Phase 2 branch disposition and Phase 3 Mode R shipment assembly.

**P-021 C1 Same-Contract-Surface Scope Boundary**: Reconciling those three
`056-F`-owned planning/backlog artifacts so `056.004-T` (T4) validates against
the ratified root `rust-version = "1.88"` (`edition = "2021"`) floor while
preserving `tools/mcp-probe` at `1.75` is directly required to complete `056-F`
without contradictory acceptance criteria. Conversely, harvesting or executing
stash `906BA4E3` or `358A5E68` (or editing non-plan files such as
`docs/developer-guide.md`, `.autoharness/harness-manifest.yaml`,
`.autoharness/workspace-profile.yaml`,
`.github/instructions/rust-mcp-server.instructions.md`, or
`.github/agents/subagents/rust-mcp-expert.agent.md`) lies outside this bounded
`056-F` Stage activation and is deliberately not performed.

## Step 5.5 Mode R Authorization for Phase 3 Shipment Assembly (`055-S`)

This section is the **durable, path-citable Step 5.5 Mode R authorization**
required by `.github/agents/_stage.agent.md` (Step 5.5, item 1, *Mode R —
ratified existing-scope handoff*) for assembling the final Phase 3 task-only
release unit of feature `056-F`.

### 1. Input Mode and Covering Feature

* **Mode**: Step 5.5 Mode R (ratified existing-scope handoff). All 33 tasks of `056-F` were harvested in earlier sessions; no new task is harvested and no synthetic Mode H harvest is manufactured.
* **Covering feature**: `056-F` — *Fix MCP serve initialize-handshake regression (Copilot CLI OS error 232)*.
* **P-015 Protected Set**: Covering feature `056-F` (`status: active`) is **excluded** from `member_ids` and `assembly_ids`. Per `056-F` DoD bullet 1 (`"This feature is delivered in phased, task-only release units. The protected covering feature 056-F is never a shipment member while work remains"`) and P-015, Phase 3 is assembled as a task-only manifest (`[056.012-T, 056.013-T, 056.004-T]`).

### 2. Authorized `member_ids` (3 Live Queued Tasks, in Dependency Order)

The exact ordered list of items intended for shipment — which becomes
`assembly_ids` and the atomic `backlogit shipment create --items` argument — is:

```text
056.012-T,056.013-T,056.004-T
```

| Order | Task ID | Title | Width / Role | In-Manifest Dependencies |
|---|---|---|---|---|
| 1 | `056.012-T` | Document serve diagnostics and evidence-selected remediation | Docs (`docs/troubleshooting.md`, `docs/mcp-tools.md`) | None (all 6 dependencies are satisfied prerequisites in `prerequisite_ids`) |
| 2 | `056.013-T` | Document managed MCP launch and compatibility contracts | Docs (`docs/mcp-tools.md`, `docs/cli-reference/graphtor-docs.md`, verify `README.md`) | `056.012-T` (plus `056.027-T` in `prerequisite_ids`) |
| 3 | `056.004-T` | Runtime verification against newest CLI + rollback/observation window | Runtime verification + `scripts/verify_copilot_mcp_show.ps1` (T4) | `056.012-T`, `056.013-T` (plus all 30 tasks in `prerequisite_ids`) |

### 3. Authorized `prerequisite_ids` (30 Satisfied Tasks, Disjoint from `member_ids`)

Every dependency that `056.012-T`, `056.013-T`, or `056.004-T` has on an item
outside `member_ids` is named in `prerequisite_ids` below (30 tasks total). None
of these 30 tasks is ever added to the shipment manifest, and all 30 are
`done`/`archived` once the 14 Phase 2 conditional tasks above complete their
Stage-ratified `done` + `selection:not-needed` transitions:

* **Shipped and archived in `049-S` (8 tasks, `archived_status: done`, commit `98f8fc63024095b0b8697545986646a564677917`)**:
  `056.001-T`, `056.002-T`, `056.003-T`, `056.019-T`, `056.020-T`, `056.021-T`, `056.022-T`, `056.023-T`
* **Shipped and archived in `054-S` (1 task, `archived_status: done`, commit `2872de3379589c2b5a91a879861bbbb345e9171c`)**:
  `056.028-T`
* **Shipped and archived in `053-S` (5 tasks, `archived_status: done`, commit `99464f7727e7714f5156a3b25a7de2ff484112e6`)**:
  `056.029-T`, `056.030-T`, `056.031-T`, `056.032-T`, `056.033-T`
* **Shipped and archived in `052-S` (1 task, `archived_status: done`, commit `9d5621a19f7706eeca187b56bbb99f8fc424f251`)**:
  `056.011-T`
* **Prior Stage-dispositioned `done` / `selection:not-needed` in `.backlogit/archive/` (1 task, commit `6b7fad3` / `86c2b0a`)**:
  `056.026-T`
* **Current Stage-dispositioned `done` / `selection:not-needed` in `.backlogit/archive/` (14 tasks, ratified by this decision)**:
  `056.005-T`, `056.006-T`, `056.007-T`, `056.008-T`, `056.009-T`, `056.010-T`, `056.014-T`, `056.015-T`, `056.016-T`, `056.017-T`, `056.018-T`, `056.024-T`, `056.025-T`, `056.027-T`

### 4. `handoff_ids` (Auditable Union Only — 33 Tasks)

`handoff_ids` is the disjoint union of `member_ids` (3 tasks) and
`prerequisite_ids` (30 tasks) = all 33 tasks `056.001-T` through `056.033-T`.
`handoff_ids` is a citation and audit convenience only and is never equated to
`assembly_ids`. `member_ids` and `prerequisite_ids` have zero intersection.

### 5. Shipment Sequencing Edges

Upon atomic creation of the Phase 3 shipment (`055-S`, allocated by
backlogit), Stage records `blocks` dependency edges from `055-S` to the four
completed predecessor shipments of `056-F` (`049-S`, `054-S`, `053-S`, `052-S`),
all four of which are already `status: archived` / `archived_status: shipped`.

### 6. Handoff-Integrity Verification: Prior Tool Allocation of `055-S` and Operator Decision Gate

Before staging publication, Stage verified bounded authoritative history for
shipment ID `055-S` across `.backlogit/checkpoints/`,
`archive/stage-054-055-local-2026-09-13`, `.backlogit/logs/055-S.jsonl`, and
SQLite `item_log_entries`:

1. **Concrete Evidence of Prior Tool Allocation (`055-S` Was Previously Issued)**:
   * On `2026-09-13T12:07:00.7952609-07:00` (`2026-09-13T19:07:00Z`), `055-S` **was actually allocated and created through `backlogit`** (not merely an unissued tentative label) for `[056.026-T]` with title `"MCP managed-config discriminator reconciliation - 056.026-T (056-F)"`.
   * **Git commit evidence**: `archive/stage-054-055-local-2026-09-13` commit `9a35d490ddf7114be2d99e93e514e6e248625c3c` created `.backlogit/queue/055-S.md` and appended `hooks_queue.jsonl` `seq: 1187` (`create_artifact`, `item_id: "055-S"`) and `seq: 1188` (`update_artifact`, `item_id: "055-S"`).
   * **Checkpoint evidence**: `.backlogit/checkpoints/checkpoint-20260913-195428.json` and `.backlogit/checkpoints/checkpoint-20260913-231222.json` both record `withdrawn_shipment: "055-S"` (bound to `056.026-T`, withdrawn when PR #122 re-based onto `origin/main` at `7e538e5`).
   * **Append-only item log evidence**: `.backlogit/logs/055-S.jsonl` (and SQLite `item_log_entries` for `item_id = '055-S'`) contains the historical `2026-09-13T12:07:00.7952609-07:00` `shipment_created` event (`items: ["056.026-T"]`) followed by the `2026-10-29T22:40:31.8651423-07:00` `shipment_created` event (`items: ["056.012-T", "056.013-T", "056.004-T"]`).
   * **Why `backlogit shipment create` re-issued `055-S`**: `backlogit`'s `NextTypedHierarchicalID` allocator computes the next shipment ID as `max(existing shipment IDs in .backlogit/queue/ and .backlogit/archive/) + 1`. Because PR #122 (`857165cf`) withdrew the 2026-09-13 `055-S` by branching from `origin/main` where `055-S.md` never existed, and subsequent PR #124/#125 minted `054-S`, the highest shipment file on `origin/main` was `054-S`. Calling `backlogit shipment create` therefore re-minted `055-S`.
   * **Never-issued candidate verification**: `056-S` has **zero** prior occurrences in `.backlogit/logs/`, `item_log_entries`, `.backlogit/queue/`, `.backlogit/archive/`, `.backlogit/checkpoints/`, or any git branch (`git log --all --grep="056-S"` is empty).

2. **Supported Non-Destructive Correction vs. Role-Boundary / Approval Stop Gate**:
   * Because `backlogit shipment create` accepts no `--id` flag, allocating `056-S` requires creating a new shipment while `055-S.md` is present (so the counter advances to `056-S`) and retiring `055-S` so two `queued` shipments do not simultaneously hold `["056.012-T", "056.013-T", "056.004-T"]` in `.backlogit/queue/` (which Step 5.5 items 2 and 3a(c) forbid).
   * Installed `backlogit 1.12.0` provides a dedicated Stage-only non-destructive retirement command:
     `backlogit shipment dispose 055-S --reason "<reason>" --by stage --authorization-ref <DL-ID> --superseded-by 056-S --confirm`
     (MCP `backlogit_dispose_shipment`), which transitions a `queued` shipment to `abandoned` under a decided deliberation without deleting files, rewriting git/hook history, or fabricating a Ship claim/ship transition.
   * **Why Stage halts for explicit operator decision rather than executing `backlogit shipment dispose` unilaterally**:
     1. **Mandatory in-session operator approval**: `backlogit shipment dispose --help` states verbatim: *"It needs a decided deliberation that names this shipment in its authorizes_disposition field, and in-session operator approval before the call."* All current dark-factory approval flags are `false`.
     2. **P-010 fail-closed Mutation Classification gate**: `backlogit_dispose_shipment` (`backlogit shipment dispose`) is not yet listed in `.github/agents/_stage.agent.md`'s `### Mutation Classification (P-010 fail-closed)` table (nor in `.autoharness/backlog-registry.yaml`). Under `.github/instructions/role-enforcement.instructions.md` (`"If the operation is a state mutation but does NOT appear in either the Allowed or Forbidden column -> treat as forbidden"`), Stage must halt and request operator authorization/classification before invoking it.

3. **Required Operator Decision Before Publication**:
   * **Option 1 (Strict Fresh Never-Issued ID `056-S` via Governed Stage Dispose)**: Operator grants in-session approval and P-010 authorization for Stage to (a) create decided deliberation `005-DL` with `authorizes_disposition: ["055-S"]`, (b) create shipment `056-S` (`--items "056.012-T,056.013-T,056.004-T"` + `blocks` edges to `049-S`, `054-S`, `053-S`, `052-S`), and (c) run `backlogit shipment dispose 055-S --reason "055-S had a prior local tool allocation on 2026-09-13 (commit 9a35d49); superseded by fresh never-issued 056-S" --by stage --authorization-ref 005-DL --superseded-by 056-S --confirm`.
   * **Option 2 (Accept `055-S` as Canonical on `origin/main`)**: Operator waives the "never-issued" constraint for `055-S` on the ground that the 2026-09-13 `055-S` (`9a35d49`) was never published to `origin/main` and was formally withdrawn in PR #122 (`857165cf`), allowing `055-S` (`c5992c25a92d72e01a6578f92b1d8fd50b576636` + this handoff-integrity commit) to proceed directly to staging publication.

