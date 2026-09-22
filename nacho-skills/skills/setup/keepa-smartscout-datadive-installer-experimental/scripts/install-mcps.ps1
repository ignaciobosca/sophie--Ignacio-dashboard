#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Keepa + SmartScout + DataDive adapter installer (Windows, experimental)

.DESCRIPTION
    Installs one or more of the curated MCPs (keepa, datadive, smartscout) into
    %USERPROFILE%\Tools\, builds them, and merges entries into Claude Desktop's
    claude_desktop_config.json. Existing servers and the `preferences` block are
    preserved. API keys are entered via hidden Read-Host -AsSecureString prompts --
    never through chat.

.PARAMETER Servers
    One or more of: keepa, datadive, smartscout. Default = all three.

.PARAMETER ResetKeys
    Re-prompt for API keys without re-cloning or rebuilding.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -Command "& '.\install-mcps.ps1' -Servers keepa,datadive"

.EXAMPLE
    powershell -ExecutionPolicy Bypass -Command "& '.\install-mcps.ps1' -ResetKeys -Servers keepa"

.NOTES
    Why -Command and not -File: when invoked via -File, powershell.exe passes
    "-Servers a,b" as a single string token "a,b" rather than splitting on the
    comma, so the [string[]] param ends up as @("a,b") and validation fails.
    Using -Command makes powershell parse the argument as a real PS expression,
    so the comma is treated as the array operator. The param block below also
    has a defensive split as a belt-and-braces fallback.
#>

[CmdletBinding()]
param(
    [string[]] $Servers,
    [switch]   $ResetKeys
)

$ErrorActionPreference = 'Stop'

# Defensive split: if someone invokes us via -File and passes
# "-Servers keepa,datadive", powershell.exe binds $Servers as @("keepa,datadive")
# (a single comma-joined string) rather than splitting. Normalise here so both
# forms work -- see .NOTES in the help block above for why.
if ($Servers -and $Servers.Count -eq 1 -and $Servers[0] -match ',') {
    $Servers = $Servers[0].Split(',') | Where-Object { $_ -ne '' }
}

function Prompt-YN([string]$Msg, [string]$Default = 'Y') {
    $reply = Read-Host -Prompt $Msg
    if ([string]::IsNullOrWhiteSpace($reply)) { $reply = $Default }
    return ($reply -match '^(y|yes)$')
}

# -- Preset definitions --------------------------------------------------------
$Presets = @{
    keepa = @{
        Repo    = 'https://github.com/BWB03/keepa-adapter.git'
        Dir     = 'keepa-adapter'
        EnvVar  = 'KEEPA_API_KEY'
        Display = 'Keepa'
    }
    datadive = @{
        Repo    = 'https://github.com/BWB03/datadive-adapter.git'
        Dir     = 'datadive-adapter'
        EnvVar  = 'DATADIVE_API_KEY'
        Display = 'DataDive'
    }
    smartscout = @{
        Repo    = 'https://github.com/BWB03/smartscout-adapter.git'
        Dir     = 'smartscout-adapter'
        EnvVar  = 'SMARTSCOUT_API_KEY'
        Display = 'SmartScout'
    }
}

