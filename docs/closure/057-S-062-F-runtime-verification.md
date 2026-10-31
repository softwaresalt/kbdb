---
title: "057-S / 062-F runtime verification"
shipment: 057-S
feature: 062-F
source_head: 66dfd172510120a81a1cbce1e24294a848a37f24
verified_at: 2026-10-31T20:33:02Z
surface: cli
adapter: command
mode: auto
verdict: PASS_WITH_FOLLOW_UP
---

## Scope and prechecks

* Workspace: `C:\Source\GitHub\kbdb`
* Artifact: `target\debug\kbdb.exe`, reporting server version `0.3.1`
* Source HEAD confirmed before and after probes
* Parent reports quality gates and full cargo build passed
* Contract: `runtime_validation` in
  `.autoharness\workspace-profile.yaml`
* Skills: runtime-verification, then operational-closure in pre-merge mode
* OS TEMP/TMP unchanged for all commands and subprocesses
* No source, installer, real init, sync, or uninstall execution
* No direct edits to actual `.kbdb` or `.graphtor` state
* Serve probes forced `--read-only`; background sync was skipped
* No scratch files created; both client subprocesses exited

The profile's legacy `graphtor-docs` release commands were adapted to the
parent-built `kbdb` debug executable. Windows subprocess EOF replaces the
profile's `/dev/null` redirection. This selects the command adapter without
starting a write-capable server or rebuilding release artifacts.

## Validator evidence

| Probe | Command | Native exit | Verdict |
| --- | --- | --- | --- |
| cli-status | `.\target\debug\kbdb.exe status` | 0 | PASS |
| doctor | `.\target\debug\kbdb.exe doctor` | 0 | PASS_WITH_FOLLOW_UP |
| mcp-stdio-startup | `.\target\debug\kbdb.exe serve --read-only`, stdin EOF | 2 | PASS |
| handshake driver | `cargo test --test serve_handshake_driver_test` | 0 | PASS |
| Stream A library selector | `cargo test --lib stream_a` | 0 | No coverage |
| Stream A binary selector | `cargo test --bin kbdb stream_a` | 0 | PASS |
| external client attempt 1 | Python STDIO subprocess, 60-second status bound | 1 | Timeout |
| external client attempt 2 | Python STDIO subprocess, extended status bound | 0 | PASS |

### CLI status and doctor

Status opened three databases read-only and reported seven registered
sources across `powerbi.db`, `eraser-io.db`, and `mermaid.db`.
CLI status does not display schema version in this invocation; the live
MCP status below confirms schema 4.

Doctor reported workspace directories, installed binary, and valid
sources YAML as PASS. It reported a WARN that the default database has
not been created and suggested sync. Discovered indexed databases are
present, so this warning is not evidence that all indexes are absent.
No sync was run to suppress the warning.

### Startup and handshake

Python `subprocess.run` supplied an empty string to stdin, captured output,
and imposed a 60-second bound. The child returned native exit 2 with empty
stdout and:

```text
starting MCP STDIO server
error: MCP server failed to start
Caused by:
  connection closed: initialize request
```

The wrapper returned 0 because that exit and diagnostic match the profile's
expected no-initialize behavior. This probe alone is not handshake evidence.

The required handshake driver passed all four tests in 0.45 seconds.
It covered successful initialize, empty-workspace diagnostics, protocol-clean
stdout, live tool/get_status parity, and forced read-only serving with a
configured real source. Its fixtures are not real indexed-source search
evidence.

### Legacy compatibility evidence

The first selector matched zero tests because workspace modules belong to
the binary, not the library. The corrected binary selector passed all 16
Stream A tests in 0.67 seconds:

* Two legacy-only/coexisting workspace doctor warning tests
* One legacy sources YAML migration test
* Four MCP key, stale-entry, custom-field, and wrapper/argument tests
* Four managed gitignore migration/preservation tests
* Five uninstall cleanup and lock safety tests

These are fixture-based tests, not installation or destructive removal from
the actual environment. No real workspace migration was attempted.

## External client checkpoint

Checkpoint `mcp-client-smoke`: completed by an actual local Python client
using JSON-RPC over the built binary's STDIO transport. This is observed
automation evidence, not an assumed operator confirmation.

The client launched:

