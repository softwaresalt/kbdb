//! Workspace `sources.yaml` initialization.
//!
//! Generates a template `sources.yaml` at `.kbdb/config/sources.yaml`
//! with commented examples for Git and local sources. Idempotent: will not
//! overwrite an existing file unless `force = true` is passed.

use std::fs;
use std::io::Write;
use std::path::Path;

use graphtor_core::path::is_reparse_point;
use graphtor_core::GraphtorError;

use crate::workspace::doctor::LEGACY_GRAPHTOR_DIR;

/// Default template content for a new `sources.yaml`.
const SOURCES_YAML_TEMPLATE: &str = r#"# kbdb sources.yaml
# Documentation source registry. Add local Markdown sources below.
# Only docline-emitted standardized Markdown is accepted.
# Run `kbdb sync` to ingest all sources.
#
# Supported source types:
#   local — scan a local directory for standardized Markdown files

sources: []

# Example local source:
# sources:
#   - id: my-internal-docs
#     type: local
#     path: /absolute/or/relative/path/to/docs
#     include:
#       - "**/*.md"
#     exclude:
#       - "**/drafts/**"
"#;

/// Initialise the `sources.yaml` in the workspace config directory.
///
/// If the file already exists and `force` is `false`, returns without
/// modification (idempotent). If `force` is `true`, overwrites.
/// Otherwise copies a regular, non-reparse legacy configuration when available,
/// changing only the two literal branding comments in its leading header.
///
/// # Errors
///
/// Returns [`GraphtorError::Config`] on I/O failure or linked target directories.
pub fn init_sources_yaml(workspace_dir: &Path, force: bool) -> Result<InitResult, GraphtorError> {
    let config_dir = workspace_dir.join("config");
    // Check parents before creating or writing anything through them.
    if is_reparse_point(workspace_dir) || is_reparse_point(&config_dir) {
        return Err(GraphtorError::Config {
            message: "workspace or config directory is a symlink or junction; refusing to init"
                .to_string(),
            field: None,
        });
    }
    fs::create_dir_all(&config_dir).map_err(|e| GraphtorError::Config {
        message: format!("failed to create config dir: {e}"),
        field: None,
    })?;

    let target = config_dir.join("sources.yaml");
    if target.symlink_metadata().is_ok() && !force {
        return Ok(InitResult {
            path: target,
            created: false,
        });
    }

    if is_reparse_point(&target) {
        return Err(GraphtorError::Config {
            message: "sources.yaml is a symlink or junction; refusing to overwrite".to_string(),
            field: None,
        });
    }
    let legacy_content = if force {
        None
    } else {
        read_legacy_sources(workspace_dir)?
    };
    let content = legacy_content
        .as_deref()
        .unwrap_or(SOURCES_YAML_TEMPLATE.as_bytes());
    // Exclusive creation prevents a concurrent init from replacing user config.
    let opened = fs::OpenOptions::new()
        .write(true)
        .create(force)
        .truncate(force)
        .create_new(!force)
        .open(&target);
    if !force
        && opened
            .as_ref()
            .is_err_and(|error| error.kind() == std::io::ErrorKind::AlreadyExists)
    {
        return Ok(InitResult {
            path: target,
            created: false,
        });
    }
    let mut file = opened.map_err(|e| GraphtorError::Config {
        message: format!("failed to open sources.yaml: {e}"),
        field: None,
    })?;
    file.write_all(content).map_err(|e| GraphtorError::Config {
        message: format!("failed to write sources.yaml: {e}"),
        field: None,
    })?;

    Ok(InitResult {
        path: target,
        created: true,
    })
}

/// Read only a regular legacy source whose entire legacy path is unlinked.
fn read_legacy_sources(workspace_dir: &Path) -> Result<Option<Vec<u8>>, GraphtorError> {
    let Some(project_root) = workspace_dir.parent() else {
        return Ok(None);
    };
    let legacy_dir = project_root.join(LEGACY_GRAPHTOR_DIR);
    let legacy_config = legacy_dir.join("config");
    let source = legacy_config.join("sources.yaml");
    if is_reparse_point(&legacy_dir)
        || is_reparse_point(&legacy_config)
        || is_reparse_point(&source)
        || !source.is_file()
    {
        return Ok(None);
    }
    let content = fs::read(&source).map_err(|e| GraphtorError::Config {
        message: format!(
            "failed to read legacy sources.yaml at {}: {e}",
            source.display()
        ),
        field: None,
    })?;
    Ok(Some(normalize_legacy_header(&content)))
}