# Plain ASCII glyphs so the script parses correctly on Windows PowerShell 5.1
# even when written without a UTF-8 BOM. PS 5.1 reads no-BOM files as cp1252,
# which would mangle Unicode chars like checkmarks / box-drawing into smart
# quotes that PS treats as string delimiters (FormatError).
function Info($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Ok  ($m) { Write-Host "[OK]   $m" -ForegroundColor Green }
function Warn($m) { Write-Host "[WARN] $m" -ForegroundColor Yellow }
function Fail($m) { Write-Host "[FAIL] $m" -ForegroundColor Red; exit 1 }

$ToolsDir  = if ($env:MCP_TOOLS_DIR) { $env:MCP_TOOLS_DIR } else { Join-Path $env:USERPROFILE 'Tools' }
$ConfigDir = Join-Path $env:APPDATA 'Claude'
$Config    = Join-Path $ConfigDir 'claude_desktop_config.json'

# Default to all three adapters when no -Servers given. The user-facing chat
# (Claude) is expected to ask which adapters and pass them via -Servers -- there's
# no interactive picker in PowerShell on purpose.
if (-not $Servers -or $Servers.Count -eq 0) {
    $Servers = @('keepa','datadive','smartscout')
}

# Validate slugs
foreach ($s in $Servers) {
    if (-not $Presets.ContainsKey($s)) {
        Fail "Unknown preset '$s'. Valid: $($Presets.Keys -join ', ')"
    }
}

Info "Servers: $($Servers -join ', ')"
Info "Tools dir: $ToolsDir"
Info "Config:    $Config"

# -- Quit Claude Desktop -------------------------------------------------------
Info 'Stopping Claude Desktop (so it can''t race the config write)'
$claudeProcs = Get-Process -Name 'Claude' -ErrorAction SilentlyContinue
if ($claudeProcs) {
    # Try graceful close first so unsaved chat state isn't lost
    foreach ($p in $claudeProcs) {
        try { $null = $p.CloseMainWindow() } catch {}
    }
    Start-Sleep -Seconds 2
    # Force-kill anything that ignored the close request
    Get-Process -Name 'Claude' -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 1
}
Ok 'Claude Desktop is stopped'

# -- Dependency auto-install (winget where available) -------------------------
function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' +
                [System.Environment]::GetEnvironmentVariable('Path','User')
}

function Ensure-WithWinget([string]$displayName, [string]$wingetId, [string]$probeCmd) {
    if (Get-Command $probeCmd -ErrorAction SilentlyContinue) { return $true }
    Warn "$displayName is not installed."
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Fail "$displayName missing and winget is also missing. Install from the Microsoft Store: search 'App Installer'. Then rerun this script."
    }
    if (-not (Prompt-YN "Install $displayName via winget now? [Y/n]")) {
        Fail "Cancelled. Install $displayName yourself, then rerun this script."
    }
    Info "winget install --id $wingetId -e --accept-source-agreements --accept-package-agreements"
    & winget install --id $wingetId -e --accept-source-agreements --accept-package-agreements
    Refresh-Path
    if (-not (Get-Command $probeCmd -ErrorAction SilentlyContinue)) {
        Fail "$displayName install completed but '$probeCmd' is still not on PATH. Open a NEW PowerShell window and rerun."
    }
    Ok "$displayName installed"
    return $true
}

if (-not $ResetKeys) {
    # Node 18+ (recommend LTS -- Node 23/24/odd-major versions can break native
    # builds in upstream adapters like keepa-adapter's better-sqlite3 pin).
    $needNode = $true
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeMajor = [int]((node -p 'process.versions.node.split(".")[0]'))
        if ($nodeMajor -ge 18) {
            Ok "Node $(node -v)"
            $needNode = $false
            # Warn (don't block) when keepa is selected on a non-LTS Node:
            # better-sqlite3 prebuilds may lag, forcing a node-gyp build that
            # needs VS C++ Build Tools and often fails on a clean machine.
            if ($Servers -contains 'keepa' -and $nodeMajor -ge 23) {
                Warn "Node $nodeMajor is non-LTS. If keepa's npm install fails on a better-sqlite3 native build, switch to Node 22 LTS (winget install --id OpenJS.NodeJS.LTS) and retry."
            }
        }
        else { Warn "Node $(node -v) is too old (need 18+)" }
    }
    if ($needNode) { Ensure-WithWinget 'Node.js LTS' 'OpenJS.NodeJS.LTS' 'node' | Out-Null }

    # git
    Ensure-WithWinget 'Git'           'Git.Git'           'git'    | Out-Null

    # python (any version 3.x -- we just need json + os)
    if (-not (Get-Command python  -ErrorAction SilentlyContinue) -and
        -not (Get-Command python3 -ErrorAction SilentlyContinue)) {
        Ensure-WithWinget 'Python 3' 'Python.Python.3.12' 'python' | Out-Null
    }

    if (-not (Test-Path $ToolsDir)) { New-Item -ItemType Directory -Path $ToolsDir | Out-Null }

    foreach ($s in $Servers) {
        $p = $Presets[$s]
        $target = Join-Path $ToolsDir $p.Dir

        if (Test-Path (Join-Path $target '.git')) {
            Info "[$s] updating existing checkout at $target"
            git -C $target pull --ff-only
        }
        elseif (Test-Path $target) {
            Fail "[$s] $target exists but isn't a git repo. Move it aside and rerun."
        }
        else {
            Info "[$s] cloning $($p.Repo) -> $target"
            git clone --depth=1 $p.Repo $target
        }

        Push-Location $target
        try {
            Info "[$s] npm install"
            # Don't use --silent: it suppresses node-gyp / native-build errors,
            # leaving an empty node_modules and a confusing 'tsup missing' error
            # at the next step. --loglevel=error keeps things tidy without
            # hiding real failures. Always check $LASTEXITCODE -- 'Stop' doesn't
            # catch native-command exit codes.
            npm install --loglevel=error
            if ($LASTEXITCODE -ne 0) {
                if ($s -eq 'keepa') {
                    Fail "[$s] npm install failed (exit $LASTEXITCODE). If you see a node-gyp / better-sqlite3 / 'Visual Studio' error, the most likely fix is to switch to Node 22 LTS: 'winget install --id OpenJS.NodeJS.LTS', open a new PowerShell, then rerun this script."
                } else {
                    Fail "[$s] npm install failed (exit $LASTEXITCODE) -- see errors above"
                }
            }
            Info "[$s] npm run build"
            npm run build
            if ($LASTEXITCODE -ne 0) { Fail "[$s] npm run build failed (exit $LASTEXITCODE) -- see errors above" }
        } finally { Pop-Location }

        $entry = Join-Path $target 'dist\index.js'
        if (-not (Test-Path $entry)) { Fail "[$s] build did not produce $entry" }
        Ok "[$s] built $entry"
    }
}

