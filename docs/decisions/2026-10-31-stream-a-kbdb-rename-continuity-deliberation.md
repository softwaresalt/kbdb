---
title: "Stream A Deliberation: kbdb Rename Continuity and Workspace Upgrade Compatibility (Batch 2)"
description: "P-021 C6 deliberation and design decisions for Stream A stash entries 0BD7D83C, 6187B1EE, and 578B8678 targeting Feature 062-F and Shipment 057-S"
topic: "Public installer release-boundary fallback, legacy pre-rename workspace compatibility, and .mcp.json managed-entry custom-shape preservation (Option 2 / Batch 2 — Stream A)"
depth: "standard"
decision_status: "decided"
promoted_to: "plan"
linked_artifacts:
  - "docs/exec-plans/2026-10-31-kbdb-rename-continuity-upgrade-plan.md"
  - ".backlogit/queue/062-F.md"
  - ".backlogit/queue/057-S.md"
tags:
  - "kbdb-rename"
  - "installer-continuity"
  - "mcp-config"
  - "legacy-compatibility"
  - "p-021-c6"
  - "dark-factory"
---

## Problem Frame

Following the completion, delivery (PR #151, `32865071a20380ac2c61d7c1211c1766284b2a71`), and post-merge closure/archival (PR #152, `b3dc39e28f87538c33f976d9bca4bb8e979779b4`) of Batch 1 (`056-S` / `061-F`), we enter Sequence Step 2 under P-017 Dark Factory Mode (`DARK_MODE_ACTIVE = true`): **Batch 2 (Option 2 — Stream A: `0BD7D83C`, `6187B1EE`, `578B8678`)**.

The mechanical rename from `graphtor-docs` / `.graphtor` to `kbdb` / `.kbdb` (PR #133, `061634a`) updated source constants, CLI strings, and public installer scripts (`install.sh`, `install.ps1`). Three concrete continuity and generation-safety gaps remain across that rename boundary:

1. **Public installer release-boundary failure (`0BD7D83C`, High)**:
   * `install.sh` and `install.ps1` resolve the latest GitHub release (`v0.3.1`) and request `kbdb-v0.3.1-<target>.(tar.gz|zip)` containing `kbdb[.exe]`. Because `v0.3.1` was published prior to the rename, its release assets are named `graphtor-docs-v0.3.1-<target>.(tar.gz|zip)` and contain `graphtor-docs[.exe]`. Without an in-script fallback, public installer invocations against pre-rename releases fail with HTTP 404.
2. **Legacy pre-rename workspace artifacts in Rust lifecycle commands (`6187B1EE`, Medium)**:
   * Existing workspaces created before PR #133 contain:
     * `"graphtor-docs"` server keys and `"x-graphtor-managed": true` provenance markers (or unmarked `{command, args: ["serve"], transport: "stdio"}` legacy entries) in `.mcp.json` and legacy editor configs (`.vscode/mcp.json`, `.cursor/mcp.json`, `.github/copilot/mcp.json`), causing `kbdb install` to leave duplicate server keys and `kbdb uninstall` to miss legacy entries.
     * `# graphtor-docs — managed by graphtor-docs install` (or ASCII hyphen `-`) marker headers and `.graphtor/` lines in `.gitignore`, plus legacy `graphtor.lock` lock files, which `src/workspace/gitignore.rs` and `src/workspace/uninstall.rs` no longer recognize.
     * Pre-existing `.graphtor/` workspace directories (and `.graphtor/config/sources.yaml` registries), which `kbdb doctor` and `kbdb init` / `kbdb install --with-ingestion` do not detect, report, or migrate.
3. **Managed `.mcp.json` custom-shape clobbering (`578B8678`, Medium)**:
   * In `src/workspace/mcp_config.rs`, `generate_mcp_config` replaces any entry carrying the managed marker (`x-kbdb-managed: true` or legacy `x-graphtor-managed: true`) with the canonical 4-key object `{command, args: ["serve"], transport: "stdio", "x-kbdb-managed": true}`. If a marked entry was customized with client-specific fields (such as `"type": "stdio"`, `"tools": ["*"]`, `"env": {...}`, or a custom wrapper/shim `command`/`args`), running `kbdb install` overwrites those fields.

All three Stream A entries carry the `DEFERRED SCOPE EXPANSION` token captured under P-021 C2 and therefore require P-021 C5/C6 duplicate detection, late-identifier reconciliation, and durable deliberation prior to planning and harvest.

### Scope Boundaries

* **In scope**: `0BD7D83C`, `6187B1EE`, and `578B8678`, plus the 6 Stage-owned planning/contract captures surfaced during Step 1.5 publication review of PR #153 (`C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`), harvested into covering feature `062-F` and Mode H fully-covered-root shipment `057-S` (sequenced after `056-S` via `backlogit dep add 057-S 056-S --type blocks`).
* **Strictly out of scope (untouched)**:
  * Stream C stash entries (`ECD56875`, `AC2E02C0`, `787C92F9`, `8EFB7D92`, `FF798FA3`).
  * P-021 captures created during the `056-S` dark run (`150A478A`, `E4B2B0B3` — per P-017/P-021, captures created during a dark run are never triaged or planned inside the dark run itself).
  * Queue items `059-F` (`059.001-T`..`059.014-T`), `013.008-T`, and `060-F`.

## Research Findings

### Prior Learnings (`docs/compound/`)

* **Checksum verification safety in installers (`docs/compound/best-practices/installer-checksum-empty-grep-pattern-2026-05-08.md`)**: Never pipe `grep` directly to `sha256sum --check`; capture the matching `SHA256SUMS` line for the active archive filename (`kbdb-...` or fallback `graphtor-docs-...`), fail closed if empty or ambiguous, and verify before extraction.
* **Reparse-point containment (`docs/compound/best-practices/reparse-point-fail-closed-containment-2026-07-16.md`)**: Any workspace migration or detection touching `.graphtor/` or `.gitignore` / `.mcp.json` must preserve `is_reparse_point` and `validate_path` containment checks so symlinks and Windows junctions are never followed outside the workspace root (Constitution Principles III/IV).
* **Level-1 ID allocation (`docs/compound/backlogit-level1-id-collision-across-parent-types.md`)**: Using `--type feature` allocates `062-F` (`max(feature) = 061` from `061-F`), avoiding any `{NNN}` collision across queue and archive.
* **Batch 1 (`056-S`) execution learnings (`docs/memory/2026-10-31-ship-056-s-execution.md`)**:
  * `mod workspace;` is compiled as part of the `kbdb` binary target (`src/main.rs`), not the `graphtor_core` library target (`src/lib.rs`). Unit tests in `src/workspace/*` must be invoked via `cargo test --bin kbdb <test_filter>`, not `cargo test --lib`.
  * `cargo test` must run with default OS `TEMP` and `TMP` outside the repository tree so `tempfile::tempdir()` does not trigger ancestor discovery of the repository's `.kbdb/` directory.
  * CI `cargo audit` uses the explicit 11-advisory `--ignore` allowlist in `.github/workflows/ci.yml`.

### Codebase Analysis

* **`install.sh` and `install.ps1`**:
  * Both scripts already support `KBDB_VERSION` / `GRAPHTOR_VERSION` and `KBDB_INSTALL_DIR` / `GRAPHTOR_INSTALL_DIR` environment variable fallbacks, but hardcode `ARCHIVE="kbdb-${KBDB_VERSION}-${TARGET}.tar.gz"` (and `.zip` in `install.ps1`) and require `kbdb` / `kbdb.exe` inside the archive.
* **`src/workspace/mcp_config.rs`**:
  * Defines `MCP_SERVER_KEY = "kbdb"`, `MANAGED_MARKER_KEY = "x-kbdb-managed"`, and `LEGACY_COMMAND_SHAPES` (`.kbdb/bin/kbdb[.exe]`, `.graphtor/bin/graphtor-docs[.exe]`).
  * Does not yet recognize `"graphtor-docs"` (`LEGACY_MCP_SERVER_KEY`), `"x-graphtor-managed"` (`LEGACY_MANAGED_MARKER_KEY`), or bare `"graphtor-docs"` / `"graphtor-docs.exe"` in `LEGACY_COMMAND_SHAPES`.
  * In `generate_mcp_config`, `ExistingEntryClass::Marked` unconditionally replaces the entry with `managed_server_value(&command)`, discarding extra keys (`type`, `tools`, `env`, `cwd`) or custom wrapper/shim `command`/`args`.
* **`src/workspace/gitignore.rs` and `src/workspace/uninstall.rs`**:
  * `gitignore.rs` checks only `MARKER_HEADER = "# kbdb — managed by kbdb install"` and `GITIGNORE_ENTRY = ".kbdb/"`.
  * `uninstall.rs` checks only `WORKSPACE_LOCK_FILE = "kbdb.lock"` in `predict_root_removal` and delegates `.gitignore` and MCP cleanup to `gitignore.rs` and `mcp_config.rs`.
* **`src/workspace/doctor.rs` and `src/workspace/init.rs`**:
  * `doctor.rs` inspects `.kbdb` (`workspace_dir`) without checking whether a sibling `.graphtor/` directory exists in `workspace_dir.parent()`.
  * `init.rs` writes a blank `SOURCES_YAML_TEMPLATE` when `.kbdb/config/sources.yaml` is absent, even when a pre-rename `.graphtor/config/sources.yaml` exists in the same project root.
* **ID Availability Verification**:
  * Confirmed zero prior references to `062-F`, `062.*`, or `057-S` across `.backlogit/queue/`, `.backlogit/archive/`, `.backlogit/logs/`, and `.backlogit/hooks_queue.jsonl`.

## P-021 C5 and C6 Triage Obligations

### Unconditional Duplicate Detection Scan — Obligation A

Stage scanned all active stash entries in `.backlogit/stash.jsonl` (10 entries at initial Batch 2 intake; 13 entries at Step 1.5 PR #153 follow-up reconciliation) and all archived stash entries in `.backlogit/archive/stash.jsonl` (87 entries at initial Batch 2 intake; 90 entries after archiving `0BD7D83C`, `6187B1EE`, and `578B8678`) for overlap with `0BD7D83C`, `6187B1EE`, `578B8678`, and the 6 Step 1.5 PR #153 planning/contract captures (`C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`):

* `0BD7D83C` covers public release-installer archive/binary fallback (`install.sh`, `install.ps1`) across the `v0.3.1` rename boundary.
* `6187B1EE` covers in-repo Rust workspace compatibility (`src/workspace/mcp_config.rs`, `gitignore.rs`, `uninstall.rs`, `doctor.rs`, `init.rs`) for pre-rename `.graphtor` / `graphtor-docs` artifacts (plus optional legacy install-dir notice in `install.sh` / `install.ps1`).
* `578B8678` covers `.mcp.json` `generate_mcp_config` custom-shape and custom-field preservation on marked entries (`src/workspace/mcp_config.rs`). Note (`C8CCC000` provenance clarification) that sub-issue (a) of `578B8678` — retiring the temporary `.copilot/graphtor-mcp-shim.cjs` bun-shim launch in `.mcp.json` and restoring direct `.kbdb\bin\kbdb.exe` `serve` execution — was delivered by Shipment `055-S` PR #141 (merge commit `4a6a912575f33f19f63129a600061db97dd2c4d5`, documented in `docs/decisions/2026-10-30-056-004-t4-restored-production-acceptance-evidence.md:26-38` and `docs/closure/2026-10-30-055-s-phase-3-final-docs-t4-post-merge-closure.md:18-20,78-79`), distinct from the mechanical `graphtor-docs` -> `kbdb` identifier rename in PR #133 (`061634a`). Sub-issue (b) (preserving custom fields such as `"type": "stdio"`, `"tools": ["*"]`, `"env"`, and custom wrapper/shim `command`/`args` on marked entries during `generate_mcp_config`) remains active and complements `6187B1EE`'s `mcp_config.rs` migration work.
* The 6 Step 1.5 PR #153 captures (`C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`) carry `DISCOVERY-STATUS: LOOKUP-UNAVAILABLE` (prioritized known-risk scan accelerator because `backlogit` CLI has no archived-stash list command) and refine the Stage-owned deliberation, implementation plan, and task contracts of `062-F` / `057-S` prior to Ship execution:
  * `C8CCC000`: Clarify `.mcp.json` bun-shim retirement provenance (`055-S` PR #141, `4a6a912575f33f19f63129a600061db97dd2c4d5` vs. mechanical rename PR #133, `061634a`) in this deliberation.
  * `435498A0`: Add a dedicated `## Constitution Check` section to `docs/exec-plans/2026-10-31-kbdb-rename-continuity-upgrade-plan.md` mapping Principles I–XI (`constitution.instructions.md:331-334`).
  * `1E585DFF`: Replace double-quoted regex `-notmatch "\$LegacyBinary"` / `-notmatch "\$legacyArchive"` with literal `.Contains('$LegacyBinary')` / `.Contains('$legacyArchive')` in `062.001-T.md` and Plan Unit 1 so PowerShell variable interpolation never leaves a trailing backslash in a regex pattern.
  * `4ABF7389`: Retain the legacy `# graphtor-docs` `.gitignore` block (`.graphtor/`) during `add_gitignore_entry` and `remove_gitignore_entry` whenever `<project_root>/.graphtor` still exists on disk (`062.003-T.md` and Plan Unit 3).
  * `BAA98E91`: Remove any stale `graphtor.lock` file inside `.kbdb/` alongside `kbdb.lock` during actual `uninstall` in `src/workspace/uninstall.rs` (matching `predict_root_removal`) and verify agreement between `dry_run: true` preview (`predict_root_removal`) and `dry_run: false` actual removal (`062.003-T.md` and Plan Unit 3).
  * `ACDAB8DA`: Normalize only `# graphtor-docs` header comments (to `# kbdb`) in `init_sources_yaml` while preserving all YAML source `path` / `url` / `glob` content byte-for-byte when copying `.graphtor/config/sources.yaml` to `.kbdb/config/sources.yaml` (`062.004-T.md` and Plan Unit 4).
* **Outcome**: **CLEAN DUPLICATE SCAN** across all 9 `DEFERRED SCOPE EXPANSION` entries (`0BD7D83C`, `6187B1EE`, `578B8678`, `C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`; zero duplicate entries found in active or archived stash).

### Mandatory Late-Identifier Reconciliation — Obligation B

Stage searched Ship-owned closure and residual-risk records (`docs/closure/`, `docs/memory/2026-10-31-ship-stage-057-s-publication.md`, and `git log` on `main`) for every `N/A` source-reference field in `0BD7D83C`, `6187B1EE`, `578B8678`, `C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, and `ACDAB8DA`:

| Stash ID | Captured `N/A` Fields | Reconciled Identifiers & Source Record | Terminal Disposition |
|---|---|---|---|
| `0BD7D83C` | `task_id`, `feature_id`, `shipment_id` (`pr_number=133`, `review_thread_id=PRRT_kwDORiB5E86xvRkz` already populated) | Originated on standalone prerequisite rename PR `#133` (`061634a`, `chore: rename graphtor-docs to kbdb (#133)`), which ran outside any shipment/feature/task | No late task/feature/shipment identifier exists; `task_id=N/A`, `feature_id=N/A`, `shipment_id=N/A` stand as truthful terminal record |
| `6187B1EE` | `task_id`, `feature_id`, `shipment_id`, `pr_number`, `review_thread_id` | Reconciled `pr_number=133` (and merge commit `061634a`) from sibling capture `0BD7D83C` on branch `chore/rename-graphtor-docs-to-kbdb`; finding was surfaced by pre-PR local review with no GitHub review thread and no shipment/feature/task | `pr_number=133` reconciled; `task_id=N/A`, `feature_id=N/A`, `shipment_id=N/A`, and `review_thread_id=N/A` stand as truthful terminal record |
| `578B8678` | `task_id`, `feature_id`, `shipment_id` (`pr_number=118`, `review_thread_id=PRRT_kwDORiB5E86fdtzs` already populated) | Verified in `docs/closure/2026-09-04-pr-118-startup-checkpoint-recovery-post-merge-closure.md` (lines 87, 186, 646): PR `#118` (`255020e`) was a standalone chore-branch session with no claimed shipment, feature, or task | No late task/feature/shipment identifier exists; `task_id=N/A`, `feature_id=N/A`, `shipment_id=N/A` stand as truthful terminal record |
| `C8CCC000` | `pr_number`, `review_thread_id` (`task_id=062.001-T`, `feature_id=062-F`, `shipment_id=057-S` already populated) | Surfaced during pre-PR local persona review of Stage commit `3441e5c` and subsequently published in staging PR `#153` (merge commit `23b0776`, recorded in `docs/memory/2026-10-31-ship-stage-057-s-publication.md`). Reconciled `pr_number=153` in place via `backlogit stash edit`; no GitHub review thread was created for this local persona finding | `pr_number=153` reconciled; `review_thread_id=N/A` stands as truthful terminal record |
| `435498A0` | `pr_number`, `review_thread_id` (`task_id=062.001-T,062.002-T,062.003-T,062.004-T`, `feature_id=062-F`, `shipment_id=057-S` already populated) | Surfaced during pre-PR local persona review of Stage commit `3441e5c` and subsequently published in staging PR `#153` (merge commit `23b0776`, recorded in `docs/memory/2026-10-31-ship-stage-057-s-publication.md`). Reconciled `pr_number=153` in place via `backlogit stash edit`; no GitHub review thread was created for this local persona finding | `pr_number=153` reconciled; `review_thread_id=N/A` stands as truthful terminal record |
| `1E585DFF` | None (`task_id=062.001-T`, `feature_id=062-F`, `shipment_id=057-S`, `pr_number=153`, `review_thread_id=PRRT_kwDORiB5E86yTdqj`, `comment_id=4432821802` all populated at capture) | Verified in `docs/memory/2026-10-31-ship-stage-057-s-publication.md` — no `N/A` fields present | All source-ref fields concrete at capture (reconciliation no-op) |
| `4ABF7389` | None (`task_id=062.003-T`, `feature_id=062-F`, `shipment_id=057-S`, `pr_number=153`, `review_thread_id=PRRT_kwDORiB5E86yTdqv`, `comment_id=4432821828` all populated at capture) | Verified in `docs/memory/2026-10-31-ship-stage-057-s-publication.md` — no `N/A` fields present | All source-ref fields concrete at capture (reconciliation no-op) |
| `BAA98E91` | None (`task_id=062.003-T`, `feature_id=062-F`, `shipment_id=057-S`, `pr_number=153`, `review_thread_id=PRRT_kwDORiB5E86yTdq7`, `comment_id=4432821845` all populated at capture) | Verified in `docs/memory/2026-10-31-ship-stage-057-s-publication.md` — no `N/A` fields present | All source-ref fields concrete at capture (reconciliation no-op) |
| `ACDAB8DA` | None (`task_id=062.004-T`, `feature_id=062-F`, `shipment_id=057-S`, `pr_number=153`, `review_thread_id=PRRT_kwDORiB5E86yTdrD`, `comment_id=4432821861` all populated at capture) | Verified in `docs/memory/2026-10-31-ship-stage-057-s-publication.md` — no `N/A` fields present | All source-ref fields concrete at capture (reconciliation no-op) |

## Options Evaluated

### Option A: Non-Destructive In-Place Compatibility, Custom-Shape Preservation, and Safe Detection/Migration (Recommended)

* **Description**:
  1. **Installers (`0BD7D83C` + `6187B1EE` notice + `1E585DFF` harness safety — `install.sh`, `install.ps1`)**:
     * Attempt to download primary `kbdb-<version>-<target>.(tar.gz|zip)` first; if the download fails (such as HTTP 404 on pre-rename release `v0.3.1`), fall back to `graphtor-docs-<version>-<target>.(tar.gz|zip)`.
     * Verify the downloaded archive against `SHA256SUMS` using the active archive name.
     * Extract `kbdb[.exe]` if present in the archive, otherwise fall back to `graphtor-docs[.exe]`, and install it to the target bin directory as `kbdb` (`kbdb.exe` on Windows).
     * Emit a non-blocking warning if a legacy `~/.local/bin/graphtor-docs` (or `${INSTALL_DIR}/graphtor-docs`) or `%LOCALAPPDATA%\graphtor-docs\bin` binary/directory is detected.
     * Use literal `.Contains('$LegacyBinary')` and `.Contains('$legacyArchive')` checks in `062.001-T`'s PowerShell `Harness command:` rather than double-quoted `-notmatch "\$LegacyBinary"` regexes (`1E585DFF`).
  2. **MCP Config Migration & Custom-Shape Preservation (`6187B1EE` (a) + `578B8678` — `src/workspace/mcp_config.rs`)**:
     * Recognize `LEGACY_MCP_SERVER_KEY = "graphtor-docs"`, `LEGACY_MANAGED_MARKER_KEY = "x-graphtor-managed"`, and bare `"graphtor-docs"` / `"graphtor-docs.exe"` in `LEGACY_COMMAND_SHAPES`.
     * On `generate_mcp_config`:
       * If a managed `"graphtor-docs"` entry exists (marked with `x-graphtor-managed: true` / `x-kbdb-managed: true` or matching `is_exact_legacy_shape`) and `"kbdb"` is absent, migrate it in place to key `"kbdb"` (removing `"graphtor-docs"`). If `"kbdb"` is already present and valid (not a collision), prune the stale managed `"graphtor-docs"` entry so no duplicate server remains.
       * When refreshing any marked entry (`x-kbdb-managed: true` or migrated `x-graphtor-managed: true`), preserve all additional user/harness keys (`"type"`, `"tools"`, `"env"`, `"cwd"`, etc.). Refresh `"command"` (and `"args": ["serve"]`) via the resolution ladder ONLY when the existing `"command"` is a standard managed binary path/name (`kbdb[.exe]`, `graphtor-docs[.exe]`, `LEGACY_COMMAND_SHAPES`, or a canonical `/.kbdb/bin/kbdb[.exe]` / `/.graphtor/bin/graphtor-docs[.exe]` path) with standard `["serve"]` args; if the marked entry uses a custom wrapper/shim `command` or custom `args`, preserve its custom `command` and `args` intact while normalizing the marker to `"x-kbdb-managed": true`. If the entry already has `"type"` and no `"transport"`, do not force-insert `"transport"`.
     * On `prune_managed_server` / `file_has_managed_entry` / `remove_mcp_config_from`: prune managed entries under both `"kbdb"` and legacy `"graphtor-docs"`, while continuing to preserve unmarked non-legacy entries and user copies under other keys.
  3. **Gitignore & Uninstall Legacy Recognition (`6187B1EE` (b) + `4ABF7389` + `BAA98E91` — `src/workspace/gitignore.rs`, `src/workspace/uninstall.rs`)**:
     * Recognize legacy marker headers (`# graphtor-docs — managed by graphtor-docs install` and `# graphtor-docs - managed by graphtor-docs install`) and `.graphtor/` / `.graphtor` entries in `has_managed_gitignore_block`, `remove_gitignore_entry`, and `add_gitignore_entry`:
       * When `add_gitignore_entry(project_root)` runs: if a legacy managed `# graphtor-docs` block is present and `<project_root>/.graphtor` still exists on disk, retain `.graphtor/` in `.gitignore` alongside the new `# kbdb — managed by kbdb install` + `.kbdb/` block; strip the legacy `# graphtor-docs` managed block only when `<project_root>/.graphtor` does not exist on disk (`4ABF7389`).
       * When `remove_gitignore_entry(project_root)` runs (during `uninstall`): remove the `# kbdb` managed block (`.kbdb/`), and remove the legacy `# graphtor-docs` managed block (`.graphtor/`) only if `<project_root>/.graphtor` does not exist on disk, retaining `.graphtor/` Git exclusion while `<project_root>/.graphtor` remains on disk (`4ABF7389`). Unmarked user-authored lines are always preserved.
     * In `src/workspace/uninstall.rs` (`BAA98E91`): ignore both `kbdb.lock` and `graphtor.lock` in `predict_root_removal`, AND remove any stale non-symlink `graphtor.lock` file inside `.kbdb/` alongside `kbdb.lock` during actual `uninstall` (`uninstall_planned` / `remove_empty_workspace_root`) so `dry_run: true` preview (`predict_root_removal`) and `dry_run: false` actual removal always agree when `graphtor.lock` is present.
  4. **Legacy `.graphtor/` Detection, Reporting, and Config Migration (`6187B1EE` (c) + `ACDAB8DA` — `src/workspace/doctor.rs`, `src/workspace/init.rs`)**:
     * In `doctor.rs`: add `detect_legacy_workspace_dir(project_root: &Path) -> Option<PathBuf>`. When a sibling `.graphtor/` exists in the project root, emit a `Check` (`name: "legacy-workspace-dir"`, `severity: Severity::Warn`) advising migration to `.kbdb/` (and enrich the `workspace-dir` `Fail` message when `.kbdb/` is missing but `.graphtor/` is present). When `.graphtor/` is absent, emit no extra check so clean minimal/full workspaces remain warning-free.
     * In `init.rs` (`ACDAB8DA`): when `init_sources_yaml` creates `.kbdb/config/sources.yaml` (`!target.exists() && !force`) and a non-symlink legacy `<project_root>/.graphtor/config/sources.yaml` exists (guarded by `is_reparse_point` on `.graphtor`, `.graphtor/config`, and `sources.yaml`), copy the legacy `sources.yaml` into `.kbdb/config/sources.yaml` normalizing **only** `# graphtor-docs` header comments (to `# kbdb`, such as `# graphtor-docs sources.yaml` -> `# kbdb sources.yaml` and ``# Run `graphtor-docs sync` `` -> ``# Run `kbdb sync` ``) while preserving all YAML source `path` / `url` / `glob` content byte-for-byte so source references pointing to retained `.graphtor/...` content are never broken.
* **Pros**: Solves all three Stream A stash entries and all 6 PR #153 review refinements completely, keeps task file ownership 100% disjoint across 4 small tasks (`1–2` files each), preserves all existing test contracts and containment invariants, and avoids risky automatic directory moves of open SQLite/Cozo databases during CLI commands.
* **Cons**: Automatic rename of the entire `.graphtor/` directory tree (which may hold open database handles) remains delegated to `scripts/convert-to-kbdb.ps1` or manual move, while `doctor` warns clearly, `.gitignore` retains `.graphtor/` exclusion while `.graphtor/` remains on disk, and `init`/`install --with-ingestion` migrates `sources.yaml` safely without breaking source paths.
* **Effort estimate**: Low–Medium (4 width-isolated tasks, `<2h` each).
* **Fit**: High alignment with Rust safety conventions, Constitution Principles III/IV (workspace containment), and P-003 task granularity.

### Option B: Automatic Destructive Rename of `.graphtor/` -> `.kbdb/` Inside `cmd_install` / `cmd_doctor` and Hard Overwrite of Marked `.mcp.json` Entries

* **Description**: Have `kbdb doctor` or `kbdb install` automatically `fs::rename(".graphtor", ".kbdb")` on disk, and require users with custom `.mcp.json` fields to remove `x-kbdb-managed: true` instead of preserving custom keys in `generate_mcp_config`.
* **Pros**: Fewer lines of merge logic in `mcp_config.rs`.
* **Cons**:
  * Mutating filesystem state inside `kbdb doctor` violates the read-only diagnostic contract of `doctor`.
  * Automatically moving `.graphtor/` during `kbdb install` fails on Windows whenever an MCP server process holds open handles in `.graphtor/` and risks partial state if both `.graphtor/` and `.kbdb/` exist.
  * Forcing users or harnesses (including this repository's own `.mcp.json`, which carries `"type": "stdio"`, `"tools": ["*"]`, and `"x-kbdb-managed": true`) to lose custom keys on `kbdb install` directly fails `578B8678`.
* **Effort estimate**: Medium.
* **Fit**: Poor — unsafe on Windows locked files and fails `578B8678`'s generation-safety requirement.

## Trade-off Comparison

| Criterion | Option A (Non-Destructive Compat + Custom-Shape Preservation) | Option B (Auto-Move `.graphtor/` + Canonical-Only Overwrite) |
|---|---|---|
| Installer `v0.3.1` continuity (`0BD7D83C`, `1E585DFF`) | Full fallback (`kbdb-...` -> `graphtor-docs-...`) with SHA-256 verification and literal `.Contains` harness check | Full fallback |
| `.mcp.json` custom fields & shims (`578B8678`, `C8CCC000`) | Preserves `"type"`, `"tools"`, `"env"`, and custom wrapper `command`/`args` on marked entries | Clobbers custom fields unless marker is removed |
| Legacy `.graphtor/` safety (`6187B1EE`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`) | Read-only `doctor` warning + retains `.graphtor/` `.gitignore` exclusion while on disk + consistent `graphtor.lock` preview/removal + safe `sources.yaml` copy preserving source paths/globs | Risk of Windows file-lock failure, untracked `.graphtor/` exposure, or broken source paths |
| Task file disjointness (P-003) | 4 tasks with 100% disjoint file sets (`1–2` files per task) | Cross-cuts `main.rs`, `install.rs`, and `doctor.rs` |

## Decision

We adopt **Option A** and decompose the work into covering feature **`062-F`** ("`kbdb` Rename Continuity, Legacy Workspace Compatibility, and MCP Config Preservation") and 4 width-isolated tasks assembled into Mode H shipment **`057-S`**:

1. **`062.001-T` (`install.sh`, `install.ps1` — 2 files)**: Public installer release-boundary archive/binary fallback (`kbdb-v<ver>-<target>` -> `graphtor-docs-v<ver>-<target>`, installing `kbdb[.exe]` or `graphtor-docs[.exe]` as `kbdb[.exe]`), legacy install-directory warning, and literal `.Contains` PowerShell harness check (`0BD7D83C`, `6187B1EE`, `C8CCC000`, `435498A0`, `1E585DFF`).
2. **`062.002-T` (`src/workspace/mcp_config.rs` — 1 file)**: Legacy `"graphtor-docs"` MCP server key and `x-graphtor-managed: true` migration/pruning plus custom-field (`type`, `tools`, `env`) and custom-wrapper/shim preservation on marked entries (`6187B1EE`, `578B8678`, `435498A0`).
3. **`062.003-T` (`src/workspace/gitignore.rs`, `src/workspace/uninstall.rs` — 2 files, depends on `062.002-T`)**: Legacy `# graphtor-docs — managed by graphtor-docs install` `.gitignore` block management (retaining `.graphtor/` exclusion while `<project_root>/.graphtor` exists on disk and stripping it only when `<project_root>/.graphtor` is absent) and consistent `graphtor.lock` handling across `predict_root_removal` preview and actual `uninstall` removal (`6187B1EE`, `435498A0`, `4ABF7389`, `BAA98E91`).
4. **`062.004-T` (`src/workspace/doctor.rs`, `src/workspace/init.rs` — 2 files)**: Legacy `.graphtor/` workspace directory detection and warning in `doctor` and safe `.graphtor/config/sources.yaml` copy in `init` normalizing only `# graphtor-docs` header comments while preserving all YAML source `path` / `url` / `glob` content byte-for-byte (`6187B1EE`, `435498A0`, `ACDAB8DA`).

## Rejected Alternatives

* **Option B (Auto-renaming `.graphtor/` during `doctor`/`install` and keeping canonical-only `.mcp.json` overwrite)**: Rejected because `doctor` must remain read-only, `.kbdb` lock bootstrap in `cmd_install` creates `.kbdb/` before `install` runs, and overwriting marked `.mcp.json` entries destroys `"type": "stdio"`, `"tools": ["*"]`, and custom wrapper settings (`578B8678`).

## Unresolved Questions

* None. All design choices for `0BD7D83C`, `6187B1EE`, `578B8678`, and the 6 PR #153 review captures (`C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`) are resolved and bounded to the 7 target files above.

## Risks and Mitigations

* **Risk 1: Checksum verification bypass during installer fallback (`0BD7D83C`)**:
  * *Mitigation*: Both `install.sh` and `install.ps1` update the active archive filename variable when falling back to `graphtor-docs-<version>-<target>.(tar.gz|zip)` BEFORE looking up the hash in `SHA256SUMS`, preserving the exact fail-closed checksum check from `docs/compound/best-practices/installer-checksum-empty-grep-pattern-2026-05-08.md`.
* **Risk 2: Symlink/junction containment escape when inspecting `.graphtor/` (`6187B1EE`)**:
  * *Mitigation*: `init_sources_yaml` checks `is_reparse_point` on `.graphtor`, `.graphtor/config`, and `.graphtor/config/sources.yaml` before reading any legacy config, and `mcp_config.rs` / `gitignore.rs` / `uninstall.rs` retain all existing `is_reparse_point` and `validate_path` guards.
* **Risk 3: Running `cargo test --lib` instead of `cargo test --bin kbdb` for `src/workspace/*` tests**:
  * *Mitigation*: `mod workspace` lives in the `kbdb` binary target (`src/main.rs`). Every Rust task's `Harness command:` explicitly invokes `cargo test --bin kbdb <specific_new_test_prefix>` and checks `if ($LASTEXITCODE -ne 0 -or $out -match "running 0 tests") { exit 1 }`.
* **Risk 4: Exposing retained `.graphtor/` artifacts as untracked or breaking retained source paths (`4ABF7389`, `ACDAB8DA`, `BAA98E91`)**:
  * *Mitigation*: `gitignore.rs` retains the legacy `# graphtor-docs` / `.graphtor/` block whenever `<project_root>/.graphtor` still exists on disk; `uninstall.rs` removes stale `graphtor.lock` during actual `uninstall` so `dry_run` preview and execution match; and `init.rs` normalizes only `# graphtor-docs` header comments while preserving all YAML source `path` / `url` / `glob` values byte-for-byte.
