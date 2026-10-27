---
description: "Autoharness tuning report for kbdb (formerly graphtor-docs) upgrading harness contracts and templates from 1.5.0 to 1.6.0"
tuned_at: "2026-10-26T17:29:00Z"
autoharness_version_from: "1.5.0"
autoharness_version_to: "1.6.0"
---

# Harness Tuning Report — 2026-10-26

## Drift Summary

* Breaking changes: 22 (17 managed skill frontmatter `FM_MISSING_REQUIRED name` findings, 5 failing targeted pipeline/policy/registry checks)
* Degrading changes: 26 (3 schema-contract upgrades, 17 managed subagent `refresh-route-frontmatter` updates, 4 advisory workspace-authored frontmatter proposals on `rust-mcp-expert.agent.md`, 2 `graphtor-docs` path updates for `.kbdb` / `kbdb`)
* Growth opportunities: 1 (`P-DYN-001` Windows hygiene policy proposal mined from 7 cross-cutting compound learnings)
* Cosmetic adjustments: 6 (`ROUTE_VARIABLE_STALE` manifest variable synchronization, 2 portability path normalizations)

## Composition

* Installed primary stack pack: `mcp-server`
* Current primary stack pack: `mcp-server`
* Installed stack packs: `mcp-server, cli-tool`
* Current stack packs: `mcp-server, cli-tool`
* Installed layers: `foundation, instructions, workflow, review, backlog, knowledge, overlays`
* Recommended layers: `foundation, instructions, workflow, review, backlog, knowledge, overlays`
* Enabled capability packs: `agent-engram, backlogit, adversarial-review, graphtor-docs`

## Checksum Scan

* Checked installed artifacts: 108
* Missing installed artifacts: 0
* User-modified artifacts (pre-tune): 20 (reconciled and preserved; post-tune: 0 divergent, 108 `unchanged`)
* Ignored artifacts: 0
* Startup-script contracts (`start.ps1`, `start.sh`): `current` (`v1.1.0`)

## Learning Signals

* Compound patterns detected: 3
  * `component_hotspot`: `src/pipeline/mod.rs` (4 entries)
  * `cross_cutting_tags`: `mcp` (3 entries across `best-practices`, `runtime-errors`, `workflow-issues`)
  * `cross_cutting_tags`: `windows` (7 entries across `best-practices`, `runtime-errors`, `workflow-issues`)
* Promotion-ready instincts: 0
* Recurring closure findings: 0
* Policy-gap candidates detected: 1 (`P-DYN-001` for cross-cutting `windows` tag across 7 compound entries)
* Learning-driven proposals generated: 1 (`.autoharness/policy-proposals/P-DYN-001.md`)

## Proposed and Applied Changes (Ordered by Priority)

### P0 — Breaking (Applied)

1. **[TUNE-001] Frontmatter conformity (`source: frontmatter-conformity`) — 17 managed skills missing required `name` key (`FM_MISSING_REQUIRED`)**
   * **Artifacts**: `.github/skills/{build-feature,compact-context,compound-refresh,compound,deliberate,evolve,file-lock,fix-ci,impl-plan,learn,observe,operational-closure,plan-harden,runtime-verification,safety-modes,skill-search,spike}/SKILL.md`
   * **Action**: Re-rendered the 16 `unchanged` managed skills from `autoharness 1.6.0` templates (preserving `# Operational Closure` and `# Runtime Verification` H1 headings for P-008/MD041 compliance) and applied `add-key` (`name: compound`) to `.github/skills/compound/SKILL.md` while preserving its body.
2. **[TUNE-002] Pipeline-topology pre-claim gate wiring and claim ordering (`source: structural-drift`)**
   * **Artifact**: `.github/agents/_ship.agent.md`
   * **Issue**: `pipeline_topology_gate_ship_agent_wiring` and `pipeline_topology_gate_ship_agent_claim_ordering` failed because `TOPOLOGY_GATE: pre_claim (before branch/worktree creation)` / `Bootstrap exemption` were absent before `BRANCH_CREATED` and a table cell in `Mutation Classification` mentioned `backlogit_claim_shipment` ahead of Step 0.5.
   * **Action**: Added the `TOPOLOGY_GATE: pre_claim (before branch/worktree creation)` bullet with its bootstrap exemption in Step 0.5 step 3a and normalized the pre-Step-0.5 table cell to `` `claim_shipment` (`backlogit shipment claim`) `` while preserving all workspace-specific P-010/P-015/P-021 rules.
