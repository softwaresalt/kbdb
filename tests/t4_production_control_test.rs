//! T4 (`056.004-T`) restored-production wire control.
//!
//! Runs the `056.002-T` read-only server control against the DELIVERED
//! production server executable and the canonical workspace named by the
//! environment, instead of the Cargo-built test binary. It is `#[ignore]`d
//! so a plain `cargo test` never depends on a production install;
//! `scripts/verify_copilot_mcp_show.ps1` runs it explicitly (sequentially,
//! never alongside a Copilot session) with:
//!
//! * `KBDB_T4_PRODUCTION_EXE`: absolute path of the delivered `kbdb` binary
//! * `KBDB_T4_WORKSPACE`: absolute canonical workspace directory
//! * `KBDB_T4_EVIDENCE_OUT`: optional path for the redacted JSON evidence
//!
//! The wire fields proven here (`initialize` id and `protocolVersion`, the
//! expected tool set, one side-effect-free `get_status`) are NOT visible in
//! `/mcp show`; the Copilot sessions prove connection separately.

mod common;

use std::path::PathBuf;
use std::time::Duration;

use common::serve_driver::{
    assert_stdout_protocol_clean, production_server_exe, run_read_only_server_control,
    ServerControlOutcome,
};
use graphtor_core::mcp::list_mcp_tools;
use serde_json::json;

/// Default overall control-session deadline. A production workspace can hold
/// very large databases, so `KBDB_T4_CONTROL_TIMEOUT_SECS` may raise it.
fn control_timeout() -> Duration {
    let secs = std::env::var("KBDB_T4_CONTROL_TIMEOUT_SECS")
        .ok()
        .and_then(|raw| raw.parse::<u64>().ok())
        .unwrap_or(60);
    Duration::from_secs(secs)
}

#[test]
#[ignore = "T4 production control: run by scripts/verify_copilot_mcp_show.ps1 with KBDB_T4_* set"]
fn production_control_proves_wire_initialize_tools_and_get_status() {
    let exe = production_server_exe().expect("KBDB_T4_PRODUCTION_EXE must name the delivered exe");
    let workspace =
        PathBuf::from(std::env::var("KBDB_T4_WORKSPACE").expect("KBDB_T4_WORKSPACE must be set"));
    assert!(
        workspace.is_absolute() && workspace.is_dir(),
        "KBDB_T4_WORKSPACE must be an existing absolute directory"
    );

    let report = run_read_only_server_control(&workspace, control_timeout());

    let success = match &report.outcome {
        ServerControlOutcome::Control(success) => success,
        other => panic!(
            "production control did not complete: {other:?} (stderr: {}, exit: {:?})",
            report.stderr, report.exit_code
        ),
    };
    assert!(
        !success.initialize.protocol_version.is_empty(),
        "negotiated protocolVersion must be non-empty"
    );

    let mut expected: Vec<String> = list_mcp_tools()
        .into_iter()
        .map(|tool| tool.name.as_ref().to_string())
        .collect();
    expected.sort();
    let mut actual = success.tool_names.clone();
    actual.sort();
    assert_eq!(
        actual, expected,
        "production tools/list must equal the manifest"
    );
    assert!(
        !success.get_status_text.is_empty(),
        "get_status must return non-empty status text"
    );
    assert_stdout_protocol_clean(&report.observed_lines);

    if let Ok(out) = std::env::var("KBDB_T4_EVIDENCE_OUT") {
        let evidence = json!({
            "control": "056.002-T read-only production control",
            "server_exe": exe.display().to_string(),
            "workspace": workspace.display().to_string(),
            "initialize": {
                "jsonrpc": "2.0",
                "protocolVersion": success.initialize.protocol_version,
                "serverInfo": success.initialize.server_info,
            },
            "tool_names": actual,
            "get_status_nonempty": true,
            "stdout_protocol_clean": true,
            "exit_code": report.exit_code,
        });
        std::fs::write(
            &out,
            serde_json::to_vec_pretty(&evidence).expect("serialize evidence"),
        )
        .expect("write evidence");
    }
}

#[test]
fn production_server_exe_refuses_missing_or_relative_override() {
    // The override must be explicit and absolute; a relative or missing path
    // can never silently fall back to the Cargo test binary for a T4 run.
    assert!(common::serve_driver::validate_production_exe("").is_err());
    assert!(common::serve_driver::validate_production_exe("kbdb.exe").is_err());
    assert!(
        common::serve_driver::validate_production_exe("C:\\definitely\\not\\here\\kbdb.exe")
            .is_err()
    );
}
