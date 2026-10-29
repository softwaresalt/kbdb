#Requires -Version 5.1
<#
.SYNOPSIS
    Converts an existing graphtor / graphtor-docs workspace to use .kbdb and kbdb.exe.

.DESCRIPTION
    Converts a workspace from `.graphtor` / `graphtor-docs` to `.kbdb` / `kbdb`:
      1. Renames `.graphtor` to `.kbdb` using `git mv` when tracked by Git,
         falling back to `Move-Item` when `.graphtor` is gitignored or untracked.
      2. Renames any workspace-local `graphtor-docs.exe` (or `graphtor-docs`)
         executable under `.kbdb\bin\` (or the workspace root) to `kbdb.exe`
         (using `git mv` when tracked, or `Rename-Item` otherwise), and optionally
         updates it from a rebuilt `kbdb.exe` binary if available.
      3. Updates `.gitignore`, `.mcp.json` (and legacy editor MCP configs),
         `.env.local`, and `.kbdb\config\*sources.yaml` references from
         `.graphtor` / `graphtor-docs` to `.kbdb` / `kbdb`.

.PARAMETER WorkspacePath
    Root directory of the workspace to convert. Defaults to the current directory.

.PARAMETER BinaryPath
    Optional path to a rebuilt `kbdb.exe` binary to copy into `.kbdb\bin\kbdb.exe`
    when the workspace uses a full (`--with-ingestion`) layout.

.EXAMPLE
    .\scripts\convert-to-kbdb.ps1
    Converts the current workspace from `.graphtor` to `.kbdb`.

.EXAMPLE
    .\scripts\convert-to-kbdb.ps1 -WorkspacePath C:\Projects\MyDocs -WhatIf
    Previews all conversion steps without modifying files.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)]
    [string]$WorkspacePath = (Get-Location).Path,

    [Parameter()]
    [string]$BinaryPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Step([string]$Message) {
    Write-Host "[kbdb-convert] $Message" -ForegroundColor Cyan
}

function Write-WarnMsg([string]$Message) {
    Write-Host "[kbdb-convert] WARNING: $Message" -ForegroundColor Yellow
}

function Test-IsReparsePoint([string]$LiteralPath) {
    if (-not (Test-Path -LiteralPath $LiteralPath)) {
        return $false
    }
    $item = Get-Item -LiteralPath $LiteralPath -Force
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Write-Utf8NoBom([string]$LiteralPath, [string]$Content) {
    if (Test-IsReparsePoint $LiteralPath) {
        throw "Refusing to write through symlink or junction: $LiteralPath"
    }
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($LiteralPath, $Content, $utf8NoBom)
}

function Test-GitTracked([string]$RepoRoot, [string]$RelativePath) {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return $false
    }
    $insideWorkTree = & git -C $RepoRoot rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0 -or $insideWorkTree -ne 'true') {
        return $false
    }
    $tracked = & git -C $RepoRoot ls-files -- $RelativePath 2>$null
    return ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($tracked -join '')))
}

if (-not (Test-Path -LiteralPath $WorkspacePath -PathType Container)) {
    throw "Workspace directory not found: $WorkspacePath"
}

$workspaceRoot = (Resolve-Path -LiteralPath $WorkspacePath).Path
Write-Step "Inspecting workspace: $workspaceRoot"

$oldDir = Join-Path $workspaceRoot '.graphtor'
$newDir = Join-Path $workspaceRoot '.kbdb'

if (Test-IsReparsePoint $oldDir) {
    throw "Refusing to convert symlink or junction at: $oldDir"
}
if (Test-IsReparsePoint $newDir) {
    throw "Refusing to convert symlink or junction at: $newDir"
}

if ((Test-Path -LiteralPath $oldDir) -and (Test-Path -LiteralPath $newDir)) {
    throw "Both '.graphtor' and '.kbdb' exist in '$workspaceRoot'. Resolve the conflict manually before running this script."
}

# ── 1. Rename .graphtor -> .kbdb ─────────────────────────────────────────────
if (Test-Path -LiteralPath $oldDir -PathType Container) {
    $useGitMv = Test-GitTracked -RepoRoot $workspaceRoot -RelativePath '.graphtor'
    if ($PSCmdlet.ShouldProcess($oldDir, "Rename workspace folder to $newDir")) {
        if ($useGitMv) {
            Write-Step "Renaming tracked .graphtor -> .kbdb via 'git mv'..."
            & git -C $workspaceRoot mv -- '.graphtor' '.kbdb'
            if ($LASTEXITCODE -ne 0) {
                throw "'git mv .graphtor .kbdb' failed with exit code $LASTEXITCODE."
            }
        } else {
            Write-Step "Renaming untracked/ignored .graphtor -> .kbdb..."
            try {
                Move-Item -LiteralPath $oldDir -Destination $newDir -ErrorAction Stop
            } catch {
                $running = @(Get-Process -Name 'graphtor-docs', 'kbdb' -ErrorAction SilentlyContinue)
                if ($running.Count -gt 0) {
                    $pids = ($running | Select-Object -ExpandProperty Id) -join ', '
                    throw "Failed to move '$oldDir' to '$newDir' because an active process (PID: $pids) holds open handles inside .graphtor. Stop the running MCP server / sync process and re-run this script. Underlying error: $($_.Exception.Message)"
                }
                throw
            }
        }
    }
} elseif (Test-Path -LiteralPath $newDir -PathType Container) {
    Write-Step "Workspace directory '.kbdb' already exists; skipping folder rename."
} else {
    Write-WarnMsg "No '.graphtor' or '.kbdb' directory found in '$workspaceRoot'."
}

# ── 2. Rename lock file and executable to kbdb.exe ───────────────────────────
$activeWsDir = if (Test-Path -LiteralPath $newDir -PathType Container) { $newDir } else { $oldDir }

if (Test-Path -LiteralPath $activeWsDir -PathType Container) {
    $oldLock = Join-Path $activeWsDir 'graphtor.lock'
    $newLock = Join-Path $activeWsDir 'kbdb.lock'
    if ((Test-Path -LiteralPath $oldLock -PathType Leaf) -and -not (Test-Path -LiteralPath $newLock)) {
        if ($PSCmdlet.ShouldProcess($oldLock, "Rename lock file to kbdb.lock")) {
            Rename-Item -LiteralPath $oldLock -NewName 'kbdb.lock'
            Write-Step "Renamed graphtor.lock -> kbdb.lock"
        }
    }

    $binDir = Join-Path $activeWsDir 'bin'
    if (Test-Path -LiteralPath $binDir -PathType Container) {
        if (Test-IsReparsePoint $binDir) {
            throw "Refusing to operate on symlinked or junctioned bin directory: $binDir"
        }

        $oldExe = Join-Path $binDir 'graphtor-docs.exe'
        $newExe = Join-Path $binDir 'kbdb.exe'
        if (Test-Path -LiteralPath $oldExe -PathType Leaf) {
            if (Test-Path -LiteralPath $newExe -PathType Leaf) {
                if ($PSCmdlet.ShouldProcess($oldExe, "Remove superseded graphtor-docs.exe alongside existing kbdb.exe")) {
                    Remove-Item -LiteralPath $oldExe -Force
                    Write-Step "Removed superseded $oldExe (kbdb.exe already present)"
                }
            } else {
                $relOldExe = '.kbdb/bin/graphtor-docs.exe'
                $trackedExe = Test-GitTracked -RepoRoot $workspaceRoot -RelativePath $relOldExe
                if ($PSCmdlet.ShouldProcess($oldExe, "Rename executable to kbdb.exe")) {
                    if ($trackedExe) {
                        & git -C $workspaceRoot mv -- $relOldExe '.kbdb/bin/kbdb.exe'
                        if ($LASTEXITCODE -ne 0) {
                            throw "'git mv $relOldExe .kbdb/bin/kbdb.exe' failed with exit code $LASTEXITCODE."
                        }
                    } else {
                        Rename-Item -LiteralPath $oldExe -NewName 'kbdb.exe'
                    }
                    Write-Step "Renamed $oldExe -> $newExe"
                }
            }
        }

        $oldUnixBin = Join-Path $binDir 'graphtor-docs'
        $newUnixBin = Join-Path $binDir 'kbdb'
        if ((Test-Path -LiteralPath $oldUnixBin -PathType Leaf) -and -not (Test-Path -LiteralPath $newUnixBin)) {
            if ($PSCmdlet.ShouldProcess($oldUnixBin, "Rename Unix executable to kbdb")) {
                Rename-Item -LiteralPath $oldUnixBin -NewName 'kbdb'
                Write-Step "Renamed $oldUnixBin -> $newUnixBin"
            }
        }

        # If a rebuilt kbdb.exe is provided or built in target\release\kbdb.exe, update .kbdb\bin\kbdb.exe.
        $candidateSourceExe = if (-not [string]::IsNullOrWhiteSpace($BinaryPath)) {
            $BinaryPath
        } else {
            $releaseExe = Join-Path $workspaceRoot 'target\release\kbdb.exe'
            if (Test-Path -LiteralPath $releaseExe -PathType Leaf) { $releaseExe } else { $null }
        }

        if ($candidateSourceExe -and (Test-Path -LiteralPath $candidateSourceExe -PathType Leaf)) {
            $resolvedSrc = (Resolve-Path -LiteralPath $candidateSourceExe).Path
            if ($resolvedSrc -ne $newExe) {
                if ($PSCmdlet.ShouldProcess($newExe, "Update workspace binary from $resolvedSrc")) {
                    Copy-Item -LiteralPath $resolvedSrc -Destination $newExe -Force
                    Write-Step "Updated $newExe from rebuilt binary $resolvedSrc"
                }
            }
        }
    }
}

# Also check for a standalone graphtor-docs.exe directly in the workspace root or target\release.
foreach ($relDir in @('', 'target\release', 'target\debug')) {
    $dirPath = if ([string]::IsNullOrEmpty($relDir)) { $workspaceRoot } else { Join-Path $workspaceRoot $relDir }
    if (-not (Test-Path -LiteralPath $dirPath -PathType Container)) { continue }
    $oldRootExe = Join-Path $dirPath 'graphtor-docs.exe'
    $newRootExe = Join-Path $dirPath 'kbdb.exe'
    if ((Test-Path -LiteralPath $oldRootExe -PathType Leaf) -and -not (Test-Path -LiteralPath $newRootExe -PathType Leaf)) {
        if ($PSCmdlet.ShouldProcess($oldRootExe, "Rename executable to kbdb.exe")) {
            Rename-Item -LiteralPath $oldRootExe -NewName 'kbdb.exe'
            Write-Step "Renamed $oldRootExe -> $newRootExe"
        }
    }
}

# ── 3. Update .gitignore ─────────────────────────────────────────────────────
$gitignorePath = Join-Path $workspaceRoot '.gitignore'
if (Test-Path -LiteralPath $gitignorePath -PathType Leaf) {
    $rawGitignore = [System.IO.File]::ReadAllText($gitignorePath)
    $updatedGitignore = $rawGitignore `
        -replace '(?m)^# graphtor-docs — managed by graphtor-docs install\r?$', '# kbdb — managed by kbdb install' `
        -replace '(?m)^# graphtor workspace runtime \(databases, state, cloned data\)\r?$', '# kbdb workspace runtime (databases, state, cloned data)' `
        -replace '(?m)^\.graphtor/', '.kbdb/'
    if ($updatedGitignore -ne $rawGitignore) {
        if ($PSCmdlet.ShouldProcess($gitignorePath, "Update .graphtor entries to .kbdb")) {
            Write-Utf8NoBom -LiteralPath $gitignorePath -Content $updatedGitignore
            Write-Step "Updated .gitignore (.graphtor/ -> .kbdb/)"
        }
    }
}