3. **[TUNE-003] Operational closure source-artifact cleanup handoff (`source: structural-drift`)**
   * **Artifact**: `.github/skills/operational-closure/SKILL.md`
   * **Issue**: `closure_source_artifact_cleanup` failed (`missing: ["Source artifact cleanup", "source_stash_id", "source_deliberation_id"]`).
   * **Action**: Added the `Source artifact cleanup` checklist item using the workspace's Stage-owned retirement handoff contract (covering both singular `source_stash_id` / `source_deliberation_id` and plural `source_stash_ids` / `source_deliberation_ids` per `_ship.agent.md` Step 7 and P-010/P-021 C5) while retaining the compatible closure output contract.
4. **[TUNE-004] Dark Factory Visibility Protocol (`source: structural-drift`)**
   * **Artifact**: `.github/policies/workflow-policies.md`
   * **Issue**: `dark_factory_visibility_contract` failed (`missing: ["Dark Factory Visibility Protocol"]`).
   * **Action**: Added the P-017 `Dark Factory Visibility Protocol` table and `Degraded visibility` rules from `workflow-policies.md.tmpl` (`1.6.0`) while preserving workspace P-015 and P-021 customizations.
5. **[TUNE-005] Orchestrator invocation `context_tier` windows, H7 propagation window, and portability (`source: structural-drift`)**
   * **Artifact**: `.github/agents/_orchestrator.agent.md`
   * **Issue**: `orchestrator_invocation_routing_directive` and `reload_propagation_directive` failed due to missing `context_tier` / `ROUTING_DEGRADED: context_tier` directives at Stage/Ship invocation sites and missing `no independent model binding` in the H7 window; portability scan flagged `~/.autoharness/` on line 477.
   * **Action**: Updated Stage and Ship invocation steps with CLI-first `autoharness routing resolve` and `context_tier` / `ROUTING_DEGRADED: context_tier` handling, tightened the H7 bullet so `no independent model binding` and `ROUTING_DEGRADED` sit within the 600-character verification window, and replaced `~/.autoharness/` with `$HOME/.autoharness/`.
6. **[TUNE-006] Stage escalation route and post-threshold negation guard (`source: structural-drift`)**
   * **Artifacts**: `.autoharness/config.yaml`, `.github/agents/_stage.agent.md`, `.github/instructions/escalation-protocol.instructions.md`
   * **Issue**: `escalation_route_resolution` failed with `ESCALATION_DEGRADED` because `stage` (`gemini-4-argon` / `google` / `high`) had no nested `stage.escalation` override and fell back to an identical `tier3` tuple; `escalation_directive_present` flagged `or authorizes another execution attempt` in `_stage.agent.md`.
   * **Action**: Configured `model_routing.stage.escalation` (`gpt-6.1-sol` / `openai` / `high` / `long_context`), updated `_stage.agent.md` and `escalation-protocol.instructions.md` escalation prose, and phrased item 5 as `and never authorizes another execution attempt`.
7. **[TUNE-007] Backlogit registry hook CLI surfaces (`source: structural-drift`)**
   * **Artifact**: `.autoharness/backlog-registry.yaml`
   * **Issue**: `backlog_registry_cli_surface` failed because `poll_hook_events` and `ack_hook_events` omitted `cli_command`.
   * **Action**: Synced `cli_command` definitions for `poll_hook_events`, `ack_hook_events`, `append_comment`, `save_memory`, and `add_to_shipment` from `autoharness 1.6.0`'s `backlogit.registry.yaml`.

### P1 — Degrading (Applied)