# -- Backup existing config ----------------------------------------------------
if (-not (Test-Path $ConfigDir)) { New-Item -ItemType Directory -Path $ConfigDir | Out-Null }
$ts = Get-Date -Format 'yyyyMMdd-HHmmss'
if (Test-Path $Config) {
    $bak = "$Config.bak.$ts"
    Copy-Item $Config $bak
    Ok "Backup -> $bak"
} else {
    Set-Content -Path $Config -Value '{}'
    Warn 'No existing config -- created an empty one'
}

# -- Prompt for API keys (hidden) ----------------------------------------------
Write-Host ''
Write-Host '-- API keys -------------------------------------------------------------'
Write-Host 'Paste each key when prompted. Input is hidden -- nothing will be echoed.'
Write-Host 'Press Enter on a blank line to keep the existing key (if any).'
Write-Host ''

$keys = @{}
foreach ($s in $Servers) {
    $p = $Presets[$s]
    $sec = Read-Host -AsSecureString "$($p.Display) API key ($($p.EnvVar))"
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
    try { $plain = [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
    finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
    $keys[$s] = $plain
}

# -- Merge into config ---------------------------------------------------------
# We hand off to python for the JSON merge because:
#  * Windows PowerShell 5.1 (still the default on Win 10/11) lacks
#    ConvertFrom-Json -AsHashtable, and PSCustomObject has gotchas around
#    preserving shape and mutating nested keys.
#  * python is already a hard requirement of the script.
Info 'Merging mcpServers into config (preserves existing servers + preferences)'

# Find python (python or python3)
$pythonExe = $null
foreach ($candidate in @('python','python3')) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $pythonExe = $candidate; break }
}
if (-not $pythonExe) { Fail 'python not found (used for JSON merge)' }

# Build the stdin payload: KEY-prefixed lines, then preset metadata lines.
# Keys never leave the parent process via env vars or argv.
$stdinLines = New-Object System.Collections.Generic.List[string]
foreach ($s in $Servers) {
    $stdinLines.Add("KEY`t$s`t$($keys[$s])")
}
foreach ($s in $Servers) {
    $p = $Presets[$s]
    $stdinLines.Add("$s|$($p.Repo)|$($p.EnvVar)|$($p.Display)|$($p.Dir)")
}

$pyScript = @'
import json, os, sys
cfg_path  = os.environ['CONFIG_PATH']
tools_dir = os.environ['TOOLS_DIR_E']
slugs     = os.environ['SLUGS_E'].split('|')

keys = {}
preset_lines = []
for raw in sys.stdin:
    line = raw.rstrip('\n')
    if line.startswith('KEY\t'):
        _, s, k = line.split('\t', 2)
        keys[s] = k
    elif line:
        preset_lines.append(line)