# ── 4. Update MCP client configuration files ─────────────────────────────────
$mcpCandidates = @(
    '.mcp.json',
    '.vscode\mcp.json',
    '.cursor\mcp.json',
    '.github\copilot\mcp.json'
)

foreach ($relMcp in $mcpCandidates) {
    $mcpPath = Join-Path $workspaceRoot $relMcp
    if (-not (Test-Path -LiteralPath $mcpPath -PathType Leaf)) {
        continue
    }
    $rawMcp = [System.IO.File]::ReadAllText($mcpPath)
    $updatedMcp = $rawMcp `
        -replace '"graphtor-docs"\s*:', '"kbdb":' `
        -replace '"x-graphtor-managed"\s*:', '"x-kbdb-managed":' `
        -replace '\.graphtor([/\\]+)', '.kbdb$1' `
        -replace 'graphtor-docs(\.exe)?', 'kbdb$1'
    if ($updatedMcp -ne $rawMcp) {
        if ($PSCmdlet.ShouldProcess($mcpPath, "Update MCP server configuration to kbdb")) {
            Write-Utf8NoBom -LiteralPath $mcpPath -Content $updatedMcp
            Write-Step "Updated MCP config: $relMcp"
        }
    }
}

# ── 5. Update .env.local ─────────────────────────────────────────────────────
$envLocalPath = Join-Path $workspaceRoot '.env.local'
if (Test-Path -LiteralPath $envLocalPath -PathType Leaf) {
    $rawEnv = [System.IO.File]::ReadAllText($envLocalPath)
    $updatedEnv = $rawEnv `
        -replace '(?m)^GRAPHTOR_EMBED_MODEL_DIR=', 'KBDB_EMBED_MODEL_DIR=' `
        -replace '(?m)^GRAPHTOR_SOURCES=', 'KBDB_SOURCES=' `
        -replace '(?m)^GRAPHTOR_DB_PATH=', 'KBDB_DB_PATH=' `
        -replace '\.graphtor([/\\]+)', '.kbdb$1'
    if ($updatedEnv -ne $rawEnv) {
        if ($PSCmdlet.ShouldProcess($envLocalPath, "Update GRAPHTOR_* environment variables and .kbdb paths")) {
            Write-Utf8NoBom -LiteralPath $envLocalPath -Content $updatedEnv
            Write-Step "Updated .env.local"
        }
    }
}

# ── 6. Update .kbdb\config\*sources.yaml ─────────────────────────────────────
$configDir = Join-Path $activeWsDir 'config'
if (Test-Path -LiteralPath $configDir -PathType Container) {
    $yamlFiles = @(Get-ChildItem -LiteralPath $configDir -Filter '*.yaml' -File -ErrorAction SilentlyContinue)
    foreach ($yamlFile in $yamlFiles) {
        $rawYaml = [System.IO.File]::ReadAllText($yamlFile.FullName)
        $updatedYaml = $rawYaml `
            -replace '# graphtor-docs sources\.yaml', '# kbdb sources.yaml' `
            -replace '`graphtor-docs sync`', '`kbdb sync`' `
            -replace '\.graphtor([/\\]+)', '.kbdb$1'
        if ($updatedYaml -ne $rawYaml) {
            if ($PSCmdlet.ShouldProcess($yamlFile.FullName, "Update .graphtor references in $($yamlFile.Name)")) {
                Write-Utf8NoBom -LiteralPath $yamlFile.FullName -Content $updatedYaml
                Write-Step "Updated source config: $($yamlFile.FullName)"
            }
        }
    }
}

Write-Step "Workspace conversion complete."
