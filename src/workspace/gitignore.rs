//! `.gitignore` management for the workspace installation.
//!
//! Appends `.kbdb/` to the project `.gitignore` during install and
//! removes the entry during uninstall. Both operations are idempotent.

use std::fs;
use std::path::Path;

use graphtor_core::path::is_reparse_point;
use graphtor_core::GraphtorError;

/// The gitignore entry managed by kbdb.
const GITIGNORE_ENTRY: &str = ".kbdb/";

/// Marker comment written before the managed entry.
const MARKER_HEADER: &str = "# kbdb — managed by kbdb install";

const LEGACY_GITIGNORE_ENTRY: &str = ".graphtor/";
const LEGACY_MARKER_HEADERS: &[&str] = &[
    "# graphtor-docs — managed by graphtor-docs install",
    "# graphtor-docs - managed by graphtor-docs install",
];

#[must_use]
fn is_legacy_marker_header(line: &str) -> bool {
    LEGACY_MARKER_HEADERS.contains(&line.trim())
}

#[must_use]
fn is_entry_line(line: &str, entry: &str) -> bool {
    line.trim() == entry || line.trim() == entry.trim_end_matches('/')
}

#[must_use]
fn legacy_graphtor_dir_exists(project_root: &Path) -> bool {
    // Retain exclusions even for dangling links or inaccessible legacy roots:
    // only proven absence permits stripping the old block.
    !matches!(
        fs::symlink_metadata(project_root.join(".graphtor")),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound
    )
}

/// Strip only marker-adjacent entries, retaining all unmarked user lines.
#[must_use]
fn strip_managed_blocks(existing: &str, remove_current: bool, retain_legacy: bool) -> String {
    let mut lines = existing.lines().peekable();
    let mut kept = Vec::with_capacity(existing.lines().count());
    let mut changed = false;
    while let Some(line) = lines.next() {
        let entry = if remove_current && line.trim() == MARKER_HEADER {
            Some(GITIGNORE_ENTRY)
        } else if !retain_legacy && is_legacy_marker_header(line) {
            Some(LEGACY_GITIGNORE_ENTRY)
        } else {
            None
        };
        if let Some(entry) = entry {
            changed = true;
            if lines.peek().is_some_and(|next| is_entry_line(next, entry)) {
                lines.next();
            }
        } else {
            kept.push(line);
        }
    }
    if changed {
        kept.join("\n") + "\n"
    } else {
        existing.to_owned()
    }
}

/// Append `.kbdb/` to `project_root/.gitignore`.
///
/// - If `.gitignore` does not exist it is created.
/// - If the entry already exists the function returns without modification
///   (idempotent).
///
/// Called by `cmd_install`'s `--with-ingestion` full-scaffold path
/// (P2-T2b); the consumption-first minimal default has no managed
/// `.gitignore` side effect.
///
/// # Errors
///
/// Returns [`GraphtorError::Config`] on I/O failure.
pub fn add_gitignore_entry(project_root: &Path) -> Result<(), GraphtorError> {
    let path = project_root.join(".gitignore");

    // Workspace-containment guard (Constitution III/IV): the `read_to_string`
    // and `fs::write` below both FOLLOW a symlinked/junction `.gitignore`, so a
    // `.gitignore` planted as a link before install would redirect the
    // managed-block write into an external target OUTSIDE the project. The
    // uninstall/read paths (`has_managed_gitignore_block`,
    // `remove_gitignore_entry`) already refuse a linked `.gitignore`; the
    // install WRITE path must refuse it too. Fail closed rather than write
    // through the link.
    if is_reparse_point(&path) {
        return Err(GraphtorError::Config {
            message: ".gitignore is a symlink or junction; refusing to write the managed \
                      kbdb entry through a linked file"
                .to_string(),
            field: None,
        });
    }

    // Read existing content; create if missing.
    let existing = if path.exists() {
        fs::read_to_string(&path).map_err(|e| GraphtorError::Config {
            message: format!("failed to read .gitignore: {e}"),
            field: None,
        })?
    } else {
        String::new()
    };

    // Migrate obsolete legacy blocks even when the current entry already exists.
    let mut updated =
        strip_managed_blocks(&existing, false, legacy_graphtor_dir_exists(project_root));
    if updated
        .lines()
        .any(|line| is_entry_line(line, GITIGNORE_ENTRY))
    {
        if updated != existing {
            fs::write(&path, updated).map_err(|e| GraphtorError::Config {
                message: format!("failed to write .gitignore: {e}"),
                field: None,
            })?;
        }
        return Ok(());
    }

    if !updated.ends_with('\n') && !updated.is_empty() {
        updated.push('\n');
    }
    updated.push('\n');
    updated.push_str(MARKER_HEADER);
    updated.push('\n');
    updated.push_str(GITIGNORE_ENTRY);
    updated.push('\n');

    fs::write(&path, updated).map_err(|e| GraphtorError::Config {
        message: format!("failed to write .gitignore: {e}"),
        field: None,
    })?;

    Ok(())
}

