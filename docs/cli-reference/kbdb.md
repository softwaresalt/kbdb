---
title: kbdb CLI Reference
description: "Complete reference for all kbdb subcommands, global flags, and exit codes"
---

```text
kbdb [GLOBAL FLAGS] <SUBCOMMAND> [SUBCOMMAND FLAGS]
```

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success — all operations completed without error |
| `1` | Partial failure — some files failed; others succeeded |
| `2` | Fatal error — pipeline stage failed, database unavailable, config invalid, etc. |

## Global Flags

These flags are accepted by every subcommand.

| Flag | Short | Env var | Default | Description |
|---|---|---|---|---|
| `--verbose` | `-v` | — | off | Enable debug-level logging |
| `--json` | — | — | off | Wrap all output in JSON-RPC 2.0 envelopes (`{"jsonrpc":"2.0","id":null,"result":{...}}`) |
| `--config <FILE>` | `-c` | `KBDB_SOURCES` | `.kbdb/config/sources.yaml` | Path to `sources.yaml` |
| `--db-path <FILE>` | `-d` | `KBDB_DB_PATH` | `.kbdb/graph.db` | Path to the primary CozoDB database |

> [!NOTE]
> `--data-dir` is a deprecated alias for `--db-path`. It still works
> but prints a warning. Use `--db-path` in new invocations.
>
> Sources can override the primary database target with the `database` field in
> `sources.yaml`. Those sources sync into sibling `.db` files under the same
> parent directory as `--db-path`.

## Subcommands

### `sync`

Run the ingestion pipeline.

```text
kbdb sync [FLAGS]
```

By default, detects changes since the last sync (via file mtime) and
re-processes only added, modified, and deleted files. Use `--full` to
force a complete acquire → validate → parse → embed → load cycle.

| Flag | Default | Description |
|---|---|---|
| `--full` | off | Force full re-ingestion of all files; ignores sync state |
| `--no-embed` | off | Skip the embedding step (faster; no vectors stored; `search_semantic` returns empty results) |
| `--batch-size <N>` | `20` | Number of files to process per parse/embed/load cycle |
| `--data-root <DIR>` | `.kbdb/data` | Root directory for acquired source files |

### `serve`

Start the MCP STDIO server.

```text
kbdb serve [--read-only]
```

Binds to STDIO (localhost only) and serves the 8 kbdb MCP tools.
Blocks until stdin closes (i.e., until the MCP client disconnects).

`serve` auto-discovers the databases to open as the union of: any
`sources.yaml`-resolved target (including an explicit `--db-path`), any
explicit `type: database` entry, and any `.db` file dropped directly inside
`.kbdb/` — no configuration is required to serve a dropped database.

### `status`

Print database statistics.

```text
kbdb status [FLAGS]
```

Reports registered sources, their kind (`local`), path, and last-sync
timestamp. If the database does not exist, prints a helpful message and exits
with code `0`.

### `init`

Generate a template `sources.yaml`.

```text
kbdb init [FLAGS]
```

Creates `.kbdb/config/sources.yaml` with commented examples for local
docline sources. Does **not** overwrite an existing file unless `--force` is
passed.

### `install`

Install kbdb into the current workspace.

```text
kbdb install [FLAGS]
```

By **default**, `install` creates a consumption-first minimal footprint:

```text
.kbdb/        ← workspace root; drop an already-generated `.db` file here
              for `serve`/`status` to auto-discover with zero configuration
```

Pass `--with-ingestion` to create the full, ingestion-capable scaffold:

```text
kbdb install --with-ingestion
```

This creates `.kbdb/{bin,data,cache,config,logs}/`, copies the running binary
to `.kbdb/bin/kbdb`, writes a starter `.kbdb/config/sources.yaml`, adds
`.kbdb/` to `.gitignore` (unless `--no-gitignore`), and registers `kbdb` in
`.mcp.json`.

### `doctor`

Diagnose workspace health.

```text
kbdb doctor
```

### `upgrade`

Upgrade the installed kbdb binary.

```text
kbdb upgrade [FLAGS]
```

Replaces `.kbdb/bin/kbdb` with the currently running binary.

### `uninstall`

Remove kbdb from the current workspace.

```text
kbdb uninstall --confirm [FLAGS]
```

### `manifest`

Print a manifest of available MCP tools.

```text
kbdb manifest [--json]
```