1. **[TUNE-008] Schema-contract upgrades (`source: schema-contract`)**
   * **`upgrade-manifest-contract-1.0.0-to-1.1.0`**: Upgraded `.autoharness/harness-manifest.yaml` `schema_version` from `1.0.0` to `1.1.0` and `autoharness_version` from `1.5.0` to `1.6.0`.
   * **`upgrade-profile-contract-1.0.0-to-1.1.0`**: Upgraded `.autoharness/workspace-profile.yaml` `schema_version` from `1.0.0` to `1.1.0`, updated `workspace_path` to `C:\Source\GitHub\kbdb`, updated `frameworks.list` (`cozo`, `sqlite`, `pulldown-cmark`, `schemars`, `indicatif`), and added `runtime_surfaces.cli: true`, `runtime_validation.validation_expectations`, and `runtime_validation.releasability` (resolving `runtime_validation_profile_contract`).
   * **`upgrade-config-contract-1.1.0-to-1.2.0` (advanced to `1.3.0`)**: Upgraded `.autoharness/config.yaml` `schema_version` from `1.1.0` to `1.3.0` (current `harness-config.schema.json` contract) and added `graphtor_docs` path settings (`.graphtor/config/sources.yaml`, `target/release/graphtor-docs`).
2. **[TUNE-009] Subagent model-routing frontmatter refresh (`source: route-drift`) — 17 managed subagents**
   * **Artifacts**: `.github/agents/subagents/{adversarial-review,agent-native-parity-reviewer,architecture-strategist,concurrency-reviewer,constitution-reviewer,correctness-reviewer,language-engineer,learnings-researcher,maintainability-reviewer,prompt-builder,schema-cli-docs-coupling-reviewer,scope-boundary-auditor,security-lens-reviewer,security-reviewer,security-sentinel,technology-reviewer,template-integrity-reviewer}.agent.md`
   * **Action**: Applied `refresh-route-frontmatter` across all 17 managed subagents (Tier 1 → `claude-haiku-5.5` / `anthropic` / `xhigh` / `long_context`; Tier 2 → `claude-sonnet-5.5` / `anthropic` / `high` / `long_context`; Tier 3 → `gemini-4-argon` / `google` / `high` / `long_context`; Anchor review → `gpt-6.1-sol` / `openai` / `high`) and removed deprecated `model_routing:` keys from `language-engineer.agent.md` and `prompt-builder.agent.md`. Also updated `_orchestrator.agent.md`, `_stage.agent.md`, `_ship.agent.md`, and `adversarial-review.instructions.md` to match.
3. **[TUNE-010] `graphtor-docs` overlay path synchronization for `kbdb` (`source: structural-drift`)**
   * **Artifact**: `.github/instructions/graphtor-docs.instructions.md`
   * **Action**: Updated `{{GRAPHTOR_SOURCES_PATH}}` to `.graphtor/config/sources.yaml` and `{{GRAPHTOR_BINARY_PATH}}` to `target/release/graphtor-docs` to match `.autoharness/workspace-profile.yaml` and `.autoharness/config.yaml`.

### P1 — Degrading (Deferred for Manual Operator Review)

The following 4 `frontmatter-conformity` proposals target the workspace-authored agent `.github/agents/subagents/rust-mcp-expert.agent.md` (`status: nonconformant-workspace`, `manual_review: true`, `value: null`). Per `tune-harness` Step 1.5c rule 3 (INV-B1), workspace-authored agents with `value: null` are preserved untouched and surfaced with their complete payload for operator decision:

