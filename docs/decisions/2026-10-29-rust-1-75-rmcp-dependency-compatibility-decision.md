---
title: "Resolve rmcp dependency compatibility via constitutional MSRV 1.88 amendment (056.029-T / 053-S)"
description: "Empirical Cargo 1.75.0 evidence and operator-approved constitutional MSRV amendment raising rust-version from 1.75 to 1.88 while preserving edition 2021"
doc_type: "decision"
topic: "Rust MSRV 1.88 amendment for the rmcp and candle dependency graph"
depth: "lightweight"
decision_status: "approved"
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
  - rust-1-88
---

## Decision

Empirical measurements under `cargo +1.75.0` and `rustc 1.75.0` proved that no
published `rmcp` release (`0.1.1` through `3.8.0`), lockfile pin, or
manifest-only patch yields a buildable Rust 1.75 dependency graph alongside
`candle 0.8`. On 2026-10-29, after reviewing this empirical evidence, the
operator explicitly selected and authorized **Option 1**: a constitutional MSRV
amendment raising `rust-version` from `"1.75"` to **`"1.88"`** while preserving
`edition = "2021"`.

Under this approved amendment:

* `056.029-T` updates root `Cargo.toml` (`[workspace.package]`) to
  `rust-version = "1.88"` (preserving `edition = "2021"`), keeps the locked
  dependency graph (`Cargo.lock`), and validates buildability with
  `cargo +1.88.0 check --all-targets --locked` and `cargo test --no-run`.
* `056.030-T` enforces the Rust `1.88.0` MSRV floor in primary CI
  (`.github/workflows/ci.yml`).
* `056.031-T`, `056.032-T`, and `056.033-T` align public documentation
  (`README.md`, `docs/ARCHITECTURE.md`), canonical agent and constitutional
  declarations (`AGENTS.md`, `.github/copilot-instructions.md`,
  `.github/instructions/constitution.instructions.md`), and Rust authoring
  instructions (`.github/instructions/rust.instructions.md`,
  `.github/instructions/technology.instructions.md`,
  `.github/instructions/technology-rust.instructions.md`) to `rust-version =
  "1.88"`.
* Stash `6C174AA9` (`globset 0.4.18` under Rust 1.75) is resolved and archived
  by this MSRV `1.88` amendment.

## Operator Decision (2026-10-29)

On `2026-10-29T17:46:17.044-07:00`, the operator reviewed the empirical Cargo
`1.75.0` findings recorded below and authorized **Option 1**:

> "Option 1: Authorize a constitutional MSRV amendment raising `rust-version`
> from `1.75` to `1.85`–`1.88` so `053-S` and `052-S` can ship."

Across `Cargo.lock` (`cargo metadata`), the exact minimum Rust version required
by the locked workspace dependency graph is **`1.88.0`** (preserving
`edition = "2021"`):

* `darling 0.23.0`, `darling_core 0.23.0`, and `darling_macro 0.23.0` (pulled
  by `rmcp-macros 1.5.0`) declare `rust-version = "1.88.0"`.
* `wit-bindgen 0.51.0` declares `rust-version = "1.87.0"`.
* `clap 4.6.1`, `tokio 1.54.1`, `rmcp 1.5.0`, and `globset 0.4.18` require
  `rust-version = "1.85"` / Cargo `edition2024` support.
* `cargo-audit >= 0.22` also requires `rustc 1.88+`.

Raising the constitutional floor to `rust-version = "1.88"` (with `edition =
"2021"` unchanged) resolves the dependency blocker without a third-party crate
fork or disruptive `rmcp`/`candle` replacement, unblocking `053-S`
(`056.029-T` through `056.033-T`) and `052-S` (`056.011-T`).

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
is not attainable through `Cargo.toml`, `Cargo.lock`, or a decision record
alone. Both `rmcp` and `candle` independently break it. Three options were
evaluated:

1. **Selected and approved (2026-10-29):** Raise `rust-version` to `"1.88"`
   (preserving `edition = "2021"`) via a constitutional MSRV amendment. The
   measured minimum across `Cargo.lock` is `rustc 1.88.0` for `darling 0.23.0`
   (via `rmcp-macros 1.5.0`), with `wit-bindgen 0.51.0` at `1.87.0` and
   `rmcp 1.5.0`/`globset 0.4.18`/`tokio 1.54.1`/`clap 4.6.1` at `1.85`.
2. **Rejected:** Replace the `rmcp` dependency and downgrade `candle` with
   source and API migration.
3. **Rejected:** Maintain a forked `rmcp` and `candle` stack at Rust 1.75.

## Verification Evidence (056.029-T)

After setting `rust-version = "1.88"` in the root `Cargo.toml` (edition kept at
`2021`, `Cargo.lock` unchanged), the locked dependency graph was verified with
`rustc 1.88.0 (6b00bc388 2025-06-23)` on 2026-10-29:

| Command | Result |
|---|---|
| `cargo +1.88.0 check --all-targets --locked` | Pass (`Finished dev profile`, 2m 33s) |
| `cargo +1.88.0 test --no-run --locked` | Pass (`Finished test profile`, 4m 50s, all test executables built) |

## Rollback

To roll back `056.029-T` through `056.033-T`, revert the `rust-version = "1.88"`
manifest, workflow, documentation, and instruction commits in `053-S` as a unit.

## Stage Ratification Summary

Stage updated the `053-S` (`056.029-T` through `056.033-T`) and `052-S`
(`056.011-T`) task and shipment contracts to execute the operator-approved
`rust-version = "1.88"` constitutional amendment and archived superseded stash
entry `6C174AA9`.
