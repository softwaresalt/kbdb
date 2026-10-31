---
title: "Implementation Plan: kbdb Rename Continuity, Legacy Workspace Compatibility, and MCP Config Preservation (062-F / 057-S)"
description: "Structured implementation plan for Batch 2 (Option 2 — Stream A: 0BD7D83C, 6187B1EE, 578B8678) covering installer release-boundary fallback, legacy Rust workspace compatibility, and .mcp.json custom-shape preservation"
source: "docs/decisions/2026-10-31-stream-a-kbdb-rename-continuity-deliberation.md"
stash_ids:
  - "0BD7D83C"
  - "6187B1EE"
  - "578B8678"
  - "C8CCC000"
  - "435498A0"
  - "1E585DFF"
  - "4ABF7389"
  - "BAA98E91"
  - "ACDAB8DA"
backlog_refs:
  - "062-F"
  - "062.001-T"
  - "062.002-T"
  - "062.003-T"
  - "062.004-T"
  - "057-S"
tags:
  - "kbdb-rename"
  - "installer-continuity"
  - "mcp-config"
  - "legacy-compatibility"
  - "057-s"
---

## Problem Frame

Following the `graphtor-docs` -> `kbdb` rename (`061634a`, PR #133) and the completion of Batch 1 (`056-S` / `061-F`), three Stream A continuity and generation-safety requirements must be implemented (`docs/decisions/2026-10-31-stream-a-kbdb-rename-continuity-deliberation.md`):

1. **Public installer release-boundary continuity (`0BD7D83C`, High; plus `6187B1EE` legacy binary notice)**:
   * `install.sh` and `install.ps1` request `kbdb-<version>-<target>.(tar.gz|zip)`, which fails with HTTP 404 against the latest published pre-rename GitHub release `v0.3.1` (`graphtor-docs-v0.3.1-<target>.(tar.gz|zip)` containing `graphtor-docs[.exe]`).
   * Both installers must attempt the primary `kbdb-<version>-<target>` archive first, fall back to `graphtor-docs-<version>-<target>` on download failure, verify the active archive against `SHA256SUMS`, extract `kbdb[.exe]` if present (else `graphtor-docs[.exe]`), install it as `kbdb` (`kbdb.exe` on Windows), and emit a non-blocking warning when a legacy `~/.local/bin/graphtor-docs` (or `${INSTALL_DIR}/graphtor-docs`) or `%LOCALAPPDATA%\graphtor-docs\bin` installation is detected.
2. **Legacy pre-rename compatibility in `kbdb` Rust workspace lifecycle code (`6187B1EE`, Medium; refined by `4ABF7389`, `BAA98E91`, `ACDAB8DA`)**:
   * `src/workspace/mcp_config.rs`: recognize the legacy `"graphtor-docs"` MCP server key, `"x-graphtor-managed": true` provenance marker, and unmarked exact-legacy `"graphtor-docs"` entries (`{command, args: ["serve"], transport: "stdio"}`) during `generate_mcp_config` (migrating to `"kbdb"` or pruning stale `"graphtor-docs"` when `"kbdb"` is already present) and during `remove_mcp_config_from` / `file_has_managed_entry` across `.mcp.json` and legacy editor configs.
   * `src/workspace/gitignore.rs` and `src/workspace/uninstall.rs`: recognize `# graphtor-docs — managed by graphtor-docs install` (and ASCII `-`) marker headers and `.graphtor/` entries in `has_managed_gitignore_block`, `remove_gitignore_entry`, and `add_gitignore_entry` — retaining the legacy `# graphtor-docs` / `.graphtor/` block in `.gitignore` during both `add_gitignore_entry` (alongside the new `# kbdb` + `.kbdb/` block) and `remove_gitignore_entry` whenever `<project_root>/.graphtor` still exists on disk, and stripping it only when `<project_root>/.graphtor` does not exist on disk (`4ABF7389`) — and in `src/workspace/uninstall.rs` both ignore `graphtor.lock` alongside `kbdb.lock` in `predict_root_removal` and remove any stale `graphtor.lock` file inside `.kbdb/` during actual `uninstall` so `dry_run: true` preview (`predict_root_removal`) and `dry_run: false` actual removal always agree (`BAA98E91`).
   * `src/workspace/doctor.rs` and `src/workspace/init.rs`: detect a pre-existing `.graphtor/` directory in `doctor.rs` (emitting a `legacy-workspace-dir` `Severity::Warn` check and enriching the missing-`.kbdb/` `workspace-dir` `Severity::Fail` message) and copy a non-symlink `<project_root>/.graphtor/config/sources.yaml` into `.kbdb/config/sources.yaml` during `init_sources_yaml` when `.kbdb/config/sources.yaml` does not yet exist, normalizing only `# graphtor-docs` header comments (to `# kbdb`) while preserving all YAML source `path` / `url` / `glob` content byte-for-byte (`ACDAB8DA`).
3. **Managed `.mcp.json` custom-shape and custom-field preservation (`578B8678`, Medium)**:
   * `src/workspace/mcp_config.rs`: when `generate_mcp_config` refreshes a marked entry (`x-kbdb-managed: true` or migrated `x-graphtor-managed: true`), preserve all additional user/harness keys (`"type"`, `"tools"`, `"env"`, `"cwd"`, etc.) and preserve custom wrapper/shim `"command"` / `"args"` (such as `"bun"` / `[".copilot/graphtor-mcp-shim.cjs"]` or custom flags) instead of overwriting the object with the 4-key canonical template. Refresh `"command"` via the resolution ladder only when the entry uses a standard managed binary command (`kbdb[.exe]`, `graphtor-docs[.exe]`, `LEGACY_COMMAND_SHAPES`, or a canonical `/.kbdb/bin/kbdb[.exe]` / `/.graphtor/bin/graphtor-docs[.exe]` path) with standard `["serve"]` args.

## Requirements Trace

| Stash ID | Requirement | Implementation Unit(s) |
|---|---|---|
| `0BD7D83C` | Primary `kbdb-v<ver>-<target>` -> fallback `graphtor-docs-v<ver>-<target>` archive download, SHA-256 verification, binary extraction (`kbdb[.exe]` else `graphtor-docs[.exe]`), and installation as `kbdb[.exe]` in `install.sh` and `install.ps1` | Unit 1 (`062.001-T`) |
| `6187B1EE` | Optional legacy install directory / binary detection notice (`~/.local/bin/graphtor-docs`, `%LOCALAPPDATA%\graphtor-docs\bin`) in `install.sh` and `install.ps1` | Unit 1 (`062.001-T`) |
| `1E585DFF` | Use literal `.Contains(''$LegacyBinary'')` and `.Contains(''$legacyArchive'')` checks in `062.001-T` PowerShell `Harness command:` to eliminate double-quoted regex variable interpolation and trailing-backslash parse errors | Unit 1 (`062.001-T`) |
| `C8CCC000` | Clarify `.mcp.json` bun-shim launch retirement provenance (`055-S` PR #141 merge `4a6a912575f33f19f63129a600061db97dd2c4d5` vs. mechanical rename PR #133 `061634a`) in the source deliberation | Deliberation (`062-F`, `062.001-T`) |
| `435498A0` | Add dedicated `## Constitution Check` section to this implementation plan mapping Principles I–XI (`constitution.instructions.md:331-334`) with zero violations | Plan (`062-F`, Units 1–4) |
| `6187B1EE` | Recognize, migrate, and prune legacy `"graphtor-docs"` MCP server key, `"x-graphtor-managed": true` marker, and unmarked exact-legacy `"graphtor-docs"` entries in `src/workspace/mcp_config.rs` | Unit 2 (`062.002-T`) |
| `578B8678` | Preserve custom fields (`type`, `tools`, `env`, `cwd`) and custom wrapper/shim `command`/`args` on marked `.mcp.json` entries during `generate_mcp_config` in `src/workspace/mcp_config.rs` | Unit 2 (`062.002-T`) |
| `6187B1EE`, `4ABF7389`, `BAA98E91` | Recognize legacy `# graphtor-docs — managed by graphtor-docs install` `.gitignore` blocks (retaining `.graphtor/` exclusion in `add_gitignore_entry` and `remove_gitignore_entry` whenever `<project_root>/.graphtor` still exists on disk, and stripping it only when `<project_root>/.graphtor` is absent) and handle `graphtor.lock` consistently in both `predict_root_removal` preview and actual `uninstall` removal in `src/workspace/gitignore.rs` and `src/workspace/uninstall.rs` | Unit 3 (`062.003-T`) |
| `6187B1EE`, `ACDAB8DA` | Detect and report an existing `.graphtor/` workspace directory in `src/workspace/doctor.rs` and copy legacy `.graphtor/config/sources.yaml` in `src/workspace/init.rs` normalizing only `# graphtor-docs` header comments while preserving all YAML source `path` / `url` / `glob` content byte-for-byte | Unit 4 (`062.004-T`) |

## Constitution Check

Per `.github/instructions/constitution.instructions.md:331-334` (`435498A0`), the table below maps all proposed work in `062-F` / `057-S` against Constitutional Principles I–XI and the active Capability Overlays:

| Principle / Overlay | Level | Plan Mapping & Compliance Evidence | Status |
|---|---|---|---|
| **I. Safety-First Rust** | MUST | All Rust changes in Units 2–4 (`mcp_config.rs`, `gitignore.rs`, `uninstall.rs`, `doctor.rs`, `init.rs`) target Rust 2021 / `rust-version = "1.88"`, preserve `#![forbid(unsafe_code)]`, propagate all errors via `Result<_, GraphtorError>` without `.unwrap()`/`.expect()` in production code, and pass `cargo clippy --all-targets -- -D warnings -D clippy::pedantic`. | PASS (0 violations) |
| **II. Test-First Development** | NON-NEGOTIABLE | Every task (`062.001-T`..`062.004-T`) carries a deterministic, single-quoted `Harness command:` verified to fail in the red phase on `main` (exit code `1`) before implementation and pass in the green phase (`cargo test --bin kbdb` + PowerShell AST parser). | PASS (0 violations) |
| **III. Workspace Isolation and Security Boundaries** | MUST | All filesystem reads and writes stay confined to `project_root` / `workspace_dir`. Existing `is_reparse_point` and `validate_path` containment checks in `mcp_config.rs`, `gitignore.rs`, and `uninstall.rs` are preserved, and `init_sources_yaml` checks `!is_reparse_point` on `.graphtor`, `.graphtor/config`, and `.graphtor/config/sources.yaml` before reading legacy config content. No secrets or credentials are introduced. | PASS (0 violations) |
| **IV. CLI Workspace Containment** | NON-NEGOTIABLE | No operation creates, modifies, or deletes files outside the workspace directory tree. Symlinked or junction `.gitignore`, `.mcp.json`, `.kbdb`, and `.graphtor` paths are refused fail-closed. | PASS (0 violations) |
| **V. Structured Observability** | MUST | `doctor.rs` emits a structured `Check` (`name: "legacy-workspace-dir"`, `severity: Severity::Warn`) surfaced identically in human and `--json` JSON-RPC 2.0 output; installer scripts emit structured `[WARN]`/`[INFO]` diagnostics; all backlog, checkpoint, and closure records are persisted via `backlogit` and `docs/`. | PASS (0 violations) |
| **VI. Single Responsibility** | SHOULD | Zero new crate dependencies are added to `Cargo.toml` or `Cargo.lock`; all units use the Rust standard library and existing crate dependencies (`serde_json`, `tempfile`). | PASS (0 violations) |
| **VII. Destructive Command Approval** | NON-NEGOTIABLE | `kbdb uninstall` continues to require `--confirm` and executes only the pre-computed `UninstallPlan` (`PA-3`). Stale `graphtor.lock` removal inside `.kbdb/` is gated on `!is_symlink` and limited to the empty-root cleanup contract so `dry_run: true` preview (`predict_root_removal`) matches `dry_run: false` execution (`BAA98E91`). Legacy `.graphtor/` directories and `.gitignore` exclusions for existing `.graphtor/` directories are never destructively removed (`4ABF7389`). | PASS (0 violations) |
| **VIII. Explicit Safety Modes for Elevated Risk** | MUST | `strict_safety.enabled: true` is active; `## Plan Hardening` classifies all proposed actions with `ActionRisk: low`, protected invariants, and rollback paths under freeze-scope/careful discipline. | PASS (0 violations) |
| **IX. Git-Friendly Persistence** | SHOULD | `refresh_marked_server_value` in `mcp_config.rs` preserves existing JSON key ordering (`serde_json` `preserve_order`), `gitignore.rs` preserves user lines and trailing newlines, and `init_sources_yaml` preserves all YAML source `path` / `url` / `glob` content byte-for-byte (`ACDAB8DA`). | PASS (0 violations) |
| **X. Agent Context Efficiency** | SHOULD | Backlog, checkpoint, and codebase lookups use `backlogit` and `engram` indexed queries and targeted file ranges rather than broad directory scans. | PASS (0 violations) |
| **XI. Merge Commit History Preservation** | NON-NEGOTIABLE | Shipment `057-S` PR delivery and closure will use `--merge` (merge commit only, P-009). | PASS (0 violations) |
| **Capability Overlays (`agent-engram`, `backlogit`, `graphtor-docs`, `adversarial-review`)** | MUST | `backlogit` index sync, hook event polling/acknowledgment, and Mode H shipment assembly (`057-S`) are enforced; `.engram/` and `.graphtor/` tool-managed artifacts are never hand-edited. | PASS (0 violations) |

* **Justified Constitutional Violations**: **None** (`0` violations across Principles I–XI).

## Implementation Units

Every unit satisfies the 2-Hour Rule (`1` or `2` files, strictly `< 3` files), 100% disjoint file ownership across all 4 units, and single-domain width isolation.

> [!IMPORTANT]
> **Critical Rust Target & Environment Notes for `_Ship` (from Batch 1 `056-S` learnings)**:
> * `mod workspace;` is declared in `src/main.rs` (`[[bin]] name = "kbdb"`), **not** in `src/lib.rs` (`[lib] name = "graphtor_core"`). All unit tests in `src/workspace/*` MUST be run with `cargo test --bin kbdb <test_filter>` (never `cargo test --lib`).
> * Keep the default OS `TEMP` and `TMP` environment variables outside the repository directory when running `cargo test` so `tempfile::tempdir()` does not trigger ancestor discovery of the repository's own `.kbdb/` directory (`E4B2B0B3`).
> * When running `cargo audit`, use the exact CI allowlist command from `.github/workflows/ci.yml`: `cargo audit --deny warnings --ignore RUSTSEC-2026-0041 --ignore RUSTSEC-2026-0367 --ignore RUSTSEC-2026-0368 --ignore RUSTSEC-2026-0369 --ignore RUSTSEC-2025-0056 --ignore RUSTSEC-2025-0141 --ignore RUSTSEC-2025-0057 --ignore RUSTSEC-2025-0119 --ignore RUSTSEC-2024-0436 --ignore RUSTSEC-2026-0249 --ignore RUSTSEC-2024-0449`.

### Unit 1: Add Pre-Rename Archive/Binary Fallback and Legacy Path Notice to Public Installers (`062.001-T`)

* **Source Stash ID(s)**: `0BD7D83C`, `6187B1EE`, `C8CCC000`, `435498A0`, `1E585DFF`
* **Domain / Width**: Installer Scripts (`install.sh`, `install.ps1`)
* **Size / Complexity**: `size: S`, `complexity: low`
* **Execution Posture**: `characterization-first`
* **Files Affected (2)**:
  1. `install.sh`
  2. `install.ps1`
* **Changes**:
  * In `install.sh`:
    * Define `LEGACY_BINARY="graphtor-docs"` and `LEGACY_ARCHIVE="${LEGACY_BINARY}-${KBDB_VERSION}-${TARGET}.tar.gz"`.
    * Attempt `curl -sSfL "${BASE_URL}/${ARCHIVE}" -o "${TMP}/${ARCHIVE}"`; if it fails, log an `info` fallback message, set `ARCHIVE="${LEGACY_ARCHIVE}"`, and run `curl -sSfL "${BASE_URL}/${ARCHIVE}" -o "${TMP}/${ARCHIVE}"`.
    * Verify `${ARCHIVE}` against `SHA256SUMS` using the existing non-empty `EXPECTED_LINE` check.
    * Extract the archive into `${TMP}` (`tar -xzf "${ARCHIVE}" -C "${TMP}"`), select `${TMP}/${BINARY}` if present or `${TMP}/${LEGACY_BINARY}` as fallback (erroring if neither exists), and install it to `${INSTALL_DIR}/${BINARY}` with mode `0755`.
    * If `${INSTALL_DIR}/${LEGACY_BINARY}` or `${HOME}/.local/bin/${LEGACY_BINARY}` exists, emit a `warn` message noting that the legacy `graphtor-docs` binary was detected and may be removed.
  * In `install.ps1`:
    * Define `$LegacyBinary = 'graphtor-docs'` and `$legacyArchive = "$LegacyBinary-$version-$Target.zip"`.
    * In the download block, try `Invoke-WebRequest "$baseUrl/$archive" -OutFile $archivePath -UseBasicParsing`; in `catch`, log `Write-Info` that the primary archive was not found and fall back to `$archive = $legacyArchive` and `$archivePath = Join-Path $tmpDir $archive`, then invoke `Invoke-WebRequest "$baseUrl/$archive" -OutFile $archivePath -UseBasicParsing`.
    * Keep the `SHA256SUMS` match against `$archive` (which now holds whichever archive was downloaded).
    * After `Expand-Archive`, resolve `$srcExe` to `Join-Path $tmpDir "$Binary.exe"` if present, else `Join-Path $tmpDir "$LegacyBinary.exe"` (erroring if neither exists), and copy it to `$dstExe = Join-Path $installDir "$Binary.exe"`.
    * Check `$legacyInstallDir = Join-Path $env:LOCALAPPDATA 'graphtor-docs\bin'` and `Join-Path $installDir "$LegacyBinary.exe"`; if either exists, emit a `Write-Warn` notice about the legacy `graphtor-docs` installation.
* **Verification**:
  * Confirm `install.sh` and `install.ps1` contain the fallback archive/binary logic and legacy notice, and verify `install.ps1` parses with zero AST errors via `[System.Management.Automation.Language.Parser]::ParseFile`. Use literal `.Contains(''$LegacyBinary'')` and `.Contains(''$legacyArchive'')` checks (`1E585DFF`) so PowerShell never interpolates `$LegacyBinary` or `$legacyArchive` inside double-quoted regex strings.
  * **Harness command**:
    `powershell -NoProfile -Command '$ErrorActionPreference = "Stop"; $sh = Get-Content -Raw "install.sh"; $ps = Get-Content -Raw "install.ps1"; if ($sh -notmatch "LEGACY_BINARY=" -or $sh -notmatch "LEGACY_ARCHIVE=" -or $sh -notmatch "graphtor-docs") { exit 1 }; if ((-not $ps.Contains(''$LegacyBinary'')) -or (-not $ps.Contains(''$legacyArchive'')) -or (-not $ps.Contains(''graphtor-docs\bin''))) { exit 1 }; $tokens = $null; $errs = $null; [void][System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path "install.ps1").Path, [ref]$tokens, [ref]$errs); if ($errs.Count -gt 0) { exit 1 }'`

### Unit 2: Migrate/Prune Legacy `graphtor-docs` MCP Entries and Preserve Custom Marked Entry Shapes (`062.002-T`)

* **Source Stash ID(s)**: `6187B1EE`, `578B8678`, `435498A0`
* **Domain / Width**: Rust Workspace Code (`src/workspace/mcp_config.rs`)
* **Size / Complexity**: `size: M`, `complexity: medium`
* **Execution Posture**: `test-first`
* **Files Affected (1)**:
  1. `src/workspace/mcp_config.rs`
* **Changes**:
  * Add `const LEGACY_MCP_SERVER_KEY: &str = "graphtor-docs";` and `const LEGACY_MANAGED_MARKER_KEY: &str = "x-graphtor-managed";`, and include `"graphtor-docs"` and `"graphtor-docs.exe"` in `LEGACY_COMMAND_SHAPES`.
  * Update `is_marked(entry)` to return `true` when either `MANAGED_MARKER_KEY` (`"x-kbdb-managed"`) or `LEGACY_MANAGED_MARKER_KEY` (`"x-graphtor-managed"`) is `Some(true)`.
  * Add `is_standard_managed_command(cmd: &str) -> bool` returning `true` when `cmd` equals `"kbdb"`, `"kbdb.exe"`, `"graphtor-docs"`, `"graphtor-docs.exe"`, an entry in `LEGACY_COMMAND_SHAPES`, or a path whose forward-slash-normalized form ends with `/.kbdb/bin/kbdb`, `/.kbdb/bin/kbdb.exe`, `/.graphtor/bin/graphtor-docs`, or `/.graphtor/bin/graphtor-docs.exe`.
  * Add `refresh_marked_server_value(existing: &serde_json::Value, command: &str) -> serde_json::Value`:
    * Clone `existing`'s object map so all additional user/harness keys (`"type"`, `"tools"`, `"env"`, `"cwd"`, etc.) and key ordering are preserved.
    * Determine whether `"command"` and `"args"` represent a standard managed invocation (`"command"` is absent or satisfies `is_standard_managed_command`, AND `"args"` is absent or `["serve"]`). When true, set `"command"` to `command` and `"args"` to `["serve"]`; otherwise preserve the custom wrapper/shim `"command"` and `"args"` untouched.
    * If neither `"transport"` nor `"type"` is present, insert `"transport": "stdio"`.
    * Remove `LEGACY_MANAGED_MARKER_KEY` (`"x-graphtor-managed"`) if present and set `MANAGED_MARKER_KEY` (`"x-kbdb-managed": true`).
  * Update `generate_mcp_config`:
    * Inspect whether `servers` contains a managed entry under `LEGACY_MCP_SERVER_KEY` (`"graphtor-docs"`) via `is_managed_for_removal`.
    * When `"kbdb"` is `Absent` and a managed `"graphtor-docs"` entry exists: remove `"graphtor-docs"` and insert `"kbdb"` using `refresh_marked_server_value` (if the legacy entry was marked) or `managed_server_value(&command)` (if it was an unmarked exact-legacy shape), returning `Ok(Some(McpConfigOutcome { path: MCP_CONFIG_PATH.to_string(), action: McpConfigAction::Updated }))`.
    * When `"kbdb"` is `LegacyShape`: also remove any managed `"graphtor-docs"` entry, insert `managed_server_value(&command)` at `"kbdb"`, and write the updated config.
    * When `"kbdb"` is `Marked`: compute `refreshed = refresh_marked_server_value(existing_kbdb, &command)` and also remove any managed `"graphtor-docs"` entry; if `"graphtor-docs"` was not removed and `servers.get(MCP_SERVER_KEY) == Some(&refreshed)`, return `Ok(None)` (byte-for-byte no-op); otherwise insert `refreshed` and write the updated config.
    * When `"kbdb"` is `Collision`: return `Err(GraphtorError::Config { .. })` without modifying the file.
  * Update `prune_managed_server`: filter `servers` for `(key.as_str() == MCP_SERVER_KEY || key.as_str() == LEGACY_MCP_SERVER_KEY) && is_managed_for_removal(cfg)` so `kbdb uninstall` (`file_has_managed_entry` and `remove_mcp_config_from`) prunes managed `"graphtor-docs"` entries as well as `"kbdb"` entries across `.mcp.json`, `.vscode/mcp.json`, `.cursor/mcp.json`, and `.github/copilot/mcp.json`.
* **Verification**:
  * Add 4 unit tests in `src/workspace/mcp_config.rs` with prefix `stream_a_mcp_compat_`:
    1. `stream_a_mcp_compat_migrates_legacy_graphtor_docs_key_and_marker`
    2. `stream_a_mcp_compat_prunes_stale_graphtor_docs_when_kbdb_present`
    3. `stream_a_mcp_compat_preserves_custom_fields_on_marked_entry`
    4. `stream_a_mcp_compat_preserves_custom_shim_command_and_args_on_marked_entry`
  * **Harness command**:
    `powershell -NoProfile -Command '$ErrorActionPreference = "Stop"; $out = cargo test --bin kbdb stream_a_mcp_compat_ | Out-String; if ($LASTEXITCODE -ne 0 -or $out -match "running 0 tests") { exit 1 }'`

### Unit 3: Support Legacy `graphtor-docs` `.gitignore` Blocks and Lock Files in Gitignore and Uninstall (`062.003-T`)

* **Source Stash ID(s)**: `6187B1EE`, `435498A0`, `4ABF7389`, `BAA98E91`
* **Domain / Width**: Rust Workspace Code (`src/workspace/gitignore.rs`, `src/workspace/uninstall.rs`)
* **Size / Complexity**: `size: S`, `complexity: low`
* **Execution Posture**: `test-first`
* **Dependencies**: `062.002-T`
* **Files Affected (2)**:
  1. `src/workspace/gitignore.rs`
  2. `src/workspace/uninstall.rs`
* **Changes**:
  * In `src/workspace/gitignore.rs` (`4ABF7389`):
    * Define `const LEGACY_GITIGNORE_ENTRY: &str = ".graphtor/";` and `const LEGACY_MARKER_HEADERS: &[&str] = &["# graphtor-docs — managed by graphtor-docs install", "# graphtor-docs - managed by graphtor-docs install"];`.
    * Add helpers `is_legacy_marker_header(line: &str) -> bool`, `is_managed_marker_header(line: &str) -> bool`, `is_kbdb_entry_line(line: &str) -> bool`, and `is_legacy_entry_line(line: &str) -> bool`, plus `legacy_graphtor_dir_exists(project_root: &Path) -> bool` (`project_root.join(".graphtor").symlink_metadata().is_ok()`).
    * Update `has_managed_gitignore_block`: return `true` when `.gitignore` contains `MARKER_HEADER` (`# kbdb — managed by kbdb install`), or when it contains a legacy marker header (`is_legacy_marker_header`) and `!legacy_graphtor_dir_exists(project_root)` (or whenever any managed marker header is present so `remove_gitignore_entry` is invoked and applies its retention guard).
    * Update `add_gitignore_entry(project_root)` (`4ABF7389`):
      * If `.gitignore` contains a legacy managed `# graphtor-docs` block and `<project_root>/.graphtor` **still exists** on disk (`legacy_graphtor_dir_exists(project_root)`), **retain** the legacy `# graphtor-docs` managed block (`.graphtor/`) in `.gitignore` alongside the new `# kbdb — managed by kbdb install` + `.kbdb/` block so retained `.graphtor/` databases, cached docs, and configuration are never exposed as untracked by `git status`.
      * If `.gitignore` contains a legacy managed `# graphtor-docs` block and `<project_root>/.graphtor` **does not exist** on disk (`!legacy_graphtor_dir_exists(project_root)`), strip the legacy `# graphtor-docs` managed block (header + immediately following `.graphtor/` or `.graphtor` line) before ensuring the `# kbdb — managed by kbdb install` + `.kbdb/` block is written.
    * Update `remove_gitignore_entry(project_root)` (`4ABF7389`):
      * Remove the `# kbdb — managed by kbdb install` managed block (header + immediately following `.kbdb/` or `.kbdb` line).
      * Remove the legacy `# graphtor-docs` managed block (header + immediately following `.graphtor/` or `.graphtor` line) **only if `<project_root>/.graphtor` does not exist on disk** (`!legacy_graphtor_dir_exists(project_root)`), retaining `.graphtor/` exclusion in `.gitignore` while `<project_root>/.graphtor` remains on disk.
      * Always preserve unmarked user-authored `.kbdb/` or `.graphtor/` lines.
  * In `src/workspace/uninstall.rs` (`BAA98E91`):
    * Add `const LEGACY_WORKSPACE_LOCK_FILE: &str = "graphtor.lock";`.
    * Update `predict_root_removal` to ignore both `WORKSPACE_LOCK_FILE` (`"kbdb.lock"`) and `LEGACY_WORKSPACE_LOCK_FILE` (`"graphtor.lock"`).
    * Update `uninstall_planned` (when `!root_is_link`) and `remove_empty_workspace_root` (before checking directory emptiness and calling `fs::remove_dir`) to remove any stale non-symlink `graphtor.lock` file inside `.kbdb/` (`let legacy_lock = workspace_dir.join(LEGACY_WORKSPACE_LOCK_FILE); if legacy_lock.is_file() && !is_symlink(&legacy_lock) { let _ = fs::remove_file(&legacy_lock); }`) alongside `kbdb.lock` during actual `uninstall`, ensuring 100% agreement between `dry_run: true` preview (`predict_root_removal` / `plan_uninstall_full`) and `dry_run: false` actual removal when `graphtor.lock` is present.
* **Verification**:
  * Add unit tests with prefix `stream_a_legacy_gitignore_` covering:
    1. `stream_a_legacy_gitignore_has_and_removes_legacy_managed_block` (in `src/workspace/gitignore.rs` — verifies removal when `.graphtor/` is absent and retention of `.graphtor/` in `remove_gitignore_entry` when `.graphtor/` still exists on disk)
    2. `stream_a_legacy_gitignore_add_migrates_or_retains_legacy_managed_block` (in `src/workspace/gitignore.rs` — verifies `add_gitignore_entry` strips `.graphtor/` when `.graphtor/` is absent on disk and retains `.graphtor/` alongside `.kbdb/` when `.graphtor/` exists on disk)
    3. `stream_a_legacy_gitignore_uninstall_cleans_legacy_gitignore_and_lock` (in `src/workspace/uninstall.rs` — verifies agreement between `plan_uninstall_full` preview `root_removal == true` and actual `uninstall` removal when a stale `graphtor.lock` is present inside `.kbdb/`)
  * **Harness command**:
    `powershell -NoProfile -Command '$ErrorActionPreference = "Stop"; $out = cargo test --bin kbdb stream_a_legacy_gitignore_ | Out-String; if ($LASTEXITCODE -ne 0 -or $out -match "running 0 tests") { exit 1 }'`

### Unit 4: Detect and Report Legacy `.graphtor/` in Doctor and Migrate Legacy `sources.yaml` in Init (`062.004-T`)

* **Source Stash ID(s)**: `6187B1EE`, `435498A0`, `ACDAB8DA`
* **Domain / Width**: Rust Workspace Code (`src/workspace/doctor.rs`, `src/workspace/init.rs`)
* **Size / Complexity**: `size: S`, `complexity: low`
* **Execution Posture**: `test-first`
* **Files Affected (2)**:
  1. `src/workspace/doctor.rs`
  2. `src/workspace/init.rs`
* **Changes**:
  * In `src/workspace/doctor.rs`:
    * Define `pub const LEGACY_GRAPHTOR_DIR: &str = ".graphtor";` and `#[must_use] pub fn detect_legacy_workspace_dir(project_root: &Path) -> Option<std::path::PathBuf>` returning `Some(legacy_dir)` when `project_root.join(LEGACY_GRAPHTOR_DIR).symlink_metadata().is_ok()`.
    * In `check_workspace_dir(workspace_dir: &Path)`: when `workspace_dir` is not a directory and `workspace_dir.parent().and_then(detect_legacy_workspace_dir)` is `Some(legacy_dir)`, include a note in the `Severity::Fail` message that a legacy `.graphtor/` directory was found at `legacy_dir.display()` and should be migrated to `.kbdb/` (e.g. via `scripts/convert-to-kbdb.ps1`) or initialized with `kbdb install`.
    * In `run_doctor(workspace_dir: &Path)`: if `workspace_dir.parent().and_then(detect_legacy_workspace_dir)` returns `Some(legacy_dir)`, push a `Check { name: "legacy-workspace-dir", severity: Severity::Warn, message: format!("legacy .graphtor/ workspace directory detected at {}; migrate to .kbdb/ (see scripts/convert-to-kbdb.ps1) or remove the stale directory", legacy_dir.display()) }`. When `.graphtor/` is absent, do not push this check so clean `.kbdb/` workspaces produce zero new checks or warnings.
  * In `src/workspace/init.rs` (`ACDAB8DA`):
    * In `init_sources_yaml(workspace_dir: &Path, force: bool)`: when `!target.exists() && !force`, check whether `workspace_dir.parent()` contains a legacy `.graphtor/config/sources.yaml` whose `.graphtor`, `.graphtor/config`, and `.graphtor/config/sources.yaml` paths are all non-reparse-points (`!graphtor_core::path::is_reparse_point(...)`) and `.graphtor/config/sources.yaml` is a regular file (`is_file()`).
    * When present, read the legacy `sources.yaml` and normalize **only** `# graphtor-docs` header comments (to `# kbdb`: specifically `# graphtor-docs sources.yaml` -> `# kbdb sources.yaml` and ``# Run `graphtor-docs sync` `` -> ``# Run `kbdb sync` ``) while preserving all YAML source `path` / `url` / `include` / `exclude` / `glob` content byte-for-byte (never rewriting `.graphtor` substrings in YAML data lines, because `init_sources_yaml` does not migrate backing data directories inside `.graphtor/`), write the copied content to `target` (`.kbdb/config/sources.yaml`), and return `Ok(InitResult { path: target, created: true })`.
* **Verification**:
  * Add 3 unit tests with prefix `stream_a_legacy_workspace_`:
    1. `stream_a_legacy_workspace_doctor_warns_when_only_legacy_graphtor_exists` (in `src/workspace/doctor.rs`)
    2. `stream_a_legacy_workspace_doctor_warns_when_legacy_graphtor_coexists_with_kbdb` (in `src/workspace/doctor.rs`)
    3. `stream_a_legacy_workspace_init_migrates_legacy_sources_yaml` (in `src/workspace/init.rs` — verifies `# graphtor-docs` header comment normalization to `# kbdb` AND byte-for-byte preservation of YAML source `path` / `url` / `glob` entries, including retained `.graphtor/...` paths)
  * **Harness command**:
    `powershell -NoProfile -Command '$ErrorActionPreference = "Stop"; $out = cargo test --bin kbdb stream_a_legacy_workspace_ | Out-String; if ($LASTEXITCODE -ne 0 -or $out -match "running 0 tests") { exit 1 }'`

## Dependency Graph

* `062.001-T` (independent — `install.sh`, `install.ps1`)
* `062.002-T` (independent — `src/workspace/mcp_config.rs`)
* `062.003-T` depends on `062.002-T` (`src/workspace/gitignore.rs`, `src/workspace/uninstall.rs` — tests full uninstall cleanup of both legacy `.gitignore` block and legacy `"graphtor-docs"` MCP config entry)
* `062.004-T` (independent — `src/workspace/doctor.rs`, `src/workspace/init.rs`)

Recommended execution order: `062.001-T -> 062.002-T -> 062.003-T -> 062.004-T`.

## Decisions and Rationale

* **Keep all `src/workspace/mcp_config.rs` changes in a single unit (`062.002-T`)**: `6187B1EE` (legacy `"graphtor-docs"` key & `x-graphtor-managed` marker) and `578B8678` (custom-field/shim preservation on marked entries) both modify `generate_mcp_config` in `src/workspace/mcp_config.rs`. Combining them into a 1-file task eliminates cross-task merge conflicts and guarantees 100% disjoint file ownership across all 4 tasks.
* **Preserve custom fields and custom wrapper commands on marked entries while still refreshing standard managed binary paths**: Distinguishing standard managed binary commands (`kbdb[.exe]`, `graphtor-docs[.exe]`, `.kbdb/bin/kbdb[.exe]`, `.graphtor/bin/graphtor-docs[.exe]`) from custom wrapper/shim commands (`bun`, etc.) lets `kbdb install` upgrade standard binary paths across the rename while preserving custom keys (`type`, `tools`, `env`, `cwd`) and custom wrapper shims (`578B8678`).
* **Retain `.graphtor/` in `.gitignore` whenever `<project_root>/.graphtor` still exists on disk (`4ABF7389`)**: Stripping `.graphtor/` from `.gitignore` during `add_gitignore_entry` or `remove_gitignore_entry` while a legacy `.graphtor/` directory remains on disk would expose its databases, cached docs, and configuration as untracked in `git status`. Both functions therefore retain the legacy `# graphtor-docs` / `.graphtor/` block whenever `<project_root>/.graphtor` exists on disk and strip it only when `<project_root>/.graphtor` is absent.
* **Keep `graphtor.lock` preview and actual removal consistent (`BAA98E91`)**: Because `predict_root_removal` ignores `graphtor.lock` alongside `kbdb.lock`, actual `uninstall` (`uninstall_planned` / `remove_empty_workspace_root`) also removes any stale non-symlink `graphtor.lock` inside `.kbdb/` so `dry_run: true` preview (`predict_root_removal`) and `dry_run: false` execution always agree.
* **Normalize only `# graphtor-docs` header comments when copying legacy `sources.yaml` (`ACDAB8DA`)**: Because `init_sources_yaml` does not move or migrate backing documentation directories inside `.graphtor/`, rewriting `.graphtor` substrings in YAML source `path` / `url` / `glob` values would break references to retained files. Normalizing only `# graphtor-docs` header comments to `# kbdb` preserves all YAML source entries byte-for-byte.
* **Emit `legacy-workspace-dir` in `doctor.rs` only when `.graphtor/` exists**: Preserves the zero-warning contract of `doctor_on_minimal_layout_reports_no_fail_or_warn` and all existing `doctor` tests on clean `.kbdb` workspaces.

## Risks and Caveats

* **Reparse-point containment across legacy `.graphtor/` reads**: `init_sources_yaml` must check `is_reparse_point` on `.graphtor`, `.graphtor/config`, and `.graphtor/config/sources.yaml` before reading so a planted symlink or junction at `.graphtor` cannot disclose an external file into `.kbdb/config/sources.yaml` (Constitution Principles III/IV).
* **Binary target test invocation**: All `src/workspace/*` unit tests reside in the `kbdb` binary target (`--bin kbdb`), not `--lib`.

## Plan Hardening Signals (REQUIRED)

* **public API, schema, or contract change**: present (narrow) — extends `.mcp.json` generation/pruning contract, `.gitignore` block recognition, `doctor` check list (when `.graphtor/` exists), `init` legacy config migration, and public installer archive fallback.
* **security, auth, permission, or compliance-sensitive behavior**: present (narrow) — touches `mcp_config.rs`, `gitignore.rs`, `uninstall.rs`, and `init.rs`, which enforce workspace reparse-point containment (`is_reparse_point`, `validate_path`) and installer `SHA256SUMS` verification.
* **migration, backfill, destructive data/config action, or irreversible step**: present (narrow) — migrates legacy `"graphtor-docs"` MCP keys, legacy `.gitignore` blocks, and legacy `.graphtor/config/sources.yaml` files, and enables `uninstall` to prune legacy `"graphtor-docs"` MCP entries and `.gitignore` blocks.
* **external integration, operator checkpoint, or external dependency**: absent — all verification is self-contained in unit tests and local script checks.
* **high runtime, rollout, or rollback risk**: absent — changes are confined to installer scripts and workspace CLI helpers (`mcp_config`, `gitignore`, `uninstall`, `doctor`, `init`), with no changes to MCP STDIO transport or CozoDB/Candle query execution.

Requires plan hardening: yes

## Plan Hardening

* **Why hardening was invoked**: `strict_safety.enabled: true` is active in `.autoharness/config.yaml`, and the plan touches security-sensitive containment boundaries (`mcp_config.rs`, `gitignore.rs`, `uninstall.rs`, `init.rs`) and public installer checksum/download flows (`install.sh`, `install.ps1`).
* **Protected invariants**:
  1. **Installer SHA-256 verification (`docs/compound/best-practices/installer-checksum-empty-grep-pattern-2026-05-08.md`)**: Fallback to `graphtor-docs-<version>-<target>.(tar.gz|zip)` must still verify the downloaded archive against `SHA256SUMS` and fail closed on missing, multiple, or mismatched hashes before extracting any binary.
  2. **Workspace reparse-point containment (`docs/compound/best-practices/reparse-point-fail-closed-containment-2026-07-16.md`, Constitution Principles III/IV)**:
     * `mcp_config.rs` must keep `is_reparse_point(&dest)`, `validate_path`, exclusive temp-file creation (`create_new`), and Unix `0600` permission preservation unchanged.
     * `gitignore.rs` must keep `is_reparse_point(&path)` on read and write paths.
     * `init.rs` must check `!is_reparse_point` on `.graphtor`, `.graphtor/config`, and `.graphtor/config/sources.yaml` before reading a legacy `sources.yaml`.
  3. **Collision fail-closed invariant in `mcp_config.rs`**: An unmarked `"kbdb"` entry that does not match `is_exact_legacy_shape` must still return `ExistingEntryClass::Collision` (`Err(GraphtorError::Config)`), leaving `.mcp.json` byte-for-byte untouched.
* **Risky Action Classification (`strict-safety`)**:
  * `ProposedAction` 1 (`062.001-T` — installer archive/binary fallback):
    * `targets`: `install.sh`, `install.ps1`
    * `change_kind`: release asset download fallback (`kbdb-...` -> `graphtor-docs-...`)
    * `ActionRisk`: `low` (additive fallback on HTTP failure; mandatory `SHA256SUMS` verification preserved before extraction)
    * `rollback`: `git revert <commit>`
    * `approval_required`: pre-authorized in operator Batch 2 prompt (`0BD7D83C`)
    * `ActionResult`: `planned`
  * `ProposedAction` 2 (`062.002-T`, `062.003-T`, `062.004-T` — legacy workspace migration & custom-shape preservation):
    * `targets`: `src/workspace/mcp_config.rs`, `src/workspace/gitignore.rs`, `src/workspace/uninstall.rs`, `src/workspace/doctor.rs`, `src/workspace/init.rs`
    * `change_kind`: backward-compatible workspace config migration and custom-key preservation
    * `ActionRisk`: `low` (preserves all unmarked user entries and reparse-point guards; covered by dedicated unit tests in `--bin kbdb`)
    * `rollback`: `git revert <commit>`
    * `approval_required`: pre-authorized in operator Batch 2 prompt (`6187B1EE`, `578B8678`)
    * `ActionResult`: `planned`
* **Review-gate capability notes**: Under P-012, `plan-review` must emit literal `dispatch_mode:` and `decision:` markers and evaluate all triggered personas from the Persona Rubric Adapter, including `Security Lens Reviewer` and `Agent-Native Parity Reviewer`.

## Runtime Verification and Closure

* **Runtime surface impact**:
  * Public installer scripts (`install.sh`, `install.ps1`) and CLI workspace management subcommands (`kbdb install`, `kbdb uninstall`, `kbdb doctor`, `kbdb init`).
  * Does **not** modify `kbdb serve` MCP STDIO transport, database schema, or query execution.
* **Verification**:
  * Red/green execution of each task's single-quoted `Harness command:` (`062.001-T`..`062.004-T`).
  * Full Rust quality gates: `cargo check --all-targets`, `cargo fmt --all -- --check`, `cargo clippy --all-targets -- -D warnings -D clippy::pedantic`, `cargo test --all-targets` (with default OS `TEMP`/`TMP`), and CI allowlist `cargo audit`.
* **Operational closure expectations**:
  * Post-merge closure (`operational-closure` skill) records `057-S` / `062-F` with build/test/audit and installer syntax verification evidence, owner `@softwaresalt`, and `git revert` as the rollback path.

## Plan Review

```text
dispatch_mode: single-agent-declared-degradation
decision: PASS
```

* **Capability declaration (P-012)**: `TOOL_DEGRADED: reviewer-subagent-dispatch — declared fallback: single-agent persona pass`.
  * **Rationale**: Stage's runtime tool contract (`<tools><task>`) mandates handling reviews whose total evidence fits a direct read inline without delegating by persona/angle. Per `.github/skills/plan-review/SKILL.md` (`## Dispatch Capability and Declared Degradation`, Step 2), Stage applies every triggered persona rubric inline and records `dispatch_mode: single-agent-declared-degradation`.
* **Hardening check (P-006 / strict-safety)**: `Requires plan hardening: yes` is present, and `## Plan Hardening` classifies both `ProposedAction` groups with `ActionRisk`, protected invariants, and rollback instructions.

### Persona Coverage Table

| Persona | Trigger Status | Mode | Findings |
|---|---|---|---|
| Constitution Reviewer | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Rust Reviewer | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Scope Boundary Auditor | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Learnings Researcher | Always-on | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Architecture Strategist | Cross-model (Always) | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Agent-Native Parity Reviewer | Triggered (MCP config / CLI doctor/init) | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |
| Security Lens Reviewer | Triggered (installer SHA256 + workspace containment) | Inline rubric pass (`single-agent-declared-degradation`) | 0 (`P0: 0, P1: 0, P2: 0, P3: 0`) |

### Per-Persona Findings

* **Constitution Reviewer**: `0` findings. Includes a dedicated `## Constitution Check` section (`435498A0`) mapping Principles I–XI (`constitution.instructions.md:331-334`) with zero violations. All 4 units enforce Constitution Principles III and IV (workspace containment via `is_reparse_point` and `validate_path`), Rust 2021 / MSRV `1.88` compatibility (`#![forbid(unsafe_code)]`), P-003 granularity (`1–2` files per task), and P-010 role boundaries.
* **Rust Reviewer**: `0` findings. Unit tests in `src/workspace/*` are correctly targeted via `cargo test --bin kbdb <prefix>`, error handling uses `Result<_, GraphtorError>` without `.unwrap()` in production code, `serde_json` `preserve_order` is leveraged in `refresh_marked_server_value` to preserve key ordering, `uninstall.rs` removes stale `graphtor.lock` during actual `uninstall` so `predict_root_removal` preview and execution agree (`BAA98E91`), `gitignore.rs` retains `.graphtor/` when `<project_root>/.graphtor` exists on disk (`4ABF7389`), and `init.rs` normalizes only `# graphtor-docs` header comments while preserving YAML source `path` / `url` / `glob` content byte-for-byte (`ACDAB8DA`).
* **Scope Boundary Auditor**: `0` findings. Strictly bounded to Stream A (`0BD7D83C`, `6187B1EE`, `578B8678`) and its 6 PR #153 review refinements (`C8CCC000`, `435498A0`, `1E585DFF`, `4ABF7389`, `BAA98E91`, `ACDAB8DA`). Stream C entries (`ECD56875`, `AC2E02C0`, `787C92F9`, `8EFB7D92`, `FF798FA3`), dark-run captures (`150A478A`, `E4B2B0B3`), and `059-F` / `013.008-T` / `060-F` are untouched.
* **Learnings Researcher**: `0` findings. Incorporates `installer-checksum-empty-grep-pattern-2026-05-08.md`, `reparse-point-fail-closed-containment-2026-07-16.md`, `backlogit-level1-id-collision-across-parent-types.md`, Batch 1 (`056-S`) execution learnings (`--bin kbdb`, default OS `TEMP`/`TMP`, and CI allowlist `cargo audit`), and literal PowerShell `.Contains` checks in `062.001-T` (`1E585DFF`).
* **Architecture Strategist**: `0` findings. File ownership across `062.001-T`..`062.004-T` is 100% disjoint (`install.sh`+`install.ps1`; `mcp_config.rs`; `gitignore.rs`+`uninstall.rs`; `doctor.rs`+`init.rs`), with an explicit `blocks` dependency edge from `062.002-T` to `062.003-T`.
* **Agent-Native Parity Reviewer**: `0` findings. `doctor` (`Check` structs serialized by both Human and `--json` JSON-RPC 2.0 modes in `cmd_doctor`), `init`, `install`, and `uninstall` maintain 100% parity between human CLI output and `--json` output.
* **Security Lens Reviewer**: `0` findings. Installer fallback still requires exact `SHA256SUMS` verification before extracting any binary, and `init_sources_yaml` checks `!is_reparse_point` on `.graphtor`, `.graphtor/config`, and `.graphtor/config/sources.yaml` before reading legacy config content.

### Gate Verdict

* **Merged counts**: `0 P0, 0 P1, 0 P2, 0 P3`
* **Gate decision**: `PASS` — ready for `harvest` into `062-F` and `062.001-T`..`062.004-T` and Mode H shipment assembly into `057-S`.