/// Preserve arbitrary bytes and line endings, never replacing YAML data.
#[must_use]
fn normalize_legacy_header(content: &[u8]) -> Vec<u8> {
    let mut normalized = Vec::with_capacity(content.len());
    let mut in_header = true;
    for line in content.split_inclusive(|byte| *byte == b'\n') {
        if !line.starts_with(b"#") && !line.iter().all(u8::is_ascii_whitespace) {
            in_header = false;
        }
        let replacement = in_header
            .then(|| {
                line.strip_prefix(b"# graphtor-docs sources.yaml")
                    .map(|tail| (b"# kbdb sources.yaml".as_slice(), tail))
                    .or_else(|| {
                        line.strip_prefix(b"# Run `graphtor-docs sync`")
                            .map(|tail| (b"# Run `kbdb sync`".as_slice(), tail))
                    })
            })
            .flatten();
        if let Some((prefix, tail)) = replacement {
            normalized.extend_from_slice(prefix);
            normalized.extend_from_slice(tail);
        } else {
            normalized.extend_from_slice(line);
        }
    }
    normalized
}

/// Result of a sources.yaml init operation.
#[derive(Debug)]
pub struct InitResult {
    /// Absolute path to the sources.yaml file.
    pub path: std::path::PathBuf,
    /// Whether the file was newly created (`true`) or already existed (`false`).
    pub created: bool,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn stream_a_legacy_workspace_init_migrates_legacy_sources_yaml() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let legacy = tmp.path().join(".graphtor/config");
        fs::create_dir_all(&legacy).expect("legacy config");
        let header =
            "# graphtor-docs sources.yaml\r\n# Run `graphtor-docs sync` to ingest all sources.\r\n";
        let data = concat!(
            "# Keep graphtor-docs and .graphtor custom comments\r\n",
            "sources:\r\n",
            "  - id: café\r\n",
            "    type: local\r\n",
            "    path: '.graphtor/docs/graphtor-docs'\r\n",
            "    url: 'https://example.invalid/.graphtor/graphtor-docs'\r\n",
            "    include: ['.graphtor/**/*.md', '**/graphtor-docs*']\r\n",
            "    exclude: ['.graphtor/cache/**']\r\n",
            "    glob: '.graphtor/**/graphtor-docs.md'\r\n",
            "    note: '# graphtor-docs sources.yaml'\r\n",
            "    description: |\r\n",
            "      # Run `graphtor-docs sync` inside YAML data\r\n",
            "# graphtor-docs sources.yaml (not a header)\r\n"
        );
        let original = format!("{header}{data}");
        let source = legacy.join("sources.yaml");
        fs::write(&source, original.as_bytes()).expect("legacy source");
        let ws = tmp.path().join(".kbdb");
        let result = init_sources_yaml(&ws, false).expect("migration");
        assert!(result.created);
        assert_eq!(result.path, ws.join("config/sources.yaml"));
        let expected =
            format!("# kbdb sources.yaml\r\n# Run `kbdb sync` to ingest all sources.\r\n{data}");
        assert_eq!(fs::read(&result.path).expect("target"), expected.as_bytes());
        assert_eq!(fs::read(&source).expect("source"), original.as_bytes());