presets = {}
for line in preset_lines:
    s, repo, env_var, display, dirname = line.split('|')
    presets[s] = {'env_var': env_var, 'dirname': dirname}

if os.path.exists(cfg_path):
    with open(cfg_path) as f:
        raw = f.read().strip()
    if not raw:
        cfg = {}
    else:
        try:
            cfg = json.loads(raw)
        except Exception as e:
            print(f'ERROR: Existing config has invalid JSON: {e}', file=sys.stderr)
            print(f'       Inspect {cfg_path} and fix it before rerunning.', file=sys.stderr)
            sys.exit(2)
else:
    cfg = {}
if not isinstance(cfg, dict):
    print('ERROR: Existing config is not a JSON object -- aborting.', file=sys.stderr)
    sys.exit(2)

mcp = cfg.setdefault('mcpServers', {})

for s in slugs:
    p = presets[s]
    entry_path = os.path.join(tools_dir, p['dirname'], 'dist', 'index.js')
    existing = mcp.get(s, {}) if isinstance(mcp.get(s), dict) else {}
    existing_env = existing.get('env', {}) if isinstance(existing, dict) else {}
    new_key = keys.get(s, '')
    final_key = new_key if new_key else existing_env.get(p['env_var'], f"PASTE_YOUR_{p['env_var']}_HERE")
    env = {p['env_var']: final_key}
    if s == 'keepa':
        env.setdefault('KEEPA_DB_PATH', os.path.join(tools_dir, p['dirname'], 'keepa.db'))
        env.setdefault('KEEPA_DEFAULT_DOMAIN', 'com')
    for ek, ev in (existing_env.items() if isinstance(existing_env, dict) else []):
        if ek != p['env_var'] and ek not in env:
            env[ek] = ev
    mcp[s] = {'command': 'node', 'args': [entry_path], 'env': env}

with open(cfg_path, 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')

print('Top-level keys:', list(cfg.keys()))
print('mcpServers now:', sorted(mcp.keys()))
'@

$env:CONFIG_PATH = $Config
$env:TOOLS_DIR_E = $ToolsDir
$env:SLUGS_E    = ($Servers -join '|')

# Write the python script to a temp file rather than using -c, because
# multi-line strings as argv on Windows PowerShell 5.1 hit cmd.exe quoting
# quirks. A real file is bulletproof and gets cleaned up below.
$pyTemp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), "mcp-installer-merge-$([Guid]::NewGuid()).py")
try {
    Set-Content -Path $pyTemp -Value $pyScript -Encoding UTF8
    $stdinLines -join "`n" | & $pythonExe $pyTemp
    if ($LASTEXITCODE -ne 0) { Fail "JSON merge step failed (exit $LASTEXITCODE). Your existing config has been backed up." }
} finally {
    if (Test-Path $pyTemp) { Remove-Item $pyTemp -Force -ErrorAction SilentlyContinue }
    # Don't leave secrets in env vars beyond this script
    Remove-Item Env:\CONFIG_PATH -ErrorAction SilentlyContinue
    Remove-Item Env:\TOOLS_DIR_E -ErrorAction SilentlyContinue
    Remove-Item Env:\SLUGS_E    -ErrorAction SilentlyContinue
}

# Validate by re-parsing
try {
    Get-Content -Path $Config -Raw | ConvertFrom-Json | Out-Null
    Ok 'JSON valid'
} catch {
    Fail "Config write produced invalid JSON: $_"
}

Write-Host ''
Write-Host '------------------------------------------------------------'
Write-Host "[OK] Config written to:"
Write-Host "  $Config"
Write-Host ''
Write-Host "[OK] Backup saved at:"
Write-Host "  $bak"
Write-Host ''
Write-Host 'NEXT -- launch Claude Desktop, then verify in chat:'
Write-Host '  * "Check my Keepa token status"'
Write-Host '  * "List my DataDive niches"'
Write-Host '  * "Search SmartScout for ASIN B0XXXXXXXX"'
Write-Host ''
Write-Host 'If a 401 / auth error comes back, rerun:'
Write-Host "  powershell -ExecutionPolicy Bypass -Command `"& '$PSCommandPath' -ResetKeys -Servers $($Servers -join ',')`""
Write-Host '------------------------------------------------------------'
