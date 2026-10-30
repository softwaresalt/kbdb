#!/usr/bin/env pwsh
# verify_copilot_mcp_show.ps1 -- T4 (056.004-T) restored-production runtime
# verification runner.
#
# Contract (see .backlogit/queue/056.004-T.md):
#   * invokes the exact interactive Copilot executable NORMALLY inside a PTY and
#     types the real `/mcp show <entry>` slash command (no wrapper, temporary
#     config, executable substitution, or model prompt);
#   * NEVER treats an exit code alone as a pass: the reconstructed CLI screen is
#     evaluated (connected + initialized, no OS error 232, tool list recorded);
#   * refuses a wrapper/non-delivered production entry before any session;
#   * correlates config hash, Copilot identity, and the Copilot-spawned server
#     pid/exe/hash/cwd/start time (Win32_Process + PEB read) for each session;
#   * runs the 056.002-T read-only production wire control SEQUENTIALLY before
#     and after the Copilot sessions (never concurrently) against the SAME
#     production binary and workspace, and checks that the sessions used that
#     same configuration and executable;
#   * emits a redacted structured result and checks every native exit code;
#   * restores every environment variable it sets and the caller's directory.
#
# Setup (once): python -m venv logs/t4/venv ; then install
# tools/t4-capture/requirements.txt into it. Output stays under logs/t4/.
[CmdletBinding()]
param(
    [string] $Workspace = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string] $Entry = 'kbdb',
    [string] $CopilotExe = (Get-Command copilot.exe -ErrorAction Stop).Source,
    [int] $Sessions = 3,
    [string] $OutRoot = (Join-Path (Resolve-Path (Join-Path $PSScriptRoot '..')).Path 'logs/t4/runs')
)
$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

class T4Failure : System.Exception {
    [int] $Code
    T4Failure([string] $Message, [int] $Code) : base($Message) { $this.Code = $Code }
}

function Fail([string] $Message, [int] $Code = 1) {
    throw [T4Failure]::new($Message, $Code)
}

$EnvNames = 'TEMP', 'TMP', 'KBDB_T4_PRODUCTION_EXE', 'KBDB_T4_WORKSPACE',
    'KBDB_T4_EVIDENCE_OUT', 'KBDB_T4_CONTROL_TIMEOUT_SECS'
$SavedEnv = @{}
foreach ($name in $EnvNames) { $SavedEnv[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }

function Invoke-T1Control([string] $RunDir, [string] $Label) {
    $env:KBDB_T4_EVIDENCE_OUT = Join-Path $RunDir "t1-$Label.json"
    & cargo test --test t4_production_control_test -- --ignored production_control_proves_wire_initialize_tools_and_get_status 2>&1 |
        Tee-Object -FilePath (Join-Path $RunDir "t1-$Label.log") | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "T1 production wire control ($Label) failed (exit $LASTEXITCODE)" }
    if (-not (Test-Path -LiteralPath $env:KBDB_T4_EVIDENCE_OUT)) { Fail "T1 control ($Label) wrote no evidence" }
}

function Invoke-T4 {
    $python = Join-Path $Workspace 'logs/t4/venv/Scripts/python.exe'
    if (-not (Test-Path -LiteralPath $python)) { Fail "capture venv missing: $python" 2 }
    if ($Sessions -lt 3) { Fail 'at least three sessions are required' 2 }

    $runDir = Join-Path $OutRoot (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    $env:TEMP = Join-Path $Workspace 'logs/t4/tmp'
    $env:TMP = $env:TEMP
    New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null

    # Entry identity (refuses wrappers): the tested Python check, with every
    # value passed as an argument so no path can break the program text.
    $program = 'import sys,json; sys.path.insert(0, sys.argv[1]); import t4_capture as t; print(json.dumps(t.check_entry(sys.argv[2], sys.argv[3])))'
    $identJson = & $python -c $program (Join-Path $Workspace 'tools/t4-capture') (Join-Path $Workspace '.mcp.json') $Entry
    if ($LASTEXITCODE -ne 0) { Fail 'production entry is not the direct delivered kbdb serve entry' 3 }
    $ident = $identJson | ConvertFrom-Json

    $env:KBDB_T4_PRODUCTION_EXE = $ident.command
    $env:KBDB_T4_WORKSPACE = $Workspace
    # A cold read of a very large production database can exceed the 60 s default.
    if (-not $env:KBDB_T4_CONTROL_TIMEOUT_SECS) { $env:KBDB_T4_CONTROL_TIMEOUT_SECS = '300' }

    Invoke-T1Control $runDir 'before'

    & $python (Join-Path $Workspace 'tools/t4-capture/t4_capture.py') `
        --workspace $Workspace --copilot-exe $CopilotExe --entry $Entry `
        --sessions $Sessions --out-dir (Join-Path $runDir 'sessions')
    $captureExit = $LASTEXITCODE
    # Any nonzero capture exit withholds the after-control: a failed or refused
    # capture may have left a client or server running, and a control must never
    # overlap a Copilot session.
    if ($captureExit -eq 4) { Fail 'client/server teardown could not be confirmed; no further control was run' 4 }
    if ($captureExit -ne 0) { Fail "Copilot /mcp show capture did not pass (exit $captureExit); the after-control was not run" $captureExit }

    Invoke-T1Control $runDir 'after'
    $sessionsDoc = Get-Content -LiteralPath (Join-Path $runDir 'sessions/sessions.json') -Raw | ConvertFrom-Json
    # The sessions and both wire controls must have used the same production
    # configuration and executable.
    if ($sessionsDoc.config.config_sha256 -ne $ident.config_sha256 -or
        $sessionsDoc.config.exe_sha256 -ne $ident.exe_sha256) {
        Fail 'production config or executable changed between the wire controls and the Copilot sessions' 5
    }
    $result = [ordered]@{
        runner             = 'scripts/verify_copilot_mcp_show.ps1'
        generated_utc      = (Get-Date).ToUniversalTime().ToString('o')
        git_head           = (& git -C $Workspace rev-parse HEAD)
        workspace          = $Workspace
        entry              = $Entry
        config             = $ident
        copilot            = $sessionsDoc.copilot
        sessions           = $sessionsDoc.sessions
        t1_control_before  = Get-Content -LiteralPath (Join-Path $runDir 't1-before.json') -Raw | ConvertFrom-Json
        t1_control_after   = Get-Content -LiteralPath (Join-Path $runDir 't1-after.json') -Raw | ConvertFrom-Json
        sink_used          = $false
        acceptance         = if ($sessionsDoc.all_passed) { 'sessions-passed' } else { 'failed' }
        observation_window = 'Healthy requires three starts within 24 hours; this run supplies them only if all three passed.'
    }
    $result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $runDir 'result.json') -Encoding utf8
    Write-Output "T4_RESULT: $(Join-Path $runDir 'result.json')"
}

$exitCode = 0
Push-Location -LiteralPath $Workspace
try {
    Invoke-T4
}
catch [T4Failure] {
    [Console]::Error.WriteLine("T4_FAIL: $($_.Exception.Message)")
    $exitCode = $_.Exception.Code
}
catch {
    [Console]::Error.WriteLine("T4_FAIL: unexpected error: $($_.Exception.Message)")
    $exitCode = 1
}
finally {
    foreach ($name in $EnvNames) { [Environment]::SetEnvironmentVariable($name, $SavedEnv[$name], 'Process') }
    Pop-Location
}
exit $exitCode