```text
.\target\debug\kbdb.exe serve --read-only
```

It used reader threads for stdout/stderr, matched JSON-RPC response IDs,
and closed stdin after the requests. Attempt 2 allowed 180 seconds for
get_status and 40 seconds for each search. Initialize and tools/list had
30-second bounds; child shutdown had a 10-second bound.

| Request | Parameters or result | Outcome |
| --- | --- | --- |
| initialize | protocolVersion `2024-11-05`, empty capabilities | Negotiated `2024-11-05` |
| initialized notification | `notifications/initialized` | Server accepted |
| tools/list | Eight canonical names | PASS |
| get_status | sources 7, chunks 68714, schema 4, auto-sync idle | PASS, 42.32 seconds |
| search_local_docs | query `flowchart`, source_id `mermaid`, top_k 3 | PASS, 2.31 seconds |
| search_semantic | query `How to draw a flowchart with nodes and arrows`, top_k 3 | PASS, 5.91 seconds |
| client shutdown | stdin closed | Server exit 0 |

Both searches returned three actual indexed hits, with `isError: false`
and no JSON-RPC error. Semantic search has no source filter in its schema;
the second request correctly searched all indexed databases.

Keyword hits referenced `syntax/flowchart.md` and
`docs/syntax/flowchart.md`, with Odd, An open link, and Parallelogram
headings. Their returned snippets contained Mermaid flowchart syntax.

Semantic hits covered Power BI troubleshooting flowchart steps, Eraser
flow-chart Nodes, and Mermaid Multi directional arrows. The latter two
included node/shape definitions and directional-arrow examples. These
results demonstrate relevant content and shaped results, not a comprehensive
ranking-quality benchmark.

One reproducible Mermaid semantic result:

```text
Chunk ID: 598bcf8d9a4fcfc7ed8136b5e7e9fe8f46263d8d96735942047dab6464a78a52
Source: syntax/flowchart.md
Heading: Flowcharts - Basic Syntax > Multi directional arrows
```

The eight advertised tools were get_chunk_by_id, get_document, get_status,
list_sources, research_topic, search_local_docs, search_semantic, and
traverse_doc_links. The local embedding model loaded successfully; no model
download or semantic omission was needed.

### Failed attempt and bounded recovery

Attempt 1 initialized successfully and listed the eight tools, then
get_status exceeded 60 seconds. Python returned 1; its child returned 0
after stdin closure and logged a five-second in-flight drain timeout.
No search was sent in that attempt.

Attempt 2 completed the same status and both searches in 50.85 seconds
overall. The earlier timeout remains a latency follow-up; its cause was not
established. No production fix or third retry was attempted.

## Invariants and limitations

* Schema 4, eight tools, and protocol negotiation observed
* Read-only posture observed for all three actual databases
* No background ingestion, migration, or index rebuild performed
* Stream A migration and preservation behavior validated in fixtures
* General traversal, symlink/reparse, and pre-v4 rejection coverage relies
  on the parent's passed quality gates, not new runtime mutation probes
* External checkpoint has no blocked model, database, or client prerequisite
* Installed editor-client configuration and installer release fallback were
  not exercised against the real environment
* Operator observation after merge remains outstanding

## Risk and closure handoff

ProposedAction: read-only CLI/MCP probes and existing fixture tests.
ActionRisk: low. Approval required: no destructive action planned.
ActionResult: applied. Actual workspace migration, installation, and uninstall
were excluded; their real-environment approval remains outside this scope.

Runtime verdict: `PASS_WITH_FOLLOW_UP`.
No profile-defined runtime release blocker was observed. Latency,
doctor warning disposition, parent review readiness, source provenance
reconciliation, and the first post-merge observation remain closure conditions.

Monitoring owner: `softwaresalt`. Validation window: first post-merge
invocation through completion of status, doctor, and the three MCP calls,
with a 30-minute observation budget. Investigate one status request exceeding
60 seconds; treat a 180-second timeout as failed validation.

Rollback trigger: one confirmed instance of data loss or managed config
corruption. Rollback is an operator-controlled revert PR, preserving indexes
and configs; no automated deletion, rebuild, or revert was authorized.

See [pre-merge closure](057-S-062-F-pre-merge-closure.md).