        let again = init_sources_yaml(&ws, false).expect("idempotent init");
        assert!(!again.created);
        assert_eq!(fs::read(&again.path).expect("target"), expected.as_bytes());
        let forced = init_sources_yaml(&ws, true).expect("forced template");
        assert_eq!(
            fs::read(&forced.path).expect("template"),
            SOURCES_YAML_TEMPLATE.as_bytes()
        );
        assert_eq!(fs::read(&source).expect("source"), original.as_bytes());
    }

    // Junctions do not require Windows symlink privileges. Generated test paths
    // are passed as distinct arguments, never interpolated into a shell script.
    fn link_directory(target: &Path, link: &Path) -> bool {
        // Rebuild with native separators: cmd's mklink treats '/' as a switch.
        #[cfg(windows)]
        let link: std::path::PathBuf = link.components().collect();
        #[cfg(windows)]
        let result = std::process::Command::new("cmd")
            .args(["/C", "mklink", "/J"])
            .arg(link)
            .arg(target)
            .output()
            .map(|output| output.status.success());
        #[cfg(unix)]
        let result = std::os::unix::fs::symlink(target, link).map(|()| true);
        match result {
            Ok(true) => true,
            other => {
                eprintln!("directory link unavailable: {other:?}");
                false
            }
        }
    }

    #[test]
    fn legacy_migration_does_not_follow_linked_source_directories() {
        for component in [".graphtor", ".graphtor/config"] {
            let tmp = tempfile::tempdir().expect("tempdir");
            let external = tmp.path().join("external");
            let config = if component == ".graphtor" {
                external.join("config")
            } else {
                external.clone()
            };
            fs::create_dir_all(&config).expect("external config");
            let source = config.join("sources.yaml");
            fs::write(&source, b"private legacy content").expect("external source");
            let link = tmp.path().join(component);
            fs::create_dir_all(link.parent().expect("parent")).expect("link parent");
            if !link_directory(&external, &link) {
                continue;
            }
            let result = init_sources_yaml(&tmp.path().join(".kbdb"), false).expect("init");
            assert_eq!(
                fs::read(result.path).expect("target"),
                SOURCES_YAML_TEMPLATE.as_bytes()
            );
            assert_eq!(fs::read(source).expect("source"), b"private legacy content");
        }
    }

    #[test]
    fn legacy_migration_does_not_follow_linked_source_file() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let config = tmp.path().join(".graphtor/config");
        fs::create_dir_all(&config).expect("config");
        let external = tmp.path().join("external.yaml");
        fs::write(&external, b"private legacy content").expect("external source");
        let link = config.join("sources.yaml");
        #[cfg(windows)]
        let linked = std::os::windows::fs::symlink_file(&external, &link);
        #[cfg(unix)]
        let linked = std::os::unix::fs::symlink(&external, &link);
        if let Err(error) = linked {
            eprintln!("file symlink unavailable: {error}");
            return;
        }
        let result = init_sources_yaml(&tmp.path().join(".kbdb"), false).expect("init");
        assert_eq!(
            fs::read(result.path).expect("target"),
            SOURCES_YAML_TEMPLATE.as_bytes()
        );
        assert_eq!(
            fs::read(external).expect("source"),
            b"private legacy content"
        );
    }

    #[test]
    fn init_refuses_linked_target_directories() {
        for component in [".kbdb", ".kbdb/config"] {
            let tmp = tempfile::tempdir().expect("tempdir");
            let external = tmp.path().join("external");
            fs::create_dir(&external).expect("external");
            let link = tmp.path().join(component);
            fs::create_dir_all(link.parent().expect("parent")).expect("parent");
            if !link_directory(&external, &link) {
                continue;
            }
            assert!(init_sources_yaml(&tmp.path().join(".kbdb"), false).is_err());
            assert_eq!(
                fs::read_dir(&external).expect("external entries").count(),
                0
            );
        }
    }

    #[test]
    fn creates_template() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let ws = tmp.path().join(".kbdb");
        fs::create_dir_all(&ws).expect("create ws");
        let result = init_sources_yaml(&ws, false).expect("init");
        assert!(result.created);
        assert!(result.path.exists());
        let content = fs::read_to_string(&result.path).expect("read");
        assert!(content.contains("sources:"));
    }

    #[test]
    fn does_not_overwrite_without_force() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let ws = tmp.path().join(".kbdb");
        fs::create_dir_all(&ws).expect("create ws");
        init_sources_yaml(&ws, false).expect("first");
        // Write custom content.
        let config = ws.join("config").join("sources.yaml");
        fs::write(&config, "custom").expect("write custom");
        let result = init_sources_yaml(&ws, false).expect("second");
        assert!(!result.created);
        assert_eq!(fs::read_to_string(&result.path).expect("read"), "custom");
    }

    #[test]
    fn force_overwrites() {
        let tmp = tempfile::tempdir().expect("tempdir");
        let ws = tmp.path().join(".kbdb");
        fs::create_dir_all(&ws).expect("create ws");
        let config = ws.join("config").join("sources.yaml");
        fs::create_dir_all(ws.join("config")).expect("mkdir");
        fs::write(&config, "custom").expect("write custom");
        let result = init_sources_yaml(&ws, true).expect("force");
        assert!(result.created);
        let content = fs::read_to_string(&result.path).expect("read");
        assert!(content.contains("sources:"));
    }
}
