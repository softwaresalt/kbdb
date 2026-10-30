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
#     production binary and workspace;
#   * emits a redacted structured result and checks every native exit code.
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

function Fail([string] $Message, [int] $Code = 1) {
    Write-Error "T4_FAIL: $Message"
    exit $Code
}

$Python = Join-Path $Workspace 'logs/t4/venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $Python)) { Fail "capture venv missing: $Python" 2 }
if ($Sessions -lt 3) { Fail 'at least three sessions are required' 2 }

$stamp = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$RunDir = Join-Path $OutRoot $stamp
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null
$env:TEMP = Join-Path $Workspace 'logs/t4/tmp'
$env:TMP = $env:TEMP
New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null

# Entry identity (refuses wrappers) -- reuse the tested Python check.
$identJson = & $Python -c "import sys,json; sys.path.insert(0,r'$Workspace/tools/t4-capture'); import t4_capture as t; print(json.dumps(t.check_entry(r'$Workspace/.mcp.json', '$Entry')))"
if ($LASTEXITCODE -ne 0) { Fail 'production entry is not the direct delivered kbdb serve entry' 3 }
$ident = $identJson | ConvertFrom-Json

$env:KBDB_T4_PRODUCTION_EXE = $ident.command
$env:KBDB_T4_WORKSPACE = $Workspace
# A cold read of a very large production database can exceed the 60 s default.
if (-not $env:KBDB_T4_CONTROL_TIMEOUT_SECS) { $env:KBDB_T4_CONTROL_TIMEOUT_SECS = '300' }

function Invoke-T1Control([string] $Label) {
    $env:KBDB_T4_EVIDENCE_OUT = Join-Path $RunDir "t1-$Label.json"
    & cargo test --test t4_production_control_test -- --ignored production_control_proves_wire_initialize_tools_and_get_status 2>&1 |
        Tee-Object -FilePath (Join-Path $RunDir "t1-$Label.log") | Out-Null
    if ($LASTEXITCODE -ne 0) { Fail "T1 production wire control ($Label) failed (exit $LASTEXITCODE)" }
    if (-not (Test-Path -LiteralPath $env:KBDB_T4_EVIDENCE_OUT)) { Fail "T1 control ($Label) wrote no evidence" }
}

Invoke-T1Control 'before'

& $Python (Join-Path $Workspace 'tools/t4-capture/t4_capture.py') `
    --workspace $Workspace --copilot-exe $CopilotExe --entry $Entry `
    --sessions $Sessions --out-dir (Join-Path $RunDir 'sessions')
$captureExit = $LASTEXITCODE

Invoke-T1Control 'after'

if ($captureExit -ne 0) { Fail "Copilot /mcp show capture did not pass (exit $captureExit)" $captureExit }

$sessionsDoc = Get-Content -LiteralPath (Join-Path $RunDir 'sessions/sessions.json') -Raw | ConvertFrom-Json
$result = [ordered]@{
    runner            = 'scripts/verify_copilot_mcp_show.ps1'
    generated_utc     = (Get-Date).ToUniversalTime().ToString('o')
    git_head          = (& git rev-parse HEAD)
    workspace         = $Workspace
    entry             = $Entry
    config            = $ident
    copilot           = $sessionsDoc.copilot
    sessions          = $sessionsDoc.sessions
    t1_control_before = Get-Content -LiteralPath (Join-Path $RunDir 't1-before.json') -Raw | ConvertFrom-Json
    t1_control_after  = Get-Content -LiteralPath (Join-Path $RunDir 't1-after.json') -Raw | ConvertFrom-Json
    sink_used         = $false
    acceptance        = if ($sessionsDoc.all_passed) { 'sessions-passed' } else { 'failed' }
    observation_window = 'Healthy requires three starts within 24 hours; this run supplies them only if all three passed.'
}
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $RunDir 'result.json') -Encoding utf8
Write-Output "T4_RESULT: $(Join-Path $RunDir 'result.json')"
exit 0