```yaml
- contract: frontmatter-conformity
  path: .github/agents/subagents/rust-mcp-expert.agent.md
  from_version: null
  to_version: fc-1
  status: nonconformant-workspace
  severity: P2
  changed_fields: [max_subagent_tier]
  action: add-key
  from_key: max_subagent_tier
  to_keys: [max_subagent_tier]
  value: null
  manual_review: true
  code: FM_MISSING_REQUIRED
  summary: ".github/agents/subagents/rust-mcp-expert.agent.md: add-key max_subagent_tier -> [max_subagent_tier] [manual review]"
  evidence:
    codes: [FM_MISSING_REQUIRED]
    file_codes: [FM_MISSING_REQUIRED]
    citation: "P-013.4/P-013.5: tier-routed agents declare max_subagent_tier, subagent_depth and the model_family/model_provider/reasoning_effort route; no bare model"
    finding: "missing required key 'max_subagent_tier'"
- contract: frontmatter-conformity
  path: .github/agents/subagents/rust-mcp-expert.agent.md
  from_version: null
  to_version: fc-1
  status: nonconformant-workspace
  severity: P2
  changed_fields: [model_family]
  action: add-key
  from_key: model_family
  to_keys: [model_family]
  value: null
  manual_review: true
  code: FM_MISSING_REQUIRED
  summary: ".github/agents/subagents/rust-mcp-expert.agent.md: add-key model_family -> [model_family] [manual review]"
  evidence:
    codes: [FM_MISSING_REQUIRED]
    file_codes: [FM_MISSING_REQUIRED]
    citation: "P-013.4/P-013.5: tier-routed agents declare max_subagent_tier, subagent_depth and the model_family/model_provider/reasoning_effort route; no bare model"
    finding: "missing required key 'model_family'"
- contract: frontmatter-conformity
  path: .github/agents/subagents/rust-mcp-expert.agent.md
  from_version: null
  to_version: fc-1
  status: nonconformant-workspace
  severity: P2
  changed_fields: [model_provider]
  action: add-key
  from_key: model_provider
  to_keys: [model_provider]
  value: null
  manual_review: true
  code: FM_MISSING_REQUIRED
  summary: ".github/agents/subagents/rust-mcp-expert.agent.md: add-key model_provider -> [model_provider] [manual review]"
  evidence:
    codes: [FM_MISSING_REQUIRED]
    file_codes: [FM_MISSING_REQUIRED]
    citation: "P-013.4/P-013.5: tier-routed agents declare max_subagent_tier, subagent_depth and the model_family/model_provider/reasoning_effort route; no bare model"
    finding: "missing required key 'model_provider'"
- contract: frontmatter-conformity
  path: .github/agents/subagents/rust-mcp-expert.agent.md
  from_version: null
  to_version: fc-1
  status: nonconformant-workspace
  severity: P2
  changed_fields: [reasoning_effort]
  action: add-key
  from_key: reasoning_effort
  to_keys: [reasoning_effort]
  value: null
  manual_review: true
  code: FM_MISSING_REQUIRED
  summary: ".github/agents/subagents/rust-mcp-expert.agent.md: add-key reasoning_effort -> [reasoning_effort] [manual review]"
  evidence:
    codes: [FM_MISSING_REQUIRED]
    file_codes: [FM_MISSING_REQUIRED]
    citation: "P-013.4/P-013.5: tier-routed agents declare max_subagent_tier, subagent_depth and the model_family/model_provider/reasoning_effort route; no bare model"
    finding: "missing required key 'reasoning_effort'"
```

### P2 — Growth (Generated for Operator Review)

1. **[TUNE-011] Dynamic policy proposal `P-DYN-001` (`source: learning-driven`)**
   * **Artifact**: `.autoharness/policy-proposals/P-DYN-001.md`
   * **Issue**: Compound library contains 7 entries tagged `windows` across `best-practices`, `runtime-errors`, and `workflow-issues` (reparse-point containment, UTF-8 without BOM subprocess/file I/O, binary test fixtures, and stale file/process locks).
   * **Proposal**: Drafted workspace-specific policy proposal `P-DYN-001` ("Windows Reparse-Point, Encoding, and File-Handle Hygiene Gate") in `.autoharness/policy-proposals/P-DYN-001.md` for operator review.

## Recommendation & Branch Safety

* **Deterministic verification (`autoharness verify-workspace`)**: **PASS** (exit code `0`, `0` strict-schema blockers, `0` blockers, `0` unresolved placeholders, `108/108` manifest checksums `unchanged`, all `43` targeted checks `PASS`).
* **Copilot Code-Review Focus base-branch caveat**: `.github/instructions/copilot-code-review.instructions.md` passed all structural and frontmatter checks (`applyTo: '**'`, `excludeAgent: 'cloud-agent'`). Remember that GitHub Copilot code review reads instructions from the pull request's **base branch**, so any future changes to that instruction take effect for code review only after merging to `main` (and the Settings → Copilot → Code review custom-instructions toggle is an advisory prerequisite).
* **Git branch safety (Phase 0c)**: The workspace is currently on `main` with uncommitted changes. Never commit or push tuning output directly to `main`. Create and switch to a feature branch (for example `git checkout -b chore/autoharness-tune-2026-10-26`), review the diff, and open a pull request.

## Adversarial Verification

### Reviewer Dispatch