/// Returns `true` when `project_root/.gitignore` exists and contains the
/// kbdb or legacy graphtor-docs managed marker header.
///
/// Uninstall planning uses this (rather than merely inferring from the
/// workspace footprint) so that a Full install created with `--no-gitignore`
/// (or one whose `.kbdb/` line is a user's own, unmarked entry) is never
/// scheduled for gitignore cleanup.
#[must_use]
pub fn has_managed_gitignore_block(project_root: &Path) -> bool {
    let path = project_root.join(".gitignore");
    // Workspace-containment guard (Constitution III/IV): `read_to_string`
    // FOLLOWS a symlinked/junction `.gitignore`, so reading a linked file would
    // report a managed block that lives OUTSIDE the project — and drive
    // uninstall into rewriting that external file. Treat a linked `.gitignore`
    // as having no managed block so cleanup is never planned for it.
    if is_reparse_point(&path) {
        return false;
    }
    let Ok(existing) = fs::read_to_string(&path) else {
        return false;
    };
    existing
        .lines()
        .any(|line| line.trim() == MARKER_HEADER || is_legacy_marker_header(line))
}

/// Remove the kbdb managed block and, only when `.graphtor` is absent,
/// legacy graphtor-docs managed blocks from `.gitignore`.
///
/// The managed entry is identified by its adjacency to the marker header:
/// [`add_gitignore_entry`] always writes the entry on the line immediately
/// after the marker, so removal strips the marker line and a single
/// immediately-following `.kbdb/` entry line. A user's own, unmarked
/// `.kbdb/` line elsewhere in the file is PRESERVED — uninstall must never
/// delete a gitignore line kbdb did not author.
///
/// If `.gitignore` does not exist or contains no managed marker, returns
/// without modification (idempotent).
///
/// # Errors
///
/// Returns [`GraphtorError::Config`] on I/O failure.
pub fn remove_gitignore_entry(project_root: &Path) -> Result<(), GraphtorError> {
    let path = project_root.join(".gitignore");
    if !path.exists() {
        return Ok(());
    }
    // Workspace-containment guard (Constitution III/IV): `read_to_string` and
    // `fs::write` both FOLLOW a symlinked/junction `.gitignore`, so touching a
    // linked file would rewrite a file OUTSIDE the project. Refuse to modify a
    // `.gitignore` that is itself a link — skip cleanup rather than reach out of
    // the workspace. Planning already excludes this case (see
    // `has_managed_gitignore_block`); this is defence-in-depth against a plan
    // that went stale after the file became a link.
    if is_reparse_point(&path) {
        return Ok(());
    }

    let existing = fs::read_to_string(&path).map_err(|e| GraphtorError::Config {
        message: format!("failed to read .gitignore: {e}"),
        field: None,
    })?;

    let updated = strip_managed_blocks(&existing, true, legacy_graphtor_dir_exists(project_root));
    if updated == existing {
        return Ok(());
    }

    fs::write(&path, updated).map_err(|e| GraphtorError::Config {
        message: format!("failed to write .gitignore: {e}"),
        field: None,
    })?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stream_a_legacy_gitignore_has_and_removes_legacy_managed_block() {
        for header in [
            "# graphtor-docs — managed by graphtor-docs install",
            "# graphtor-docs - managed by graphtor-docs install",
        ] {
            for entry in [".graphtor/", ".graphtor"] {
                for retain in [false, true] {
                    let tmp = tempfile::tempdir().expect("tempdir");
                    if retain {
                        fs::create_dir(tmp.path().join(".graphtor")).expect("legacy root");
                    }
                    let path = tmp.path().join(".gitignore");
                    fs::write(
                        &path,
                        format!("target/\n.graphtor/\n{header}\n{entry}\n{MARKER_HEADER}\n.kbdb/\n.env\n"),
                    )
                    .expect("seed");
                    assert!(has_managed_gitignore_block(tmp.path()));
                    remove_gitignore_entry(tmp.path()).expect("remove");
                    let after = fs::read_to_string(&path).expect("read");
                    assert_eq!(after.contains(header), retain);
                    assert!(!after.contains(MARKER_HEADER));
                    assert!(!after.contains(".kbdb/"));
                    assert!(after.contains("target/\n.graphtor/\n"));
                    assert!(after.contains(".env\n"));
                    let first = after;
                    remove_gitignore_entry(tmp.path()).expect("repeat remove");
                    assert_eq!(fs::read_to_string(&path).expect("read"), first);
                }
            }
        }
    }

    #[test]
    fn stream_a_legacy_gitignore_recognizes_legacy_only_and_preserves_unmarked_lines() {
        for header in [
            "# graphtor-docs — managed by graphtor-docs install",
            "# graphtor-docs - managed by graphtor-docs install",
        ] {
            let tmp = tempfile::tempdir().expect("tempdir");
            let path = tmp.path().join(".gitignore");
            fs::write(&path, format!("{header}\n.graphtor/\n")).expect("seed");
            assert!(has_managed_gitignore_block(tmp.path()));
            remove_gitignore_entry(tmp.path()).expect("remove");
            assert!(!has_managed_gitignore_block(tmp.path()));
            fs::write(&path, ".graphtor/\n.kbdb/\n.env\n").expect("unmarked");
            assert!(!has_managed_gitignore_block(tmp.path()));
            remove_gitignore_entry(tmp.path()).expect("preserve");
            assert_eq!(
                fs::read_to_string(&path).expect("read"),
                ".graphtor/\n.kbdb/\n.env\n"
            );
        }
    }

    #[test]
    fn stream_a_legacy_gitignore_add_migrates_or_retains_legacy_managed_block() {
        for header in [
            "# graphtor-docs — managed by graphtor-docs install",
            "# graphtor-docs - managed by graphtor-docs install",
        ] {
            for retain in [false, true] {
                for already_current in [false, true] {
                    let tmp = tempfile::tempdir().expect("tempdir");
                    if retain {
                        fs::create_dir(tmp.path().join(".graphtor")).expect("legacy root");
                    }
                    let path = tmp.path().join(".gitignore");
                    let current = if already_current {
                        format!("{MARKER_HEADER}\n.kbdb/\n")
                    } else {
                        String::new()
                    };
                    fs::write(
                        &path,
                        format!("target/\n{header}\n.graphtor\n{current}.env\n"),
                    )
                    .expect("seed");
                    add_gitignore_entry(tmp.path()).expect("add");
                    let after = fs::read_to_string(&path).expect("read");
                    assert_eq!(after.contains(header), retain);
                    assert_eq!(after.lines().any(|line| line == ".graphtor"), retain);
                    assert!(after.contains(&format!("{MARKER_HEADER}\n.kbdb/\n")));
                    assert!(after.contains("target/\n"));
                    assert!(after.contains(".env\n"));
                    add_gitignore_entry(tmp.path()).expect("repeat");
                    assert_eq!(fs::read_to_string(&path).expect("read"), after);
                }
            }
        }
    }

    #[test]
    fn stream_a_legacy_gitignore_retains_block_for_dangling_legacy_link() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let link = tmp.path().join(".graphtor");
        if try_symlink_file(&tmp.path().join("missing"), &link).is_err() {
            eprintln!("symlink privilege unavailable; dangling-link test skipped");
            return;
        }
        let path = tmp.path().join(".gitignore");
        let original = "# graphtor-docs - managed by graphtor-docs install\n.graphtor/\n";
        fs::write(&path, original).expect("seed");
        add_gitignore_entry(tmp.path()).expect("add");
        remove_gitignore_entry(tmp.path()).expect("remove");
        assert!(fs::read_to_string(&path).expect("read").contains(original));
    }

    #[test]
    fn add_creates_entry() {
        let tmp = tempfile::tempdir().expect("tempdir");
        add_gitignore_entry(tmp.path()).expect("add");
        let content = fs::read_to_string(tmp.path().join(".gitignore")).expect("read");
        assert!(content.contains(GITIGNORE_ENTRY));
    }

    #[test]
    fn add_is_idempotent() {
        let tmp = tempfile::tempdir().expect("tempdir");
        add_gitignore_entry(tmp.path()).expect("first");
        add_gitignore_entry(tmp.path()).expect("second");
        let content = fs::read_to_string(tmp.path().join(".gitignore")).expect("read");
        let count = content.matches(GITIGNORE_ENTRY).count();
        assert_eq!(count, 1, "entry should appear exactly once");
    }

    #[test]
    fn remove_cleans_entry() {
        let tmp = tempfile::tempdir().expect("tempdir");
        add_gitignore_entry(tmp.path()).expect("add");
        remove_gitignore_entry(tmp.path()).expect("remove");
        let content = fs::read_to_string(tmp.path().join(".gitignore")).expect("read");
        assert!(!content.contains(GITIGNORE_ENTRY));
    }

    #[test]
    fn remove_preserves_user_authored_unmarked_entry() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let path = tmp.path().join(".gitignore");
        // A user's own, unmarked `.kbdb/` line plus unrelated entries.
        fs::write(&path, "target/\n.kbdb/\n.env\n").expect("seed");
        remove_gitignore_entry(tmp.path()).expect("remove");
        let content = fs::read_to_string(&path).expect("read");
        assert!(
            content.contains(GITIGNORE_ENTRY),
            "user-authored unmarked .kbdb/ line must be preserved"
        );
        assert!(content.contains("target/"));
        assert!(content.contains(".env"));
    }

    #[test]
    fn remove_strips_managed_block_but_keeps_user_lines() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let path = tmp.path().join(".gitignore");
        fs::write(&path, "target/\n.env\n").expect("seed");
        add_gitignore_entry(tmp.path()).expect("add");
        remove_gitignore_entry(tmp.path()).expect("remove");
        let content = fs::read_to_string(&path).expect("read");
        assert!(!content.contains(MARKER_HEADER), "marker removed");
        assert!(!content.contains(GITIGNORE_ENTRY), "managed entry removed");
        assert!(content.contains("target/"), "user line preserved");
        assert!(content.contains(".env"), "user line preserved");
    }

    #[test]
    fn has_managed_block_reflects_marker_presence() {
        // No .gitignore -> no managed block.
        let tmp = tempfile::tempdir().expect("tempdir");
        assert!(
            !has_managed_gitignore_block(tmp.path()),
            "no .gitignore -> no managed block"
        );

        // An unmarked user `.kbdb/` line is not a managed block.
        let tmp2 = tempfile::tempdir().expect("tempdir");
        fs::write(tmp2.path().join(".gitignore"), ".kbdb/\n").expect("seed");
        assert!(
            !has_managed_gitignore_block(tmp2.path()),
            "unmarked .kbdb/ line is not a managed block"
        );

        // add writes the marker -> managed block present.
        let tmp3 = tempfile::tempdir().expect("tempdir");
        add_gitignore_entry(tmp3.path()).expect("add");
        assert!(
            has_managed_gitignore_block(tmp3.path()),
            "marker written by add -> managed block present"
        );
    }

    // ── workspace containment: symlinked `.gitignore` (X4) ──────────────────

    /// Create a file symlink cross-platform, returning `Err` when the platform
    /// refuses (e.g. Windows without the symlink privilege) so the caller can
    /// self-skip rather than fail.
    fn try_symlink_file(target: &Path, link: &Path) -> std::io::Result<()> {
        #[cfg(unix)]
        {
            std::os::unix::fs::symlink(target, link)
        }
        #[cfg(windows)]
        {
            std::os::windows::fs::symlink_file(target, link)
        }
    }

    #[test]
    fn symlinked_gitignore_is_never_treated_as_managed_or_rewritten() {
        // A `.gitignore` that is itself a symlink/junction points at a file
        // OUTSIDE the project. `has_managed_gitignore_block` must not read it as
        // managed, and `remove_gitignore_entry` must not rewrite the external
        // target (Constitution III/IV).
        let project = tempfile::tempdir().expect("project tempdir");
        let external = tempfile::tempdir().expect("external tempdir");
        let external_file = external.path().join("real-gitignore");
        let original = format!("{MARKER_HEADER}\n{GITIGNORE_ENTRY}\nnode_modules/\n");
        fs::write(&external_file, &original).expect("write external gitignore");

        let link = project.path().join(".gitignore");
        if try_symlink_file(&external_file, &link).is_err() {
            return; // platform refused symlink creation — skip
        }

        assert!(
            !has_managed_gitignore_block(project.path()),
            "a symlinked .gitignore must not be reported as holding a managed block"
        );
        remove_gitignore_entry(project.path()).expect("remove must skip a symlinked .gitignore");
        assert_eq!(
            fs::read_to_string(&external_file).expect("read external"),
            original,
            "the external file behind a symlinked .gitignore must be left unchanged"
        );
    }

    #[test]
    fn add_refuses_to_write_through_a_symlinked_gitignore() {
        // A6C7EDB3: a `.gitignore` planted as a symlink before install points at
        // a file OUTSIDE the project. `add_gitignore_entry`'s read + write would
        // FOLLOW the link and rewrite the external target (Constitution III/IV).
        // The install WRITE path must refuse a linked `.gitignore` and fail
        // closed, matching the uninstall/read guards.
        let project = tempfile::tempdir().expect("project tempdir");
        let external = tempfile::tempdir().expect("external tempdir");
        let external_file = external.path().join("real-gitignore");
        let original = "node_modules/\n".to_string();
        fs::write(&external_file, &original).expect("write external gitignore");

        let link = project.path().join(".gitignore");
        if try_symlink_file(&external_file, &link).is_err() {
            return; // platform refused symlink creation — skip
        }

        let result = add_gitignore_entry(project.path());
        assert!(
            result.is_err(),
            "add_gitignore_entry through a symlinked .gitignore must fail closed"
        );
        assert_eq!(
            fs::read_to_string(&external_file).expect("read external"),
            original,
            "the external file behind a symlinked .gitignore must be left unchanged"
        );
    }
}
