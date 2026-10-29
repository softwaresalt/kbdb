---
title: "No Cargo-only dependency strategy satisfies Rust 1.75 with rmcp (056.029-T / 053-S)"
description: "Empirical Cargo 1.75.0 evidence that no published rmcp release, pin, or manifest-only patch yields a buildable Rust 1.75 graph, and the blocked disposition required by 056.029-T"
doc_type: "decision"
topic: "Rust 1.75 MSRV compatibility of the rmcp dependency graph"
depth: "lightweight"
decision_status: "blocked-pending-operator-decision"
backlog_refs:
  - "053-S"
  - "056.029-T"
  - "056.030-T"
  - "056.031-T"
  - "056.032-T"
  - "056.033-T"
  - "056.011-T"
  - "052-S"
linked_artifacts:
  - "docs/decisions/2026-08-29-mcp-serve-discover-preinitialize-evidence.md"
  - "docs/exec-plans/2026-08-21-mcp-serve-initialize-handshake-regression-plan.md"
tags:
  - msrv
  - rmcp
  - cargo
  - rust-1-75
---

## Decision

`056.029-T` cannot select an MSRV-compatible dependency strategy inside its
file ownership (`Cargo.toml`, `Cargo.lock`, one decision record). Every
candidate was measured with Cargo and rustc 1.75.0. None produces a graph that
parses and builds without source or API migration, a deep fork of third-party
crates, or a change to the `rust-version = "1.75"` floor. This record applies
the governed disposition from the task: `Cargo.toml`, `Cargo.lock`, `src/**`
and `rust-version` are left unchanged, and `056.029-T` and `053-S` remain
blocked pending a named bounded follow-up and an operator decision.

## Evidence

All measurements ran on 2026-10-29 with toolchains `1.75.0` and stable `1.97.0`
on Windows (`x86_64-pc-windows-msvc`).

### Baseline

`cargo +1.75.0 check --locked` fails before compiling anything. The locked
`globset 0.4.18` manifest requires the unstable Cargo feature `edition2024`
(stash `6C174AA9`). Cargo 1.75 also fails on the resolved `rmcp 1.5.0` manifest.

### Candidate 1: compatible published rmcp release or pin

The `Cargo.toml` manifest of every non-yanked rmcp release was inspected:
`0.1.1` to `0.17.0`, `1.0.0` to `1.8.0`, and `2.0.0` to `2.2.0` all declare
`edition = "2024"`. Releases `3.0.0` to `3.8.0` declare `rust-version = "1.88"`.
No published release can be parsed by Cargo 1.75. Rejected.

### Candidate 2: lockfile-only repair

An MSRV-aware lockfile was resolved with
`CARGO_RESOLVER_INCOMPATIBLE_RUST_VERSIONS=fallback` on stable Cargo. It still
resolved edition-2024 crates (`globset 0.4.19`, `smawk 0.3.3`, `rmcp 1.8.0`,
`rmcp-macros 1.8.0`). Manual precise pins fixed `globset` (0.4.16) and
`smawk` (0.3.2), but `rmcp` cannot be pinned away from edition 2024.
Rejected.

### Candidate 3: manifest-only patch of rmcp 1.5.0

A scratch copy of `rmcp 1.5.0` and `rmcp-macros 1.5.0` was patched through
`[patch.crates-io]` with `edition` set to `2021`, and `rmcp-macros` pointed at
`darling 0.20` (`darling 0.23` requires rustc 1.88).

* Manifests then parse under Cargo 1.75.
* An isolated crate depending only on the patched rmcp failed with 381 rustc
  1.75.0 errors: 97 `lint reasons are experimental`, 96 unstable-attribute
  errors, 65 `cannot find trait` errors, and others. The rmcp source itself
  needs a newer compiler, so a backport would be a source-level fork of rmcp.
* The full graph (`graphtor-core`) also failed for reasons unrelated to rmcp.
  After pinning `half 2.4.1`, `candle-core/nn/transformers 0.8.3`,
  `globset 0.4.16`, and `smawk 0.3.2`, the build stopped in `pulp 0.21.4`,
  reached through `candle-core -> gemm`. Its build script emits
  `cargo::rustc-check-cfg`, which Cargo 1.75 rejects. Every `pulp` 0.21.x
  release uses that directive.

A narrow patch is therefore not feasible: it needs a full fork of rmcp
(rejected: unbounded maintenance and security-review cost) and a downgrade or
replacement of the `candle` 0.8 stack, which changes source APIs.

## Conclusion

With the current dependency set (`rmcp 1.x`, `candle 0.8`), the `1.75` floor
is not attainable through Cargo.toml, Cargo.lock, or a decision record alone.
Both `rmcp` and `candle` independently break it. The options are all outside
`056.029-T` ownership:

1. Raise `rust-version` after a separately approved constitutional amendment.
   The measured minimum is rustc 1.88 for `rmcp 3.x` and its `darling` chain;
   a lower floor needs its own measurement.
2. Replace the rmcp dependency and downgrade candle with source and API
   migration, as a named bounded follow-up.
3. Maintain a forked rmcp and candle stack at Rust 1.75 (not recommended).

## Rollback

No repository change was made by this task other than this record, so there is
nothing to roll back. Scratch experiments lived in the OS temp directory.

## Follow-up handoff for Stage

Stage owns creating the bounded follow-up and the operator decision between
options 1 to 3. `056.030-T` to `056.033-T` stay blocked on `056.029-T`.