* **Anchor Reviewer** (`model_routing.anchor_review`: `openai` / `gpt-6.1-sol`, `high` — `TOOL_OK: anchor-review-model`): `overlay-coherence` — 0 findings
* **Reviewer A** (Template Fidelity — `google` / `gemini-4-argon`, `high`, `long_context`): 0 findings
* **Reviewer B** (Overlay Coherence — `anthropic` / `claude-sonnet-5.5`, `high`, `long_context`): 0 findings
* **Reviewer C** (Cross-Reference Integrity — `anthropic` / `claude-haiku-5.5`, `xhigh`, `long_context`): 16 raw findings (6 confirmed HIGH-confidence cross-reference/staleness findings auto-remediated, 1 false positive dismissed, 9 LOW/MEDIUM advisory observations)

### Consensus Findings (Ordered by Confidence × Severity)

#### HIGH Confidence (Verified by File Inspection & Auto-Remediated)

| # | Severity | Domain | File | Issue | Status |
|---|---|---|---|---|---|
| 1 | MAJOR | `cross-reference` | `AGENTS.md`, `.github/instructions/constitution.instructions.md` | `graphtor-docs` capability overlay sections still pointed to `.graphtor/config/sources.yaml` and had duplicate `graphtor-docs` overlay blocks | AUTO-FIXED |
| 2 | MAJOR | `cross-reference` | `.github/copilot-instructions.md` | `graphtor-docs` section referenced `.graphtor/config/sources.yaml` with duplicate bullets and missing blank line before `## Remote Operator Integration` | AUTO-FIXED |
| 3 | MAJOR | `cross-reference` | `.github/copilot-instructions.md` | Technology Stack table still listed `lancedb` and `kuzu` instead of `cozo (SQLite backend)` from `Cargo.toml` and `workspace-profile.yaml` | AUTO-FIXED |
| 4 | MAJOR | `cross-reference` | `.github/copilot-instructions.md` | Project Structure tree omitted current `src/` modules (`cli`, `db`, `embed`, `ingest_contract`, `mcp`, `parse`, `pipeline`, `query`, `sync`, `workspace`), `tools/mcp-probe/`, and `docs/` subdirectories | AUTO-FIXED |
| 5 | MINOR | `cross-reference` | `.github/prompts/feature-flow-dark.prompt.md` | Requirements 3, 4, and 6 did not explicitly mention the P-018 `copilot-review` gate when engaged or P-020 post-merge context compaction | AUTO-FIXED |
| 6 | MINOR | `cross-reference` | `.github/skills/review/SKILL.md` | `agent-intercom` ping was not gated on pack installation and dark-mode readiness section did not note P-018 precedence when Copilot review is engaged | AUTO-FIXED |

#### MEDIUM / LOW Confidence (Advisory Observations)

* `.github/skills/review/SKILL.md`: Persona subagent names in tables use short filenames (`security-reviewer.agent.md`) while `AGENTS.md` documents `.github/agents/subagents/` as the dispatch directory (advisory; matches upstream `review/SKILL.md.tmpl`).
* `.github/instructions/github-pr-automation.instructions.md`: `§1.9.2` local readiness block focuses on `Blocking findings: P0=0, P1=0` while `Follow-ups` summarizes P2/P3 handling (advisory; matches upstream `github-pr-automation.instructions.md.tmpl`).
* `.autoharness/workspace-profile.yaml`: `mcp-stdio-startup` probe uses `< /dev/null` syntax from existing closure precedent (`049-S`) and `mcp-client-smoke` fallback yields `READY_WITH_CONDITIONS` when deferred (advisory; preserved from workspace's established runtime validator contract).
* **Dismissed false positive**: Reviewer C flagged `validation_expectations.minimum_verdict: PASS_WITH_FOLLOW_UP` and `releasability.status_when_satisfied: READY_WITH_CONDITIONS` against `review/SKILL.md`'s `READY_WITH_FOLLOWUPS`. Those fields belong to the `runtime-verification` and `operational-closure` contracts and are constrained by `schemas/workspace-profile.schema.json` to `PASS_WITH_FOLLOW_UP` and `READY_WITH_CONDITIONS`.

### Auto-Remediation Summary

* Findings auto-fixed: 6
* Findings requiring manual review: 4 (`rust-mcp-expert.agent.md` workspace-authored frontmatter proposals) + 1 (`P-DYN-001` policy proposal)
* False positives dismissed: 1

### Verification Result: PASS WITH WARNINGS

