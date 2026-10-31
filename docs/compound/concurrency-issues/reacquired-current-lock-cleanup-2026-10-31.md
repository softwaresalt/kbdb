---
title: Preserve a current workspace lock reacquired after uninstall release
description: Empty-root cleanup must not unlink a new writer's current lock.
source: docs/compound/concurrency-issues/reacquired-current-lock-cleanup-2026-10-31.md
doc_type: learning
problem_type: lock_reacquisition_race
category: concurrency-issues
component: workspace uninstall
root_cause: Cleanup treated a current lock pathname as disposable after ownership ended.
resolution_type: code_fix
severity: high
message: A reacquired current lock must keep the workspace alive.
file_path: src/workspace/uninstall.rs
citations:
  - "PR #155"
  - "src/workspace/uninstall.rs"
  - "docs/closure/057-S-062-F-post-merge-closure.md"
  - "3c790d877c7ce5fc408419b85c66ed8ff3d0d8cd"
tags:
  - uninstall
  - workspace-lock
  - reacquisition
  - legacy-compatibility
  - preview-parity
---

## Problem

In 057-S / 062-F task 062.003-T, uninstall released its advisory lock before
empty-root cleanup. A concurrent installer could acquire a new `kbdb.lock`
in that interval. Cleanup could then unlink the new owner's lock and remove
the workspace beneath that owner.
Copilot identified the defect in PR #155; P-021 C1 classified remediation as
completion of the authorized safe cleanup contract.

## Root Cause

Releasing the caller's lock ends its ownership; the same pathname can now
represent another writer. Neither the expected filename nor a previously
empty directory proves that cleanup still owns the current lock.
Legacy lock files also require ownership evidence, not filename-only removal.

## Resolution

Fix `3c790d877c7ce5fc408419b85c66ed8ff3d0d8cd` changed
`src/workspace/uninstall.rs`:

* `remove_empty_workspace_root` never unlinks a current `kbdb.lock`
* A current lock observed after release blocks cleanup, including immediately
  before a legacy unlink
* `stale_legacy_lock_token` accepts only regular, non-reparse legacy
  `graphtor.lock` files with a valid, unambiguous, nonzero PID and dead owner
* Legacy unlink revalidates file type, owner liveness, and the exact scanned
  token; missing, malformed, changed, or live ownership blocks cleanup
* Preview and execution share the legacy-staleness predicate; preview may
  ignore the caller's current lock because the caller will release it
* Final emptiness checks and nonrecursive removal retain concurrently
  repopulated roots instead of deleting their contents

Two focused regressions were observed red before production edits: live or
unknown legacy ownership, and current-lock reacquisition after caller release.
All eleven Unit 3 tests then passed, followed by full fmt, pedantic clippy,
all-target tests, eleven-ignore CI audit, cargo check, and cargo build.
Three-model remediation review passed; Copilot's thread was replied to and
resolved before the current-HEAD readiness gate passed.

## Prevention

Treat a released lock's pathname as unowned. Do not reacquire through a
stale-reclaiming API merely to clean up, and never unlink a current/live lock.
Require dead-owner evidence plus token revalidation for legacy cleanup.
Test ownership handoff explicitly, and preserve preview/execution parity.
These checks narrow races; they do not turn a scan into an atomic filesystem
transaction.

See [the source](../../../src/workspace/uninstall.rs) and
[canonical closure](../../closure/057-S-062-F-post-merge-closure.md).
Indexed duplicate-learning discovery was unavailable in this bounded capture;
no equivalent-learning claim or unrelated documentation edit was made.
