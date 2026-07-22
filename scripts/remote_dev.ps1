[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Probe", "Sync", "Test", "Deploy", "Exec", "ImportHistory", "Collect", "Logs", "Cleanup")]
    [string]$Action,
    [string]$SessionId = "",
    [ValidateSet("backend", "frontend", "playwright", "stack")]
    [string]$Runner = "stack",
    [string]$Command = "",
    [switch]$AllowProviderCalls,
    [switch]$AllowPartialTraceRecovery,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptRoot "..")).Path
$ConfigPath = Join-Path $RepoRoot "deploy/remote-dev.env"
$SessionStore = Join-Path $RepoRoot ".remote-validation"
$script:LastNativeExitCode = 0
$script:Manifest = $null
$script:ManifestPath = $null

function Read-KeyValueFile {
    param([string]$Path)
    $values = @{}
    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2) { throw "Invalid config line in ${Path}: ${line}" }
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $values
}

function Require-Key {
    param([hashtable]$Values, [string]$Key)
    if (-not $Values.ContainsKey($Key) -or [string]::IsNullOrWhiteSpace($Values[$Key])) {
        throw "Missing required remote config key: ${Key}"
    }
    return $Values[$Key]
}

function Test-CommandAvailable {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is not available: ${Name}"
    }
}

function New-SessionId {
    $stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $commit = (& git -C $RepoRoot rev-parse --short HEAD).Trim().ToLowerInvariant()
    $suffix = ([guid]::NewGuid().ToString("N")).Substring(0, 6)
    return "${stamp}-${commit}-${suffix}".ToLowerInvariant()
}

function Assert-SafeSessionId {
    param([string]$Value)
    if ($Value -notmatch '^[a-z0-9][a-z0-9-]{5,63}$') {
        throw "Unsafe SessionId. Use 6-64 lowercase letters, digits and hyphens."
    }
}

function ConvertTo-ShellLiteral {
    param([string]$Value)
    if ($Value.Contains("'")) { throw "Unsafe single quote in remote value." }
    return "'${Value}'"
}

function Invoke-Native {
    param([string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory = $RepoRoot)
    $display = "$FilePath $($Arguments -join ' ')"
    if ($DryRun) {
        Write-Host "[dry-run] ${display}"
        $script:LastNativeExitCode = 0
        return
    }
    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        $script:LastNativeExitCode = $LASTEXITCODE
    }
    finally { Pop-Location }
}

function Invoke-SshScript {
    param([string]$Script)
    if ($DryRun) {
        Write-Host "[dry-run] ssh ${sshTarget} bash -s"
        $script:LastNativeExitCode = 0
        return
    }
    $token = [guid]::NewGuid().ToString("N")
    $localScript = Join-Path ([System.IO.Path]::GetTempPath()) "pwos-${token}.sh"
    $remoteScript = "/tmp/pwos-${token}.sh"
    try {
        [System.IO.File]::WriteAllText(
            $localScript,
            $Script.Replace("`r`n", "`n"),
            [System.Text.UTF8Encoding]::new($false)
        )
        & scp $localScript "${sshTarget}:${remoteScript}"
        if ($LASTEXITCODE -ne 0) {
            $script:LastNativeExitCode = $LASTEXITCODE
            return
        }
        & ssh $sshTarget bash $remoteScript
        $remoteExitCode = $LASTEXITCODE
        & ssh $sshTarget rm -f -- $remoteScript
        $script:LastNativeExitCode = $remoteExitCode
    }
    finally { Remove-Item -LiteralPath $localScript -Force -ErrorAction SilentlyContinue }
}

function Stop-OnNativeFailure {
    param([string]$Operation)
    if ($script:LastNativeExitCode -ne 0) {
        Complete-Manifest -ExitCode $script:LastNativeExitCode
        [Console]::Error.WriteLine("${Operation} failed with exit code $($script:LastNativeExitCode).")
        exit $script:LastNativeExitCode
    }
}

function Save-Manifest {
    if ($DryRun) { return }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $script:ManifestPath) | Out-Null
    $script:Manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $script:ManifestPath -Encoding UTF8
}

function Add-ManifestCommand {
    param([string]$Kind, [string]$Value)
    $script:Manifest.commands += [ordered]@{
        action = $Kind
        runner = $Runner
        command = $Value
        at = (Get-Date).ToUniversalTime().ToString("o")
        completed_at = $null
        exit_code = $null
    }
    Save-Manifest
}

function Complete-Manifest {
    param([int]$ExitCode)
    if ($null -eq $script:Manifest) { return }
    $script:Manifest.completed_at = (Get-Date).ToUniversalTime().ToString("o")
    $script:Manifest.exit_code = $ExitCode
    if ($script:Manifest.commands.Count -gt 0) {
        $lastCommand = $script:Manifest.commands[-1]
        if ($lastCommand -is [System.Collections.IDictionary]) {
            $lastCommand["completed_at"] = $script:Manifest.completed_at
            $lastCommand["exit_code"] = $ExitCode
        }
        else {
            if ($null -eq $lastCommand.PSObject.Properties["completed_at"]) {
                $lastCommand | Add-Member -NotePropertyName completed_at -NotePropertyValue $null
            }
            if ($null -eq $lastCommand.PSObject.Properties["exit_code"]) {
                $lastCommand | Add-Member -NotePropertyName exit_code -NotePropertyValue $null
            }
            $lastCommand.completed_at = $script:Manifest.completed_at
            $lastCommand.exit_code = $ExitCode
        }
    }
    Save-Manifest
}

function Write-RemoteManifest {
    if ($DryRun) { return }
    Invoke-Native -FilePath "ssh" -Arguments @($sshTarget, "test", "-d", $workspace)
    if ($script:LastNativeExitCode -ne 0) {
        $script:LastNativeExitCode = 0
        Write-Host "Remote session workspace is absent; local manifest retained after cleanup."
        return
    }
    $remoteManifest = "${workspace}/session-manifest.json"
    Invoke-Native -FilePath "scp" -Arguments @($script:ManifestPath, "${sshTarget}:${remoteManifest}")
    Stop-OnNativeFailure "session manifest upload"
}

function Assert-ProviderPermission {
    param([string]$Value)
    if ($AllowProviderCalls) { return }
    $providerPattern = '(?i)(run-radar|run-signal|run-power-web|signal-monitoring-runs|power-web-runs|curl\s+.*(-x|--request)\s+post|invoke-restmethod\s+.*-method\s+post|openrouter)'
    if ($Value -match $providerPattern) {
        throw "provider_calls_blocked: use -Runner stack -AllowProviderCalls for an explicitly announced live action"
    }
}

function Sync-Workspace {
    Add-ManifestCommand -Kind "Sync" -Value "workspace archive"
    $archiveName = "pwos-${SessionId}.tar.gz"
    $archivePath = Join-Path ([System.IO.Path]::GetTempPath()) $archiveName
    $remoteArchive = "/tmp/${archiveName}"
    $excludeArgs = @(
        "--exclude=.git", "--exclude=.external", "--exclude=.venv", "--exclude=venv",
        "--exclude=node_modules", "--exclude=frontend/node_modules", "--exclude=frontend/dist",
        "--exclude=frontend/test-results",
        "--exclude=demo/output", "--exclude=.pytest_cache", "--exclude=.remote-validation",
        "--exclude=__pycache__", "--exclude=*.pyc", "--exclude=.env", "--exclude=.env.*"
    )
    if ($DryRun) {
        Write-Host "[dry-run] tar ${archivePath}; secrets, caches, databases and generated output excluded"
        $archiveSha = "dry-run"
    }
    else {
        Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
        Invoke-Native -FilePath "tar" -Arguments (@("-czf", $archivePath) + $excludeArgs + @("-C", $RepoRoot, "."))
        Stop-OnNativeFailure "workspace archive"
        $archiveSha = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    $script:Manifest.workspace_sha256 = $archiveSha
    Save-Manifest
    Invoke-Native -FilePath "scp" -Arguments @($archivePath, "${sshTarget}:${remoteArchive}")
    Stop-OnNativeFailure "workspace upload"
    $syncScript = @"
set -euo pipefail
mkdir -p $(ConvertTo-ShellLiteral $validationRoot) $(ConvertTo-ShellLiteral $releaseRoot) $(ConvertTo-ShellLiteral $sharedRoot)
test ! -L $(ConvertTo-ShellLiteral $workspace)
rm -rf -- $(ConvertTo-ShellLiteral $workspace)
mkdir -p $(ConvertTo-ShellLiteral $workspace)
remote_sha=`$(sha256sum $(ConvertTo-ShellLiteral $remoteArchive) | awk '{print `$1}')
test "`$remote_sha" = $(ConvertTo-ShellLiteral $archiveSha)
tar -xzf $(ConvertTo-ShellLiteral $remoteArchive) -C $(ConvertTo-ShellLiteral $workspace)
rm -f -- $(ConvertTo-ShellLiteral $remoteArchive)
printf '%s\n' "workspace_sha256=`$remote_sha" "workspace=$(ConvertTo-ShellLiteral $workspace)"
"@
    Invoke-SshScript $syncScript
    Stop-OnNativeFailure "remote workspace sync"
    if (-not $DryRun) { Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue }
    Write-RemoteManifest
}

function Get-ComposeExports {
    return @"
export POWER_WEB_OS_DATA_PATH=$(ConvertTo-ShellLiteral "${sharedRoot}/demo-output")
export POWER_WEB_OS_ENV_FILE=$(ConvertTo-ShellLiteral "${sharedRoot}/.env")
export POWER_WEB_OS_API_HOST_PORT=$(ConvertTo-ShellLiteral $apiPort)
export POWER_WEB_OS_FRONTEND_HOST_PORT=$(ConvertTo-ShellLiteral $frontendPort)
export POWER_WEB_OS_REDIS_HOST_PORT=$(ConvertTo-ShellLiteral $redisBind)
export POWER_WEB_OS_REMOTE_API_URL=$(ConvertTo-ShellLiteral $apiUrl)
export POWER_WEB_OS_REMOTE_FRONTEND_URL=$(ConvertTo-ShellLiteral $frontendUrl)
export POWER_WEB_OS_REMOTE_COMPOSE_PROJECT=$(ConvertTo-ShellLiteral $devComposeProject)
export POWER_WEB_OS_REMOTE_CURRENT_PATH=$(ConvertTo-ShellLiteral "${remoteBase}/current")
export VITE_POWER_WEB_OS_API_BASE_URL=$(ConvertTo-ShellLiteral $apiUrl)
export POWER_WEB_OS_CORS_ORIGINS=$(ConvertTo-ShellLiteral "${frontendUrl},http://127.0.0.1:5173,http://localhost:5173")
"@
}

if (-not (Test-Path $ConfigPath)) { throw "Missing remote config: ${ConfigPath}" }
foreach ($requiredCommand in @("git", "tar", "ssh", "scp")) { Test-CommandAvailable $requiredCommand }

$config = Read-KeyValueFile $ConfigPath
$sshTarget = Require-Key $config "POWER_WEB_OS_REMOTE_SSH_TARGET"
$remoteBase = Require-Key $config "POWER_WEB_OS_REMOTE_PATH"
$validationRoot = Require-Key $config "POWER_WEB_OS_REMOTE_VALIDATION_ROOT"
$releaseRoot = Require-Key $config "POWER_WEB_OS_REMOTE_RELEASE_ROOT"
$sharedRoot = Require-Key $config "POWER_WEB_OS_REMOTE_SHARED_ROOT"
$devComposeProject = Require-Key $config "POWER_WEB_OS_REMOTE_COMPOSE_PROJECT"
$lockPath = Require-Key $config "POWER_WEB_OS_REMOTE_LOCK_PATH"
$apiUrl = Require-Key $config "POWER_WEB_OS_REMOTE_API_URL"
$frontendUrl = Require-Key $config "POWER_WEB_OS_REMOTE_FRONTEND_URL"
$apiPort = Require-Key $config "POWER_WEB_OS_REMOTE_API_PORT"
$frontendPort = Require-Key $config "POWER_WEB_OS_REMOTE_FRONTEND_PORT"
$redisBind = Require-Key $config "POWER_WEB_OS_REMOTE_REDIS_BIND"

if (-not $SessionId) { $SessionId = New-SessionId }
Assert-SafeSessionId $SessionId
$workspace = "${validationRoot}/${SessionId}"
$composeProject = "pwos-val-${SessionId}".ToLowerInvariant()
$branch = (& git -C $RepoRoot rev-parse --abbrev-ref HEAD).Trim()
$commit = (& git -C $RepoRoot rev-parse HEAD).Trim()
$dirty = [bool]((& git -C $RepoRoot status --porcelain).Count)
$script:ManifestPath = Join-Path $SessionStore "${SessionId}/manifest.json"
if (Test-Path $script:ManifestPath) {
    $script:Manifest = Get-Content -LiteralPath $script:ManifestPath -Raw | ConvertFrom-Json
    $script:Manifest.branch = $branch
    $script:Manifest.commit = $commit
    $script:Manifest.dirty = $dirty
    $script:Manifest.completed_at = $null
    $script:Manifest.exit_code = $null
    $script:Manifest.provider_calls_allowed = [bool]$AllowProviderCalls
}
else {
    $script:Manifest = [ordered]@{
        session_id = $SessionId
        branch = $branch
        commit = $commit
        dirty = $dirty
        workspace_sha256 = ""
        server = (Require-Key $config "POWER_WEB_OS_REMOTE_HOST")
        compose_project = $composeProject
        commands = @()
        started_at = (Get-Date).ToUniversalTime().ToString("o")
        completed_at = $null
        exit_code = $null
        provider_calls_allowed = [bool]$AllowProviderCalls
    }
}
Save-Manifest

Write-Host "Remote contour session: ${SessionId}"
Write-Host "Server: $($script:Manifest.server) via ${sshTarget}"
Write-Host "Workspace: ${workspace}"
Write-Host "Compose project: ${composeProject}"
Write-Host "Provider calls allowed: $([bool]$AllowProviderCalls)"

switch ($Action) {
    "Probe" {
        Add-ManifestCommand -Kind "Probe" -Value "ssh docker compose resources paths env lock stack"
        $probeScript = @"
set -euo pipefail
command -v docker >/dev/null
docker version --format 'docker={{.Server.Version}}'
docker compose version
test -w $(ConvertTo-ShellLiteral $remoteBase)
df -Pk $(ConvertTo-ShellLiteral $remoteBase) | tail -1
awk '/MemAvailable/ {print "memory_kb=" `$2}' /proc/meminfo
if [ -f $(ConvertTo-ShellLiteral "${sharedRoot}/.env") ] || [ -f $(ConvertTo-ShellLiteral "${remoteBase}/.env") ]; then echo env=present; else echo env=missing; exit 3; fi
if flock -n $(ConvertTo-ShellLiteral $lockPath) -c true; then echo lock=available; else echo lock=busy; fi
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) -f $(ConvertTo-ShellLiteral "${remoteBase}/current/docker-compose.yml") ps 2>/dev/null || true
"@
        Invoke-SshScript $probeScript
        Stop-OnNativeFailure "remote probe"
    }
    "Sync" { Sync-Workspace }
    "Test" {
        if (-not $Command) { throw "Test requires -Command." }
        Assert-ProviderPermission $Command
        Add-ManifestCommand -Kind "Test" -Value $Command
        $service = switch ($Runner) {
            "backend" { "backend-tests" }
            "frontend" { "frontend-tests" }
            "playwright" {
                if ($Command -match '(?i)(catalog-recovery|lifecycle-control)') { "playwright-control-tests" }
                else { "playwright-tests" }
            }
            default { throw "Test runner must be backend, frontend or playwright." }
        }
        $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Command))
        $runTestScript = @"
set -euo pipefail
test -d $(ConvertTo-ShellLiteral $workspace)
cd $(ConvertTo-ShellLiteral $workspace)
$(Get-ComposeExports)
command=`$(printf '%s' $(ConvertTo-ShellLiteral $encoded) | base64 -d)
docker compose -p $(ConvertTo-ShellLiteral $composeProject) -f docker-compose.validation.yml run -T --rm --build $(ConvertTo-ShellLiteral $service) bash -lc "`$command"
"@
        $runTestEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($runTestScript))
        if ($service -eq "playwright-control-tests") {
            $testScript = @"
set -euo pipefail
locked_command=`$(printf '%s' $(ConvertTo-ShellLiteral $runTestEncoded) | base64 -d)
set +e
flock -E 75 -n $(ConvertTo-ShellLiteral $lockPath) bash -lc "`$locked_command" 2>&1 | tee $(ConvertTo-ShellLiteral "${workspace}/.remote-test-last.log")
code=`${PIPESTATUS[0]}
set -e
if [ "`$code" -eq 75 ]; then echo remote_stack_busy >&2; fi
exit "`$code"
"@
        }
        else {
            $testScript = @"
set -euo pipefail
test_command=`$(printf '%s' $(ConvertTo-ShellLiteral $runTestEncoded) | base64 -d)
set +e
bash -lc "`$test_command" 2>&1 | tee $(ConvertTo-ShellLiteral "${workspace}/.remote-test-last.log")
code=`${PIPESTATUS[0]}
set -e
exit "`$code"
"@
        }
        Invoke-SshScript $testScript
        Stop-OnNativeFailure "remote ${Runner} test"
        Write-RemoteManifest
    }
    "Deploy" {
        Sync-Workspace
        Add-ManifestCommand -Kind "Deploy" -Value "build release, activate current, start persistent stack, check HTTP"
        $release = "${releaseRoot}/${SessionId}"
        $upCommand = @"
cd $(ConvertTo-ShellLiteral "${remoteBase}/current")
$(Get-ComposeExports)
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) up -d
"@
        $upEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($upCommand))
        $deployScript = @"
set -euo pipefail
mkdir -p $(ConvertTo-ShellLiteral $sharedRoot) $(ConvertTo-ShellLiteral "${sharedRoot}/demo-output") $(ConvertTo-ShellLiteral $releaseRoot)
if [ ! -f $(ConvertTo-ShellLiteral "${sharedRoot}/.env") ]; then
  test -f $(ConvertTo-ShellLiteral "${remoteBase}/.env")
  cp $(ConvertTo-ShellLiteral "${remoteBase}/.env") $(ConvertTo-ShellLiteral "${sharedRoot}/.env")
  chmod 600 $(ConvertTo-ShellLiteral "${sharedRoot}/.env")
fi
test ! -L $(ConvertTo-ShellLiteral $release)
rm -rf -- $(ConvertTo-ShellLiteral $release)
mkdir -p $(ConvertTo-ShellLiteral $release)
cp -a $(ConvertTo-ShellLiteral "${workspace}/.") $(ConvertTo-ShellLiteral $release)
$(Get-ComposeExports)
cd $(ConvertTo-ShellLiteral $release)
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) config --quiet
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) build
previous=""
if [ -L $(ConvertTo-ShellLiteral "${remoteBase}/current") ]; then
  candidate=`$(readlink $(ConvertTo-ShellLiteral "${remoteBase}/current") 2>/dev/null || true)
  if [ -n "`$candidate" ] && [ "`$candidate" != $(ConvertTo-ShellLiteral "${remoteBase}/current") ] && [ -d "`$candidate" ]; then previous="`$candidate"; fi
fi
ln -sfn $(ConvertTo-ShellLiteral $release) $(ConvertTo-ShellLiteral "${remoteBase}/current.next")
mv -Tf $(ConvertTo-ShellLiteral "${remoteBase}/current.next") $(ConvertTo-ShellLiteral "${remoteBase}/current")
locked_command=`$(printf '%s' $(ConvertTo-ShellLiteral $upEncoded) | base64 -d)
set +e
flock -E 75 -n $(ConvertTo-ShellLiteral $lockPath) bash -lc "`$locked_command"
code=`$?
set -e
if [ "`$code" -ne 0 ]; then
  if [ "`$code" -eq 75 ]; then echo remote_stack_busy >&2; fi
  if [ -n "`$previous" ]; then
    ln -sfn "`$previous" $(ConvertTo-ShellLiteral "${remoteBase}/current.next")
    mv -Tf $(ConvertTo-ShellLiteral "${remoteBase}/current.next") $(ConvertTo-ShellLiteral "${remoteBase}/current")
  else
    rm -f -- $(ConvertTo-ShellLiteral "${remoteBase}/current")
  fi
  exit "`$code"
fi
for attempt in `$(seq 1 60); do curl -fsS $(ConvertTo-ShellLiteral "${apiUrl}/health") >/dev/null && break; sleep 2; done
curl -fsS $(ConvertTo-ShellLiteral "${apiUrl}/health") >/dev/null
curl -fsS $(ConvertTo-ShellLiteral "${apiUrl}/api/radars") >/dev/null
curl -fsS $(ConvertTo-ShellLiteral $frontendUrl) >/dev/null
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) ps
echo release=$(ConvertTo-ShellLiteral $release)
"@
        Invoke-SshScript $deployScript
        Stop-OnNativeFailure "remote deploy"
        Write-RemoteManifest
    }
    "Exec" {
        if (-not $Command) { throw "Exec requires -Command." }
        if ($Runner -ne "stack") { throw "Exec currently requires -Runner stack." }
        Assert-ProviderPermission $Command
        Add-ManifestCommand -Kind "Exec" -Value $Command
        $encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($Command))
        $stackCommand = @"
cd $(ConvertTo-ShellLiteral "${remoteBase}/current")
$(Get-ComposeExports)
command=`$(printf '%s' $(ConvertTo-ShellLiteral $encoded) | base64 -d)
bash -lc "`$command"
"@
        $stackEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($stackCommand))
        $execScript = @"
set -euo pipefail
test -d $(ConvertTo-ShellLiteral "${remoteBase}/current")
locked_command=`$(printf '%s' $(ConvertTo-ShellLiteral $stackEncoded) | base64 -d)
set +e
flock -E 75 -n $(ConvertTo-ShellLiteral $lockPath) bash -lc "`$locked_command"
code=`$?
set -e
if [ "`$code" -eq 75 ]; then echo remote_stack_busy >&2; fi
exit "`$code"
"@
        Invoke-SshScript $execScript
        Stop-OnNativeFailure "remote stack command"
        Write-RemoteManifest
    }
    "ImportHistory" {
        if ($Runner -ne "stack") { throw "ImportHistory requires -Runner stack." }
        if ($AllowProviderCalls) { throw "ImportHistory never permits provider calls." }
        $localDatabase = Join-Path $RepoRoot "demo/output/power_web_os.sqlite3"
        if (-not (Test-Path -LiteralPath $localDatabase -PathType Leaf)) {
            throw "Local history database is missing: ${localDatabase}"
        }
        foreach ($sidecar in @("${localDatabase}-wal", "${localDatabase}-shm")) {
            if (Test-Path -LiteralPath $sidecar) {
                throw "Local history database is active or not checkpointed: ${sidecar}"
            }
        }
        $databaseSha = (Get-FileHash -LiteralPath $localDatabase -Algorithm SHA256).Hash.ToLowerInvariant()
        $databaseBytes = (Get-Item -LiteralPath $localDatabase).Length
        Add-ManifestCommand -Kind "ImportHistory" -Value "checkpointed SQLite; sha256=${databaseSha}; bytes=${databaseBytes}; partial_trace_recovery=$([bool]$AllowPartialTraceRecovery)"
        $stagingDirectory = "${workspace}/history-import"
        $remoteDatabase = "${stagingDirectory}/power_web_os.sqlite3"
        $prepareScript = @"
set -euo pipefail
test ! -L $(ConvertTo-ShellLiteral $workspace)
mkdir -p $(ConvertTo-ShellLiteral $stagingDirectory)
rm -f -- $(ConvertTo-ShellLiteral $remoteDatabase) $(ConvertTo-ShellLiteral "${stagingDirectory}/power_web_os.recovered.sqlite3")
"@
        Invoke-SshScript $prepareScript
        Stop-OnNativeFailure "remote history staging"
        Invoke-Native -FilePath "scp" -Arguments @($localDatabase, "${sshTarget}:${remoteDatabase}")
        Stop-OnNativeFailure "history database upload"

        $recoveryAllowed = if ($AllowPartialTraceRecovery) { "1" } else { "0" }
        $integrityCode = @"
import os
import sqlite3
from pathlib import Path

source_path = Path("/input/power_web_os.sqlite3")
source = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
required = {"radars", "radar_runs", "radar_run_outputs"}
tables_present = {row[0] for row in source.execute("select name from sqlite_master where type='table'")}
assert required <= tables_present, sorted(required - tables_present)
integrity = source.execute("pragma integrity_check").fetchone()[0]
run_count = source.execute("select count(*) from radar_runs").fetchone()[0]
if integrity == "ok":
    source.close()
    print(f"source_integrity=ok source_run_count={run_count}")
    raise SystemExit(0)
if os.environ.get("ALLOW_PARTIAL_TRACE_RECOVERY") != "1":
    source.close()
    raise AssertionError(integrity)

target_path = Path("/input/power_web_os.recovered.sqlite3")
target_path.unlink(missing_ok=True)
target = sqlite3.connect(target_path)
target.execute("pragma foreign_keys=off")
target.execute("pragma journal_mode=off")
target.execute("pragma synchronous=off")
objects = source.execute("select type,name,tbl_name,sql,rootpage from sqlite_master where sql is not null order by case type when 'table' then 0 when 'index' then 1 when 'trigger' then 2 when 'view' then 3 else 4 end,rootpage,name").fetchall()
tables = [(name, sql) for kind, name, _, sql, _ in objects if kind == "table" and not name.startswith("sqlite_")]
for _, sql in tables:
    target.execute(sql)
target.commit()
unreadable = []
for table, _ in tables:
    columns = [row[1] for row in source.execute(f'pragma table_info("{table}")')]
    quoted = ",".join(f'"{column}"' for column in columns)
    insert_sql = f'insert into "{table}" ({quoted}) values ({",".join("?" for _ in columns)})'
    if table == "radar_run_technical_traces":
        ids = [row[0] for row in source.execute("select trace_id from radar_run_technical_traces indexed by sqlite_autoindex_radar_run_technical_traces_1")]
        for trace_id in ids:
            try:
                row = source.execute(f"select {quoted} from radar_run_technical_traces where trace_id=?", (trace_id,)).fetchone()
                if row is not None:
                    target.execute(insert_sql, row)
            except sqlite3.DatabaseError as exc:
                unreadable.append((trace_id, str(exc)))
    else:
        cursor = source.execute(f'select {quoted} from "{table}"')
        while batch := cursor.fetchmany(250):
            target.executemany(insert_sql, batch)
    target.commit()
for kind, _, _, sql, _ in objects:
    if kind in {"index", "trigger", "view"}:
        target.execute(sql)
target.commit()
recovered_integrity = target.execute("pragma integrity_check").fetchone()[0]
foreign_key_issues = target.execute("pragma foreign_key_check").fetchall()
recovered_runs = target.execute("select count(*) from radar_runs").fetchone()[0]
target.close()
source.close()
assert recovered_integrity == "ok", recovered_integrity
assert not foreign_key_issues, foreign_key_issues[:10]
assert recovered_runs == run_count, (recovered_runs, run_count)
print(f"source_integrity=recovered source_run_count={run_count} unreadable_trace_count={len(unreadable)}")
for trace_id, reason in unreadable:
    print(f"unreadable_trace={trace_id} reason={reason}")
"@
        $integrityEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($integrityCode))
        $backupDatabase = "${sharedRoot}/backups/power_web_os.sqlite3.before-${SessionId}.bak"
        $lifecycleCommand = @"
set -euo pipefail
cd $(ConvertTo-ShellLiteral "${remoteBase}/current")
$(Get-ComposeExports)
source_db=$(ConvertTo-ShellLiteral $remoteDatabase)
target_db=$(ConvertTo-ShellLiteral "${sharedRoot}/demo-output/power_web_os.sqlite3")
backup_db=$(ConvertTo-ShellLiteral $backupDatabase)
mkdir -p $(ConvertTo-ShellLiteral "${sharedRoot}/backups") $(ConvertTo-ShellLiteral "${sharedRoot}/demo-output")
remote_sha=`$(sha256sum "`$source_db" | awk '{print `$1}')
test "`$remote_sha" = $(ConvertTo-ShellLiteral $databaseSha)
integrity_code=`$(printf '%s' $(ConvertTo-ShellLiteral $integrityEncoded) | base64 -d)
docker run --rm -e ALLOW_PARTIAL_TRACE_RECOVERY=$(ConvertTo-ShellLiteral $recoveryAllowed) -v $(ConvertTo-ShellLiteral "${stagingDirectory}:/input:rw") python:3.12-slim python -c "`$integrity_code"
if [ -f $(ConvertTo-ShellLiteral "${stagingDirectory}/power_web_os.recovered.sqlite3") ]; then
  source_db=$(ConvertTo-ShellLiteral "${stagingDirectory}/power_web_os.recovered.sqlite3")
fi
import_sha=`$(sha256sum "`$source_db" | awk '{print `$1}')
test -f "`$target_db"
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) stop api worker
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) rm -f api worker backend-init
cp -a "`$target_db" "`$backup_db"
install -m 600 "`$source_db" "`$target_db.incoming"
mv -f "`$target_db.incoming" "`$target_db"
rm -f -- "`$target_db-wal" "`$target_db-shm"
set +e
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) up -d api worker
start_code=`$?
if [ "`$start_code" -eq 0 ]; then
  health_code=1
  for attempt in `$(seq 1 90); do
    if curl -fsS $(ConvertTo-ShellLiteral "${apiUrl}/health") >/dev/null; then health_code=0; break; fi
    sleep 2
  done
else
  health_code="`$start_code"
fi
set -e
if [ "`$health_code" -ne 0 ]; then
  echo history_import_failed_rolling_back >&2
  docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) stop api worker || true
  docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) rm -f api worker backend-init || true
  cp -a "`$backup_db" "`$target_db"
  rm -f -- "`$target_db-wal" "`$target_db-shm"
  docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) up -d api worker
  exit "`$health_code"
fi
curl -fsS $(ConvertTo-ShellLiteral "${apiUrl}/api/radars") >/dev/null
rm -f -- $(ConvertTo-ShellLiteral $remoteDatabase) $(ConvertTo-ShellLiteral "${stagingDirectory}/power_web_os.recovered.sqlite3")
printf '%s\n' "history_import=completed" "uploaded_source_sha256=`$remote_sha" "imported_database_sha256=`$import_sha" "backup=`$backup_db"
"@
        $lifecycleEncoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($lifecycleCommand))
        $importScript = @"
set -euo pipefail
locked_command=`$(printf '%s' $(ConvertTo-ShellLiteral $lifecycleEncoded) | base64 -d)
set +e
flock -E 75 -n $(ConvertTo-ShellLiteral $lockPath) bash -lc "`$locked_command"
code=`$?
set -e
if [ "`$code" -eq 75 ]; then echo remote_stack_busy >&2; fi
exit "`$code"
"@
        Invoke-SshScript $importScript
        Stop-OnNativeFailure "remote history import"
        Write-RemoteManifest
    }
    "Collect" {
        if (-not $Command) { throw "Collect requires one repository-relative artifact path in -Command." }
        $normalized = $Command.Replace('\', '/').TrimStart('/')
        $allowed = $normalized -match '^(docs/.+/validation/.+\.(json|md)|docs/.+\.pdf|frontend/test-results/.+|\.remote-session-summary\.json)$'
        if (-not $allowed -or $normalized.Contains("..") -or $normalized -match '(?i)(\.env|sqlite|secret|token|raw)') {
            throw "artifact_not_allowed: ${Command}"
        }
        Add-ManifestCommand -Kind "Collect" -Value $normalized
        $localPath = Join-Path $RepoRoot ($normalized.Replace('/', [IO.Path]::DirectorySeparatorChar))
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $localPath) | Out-Null
        Invoke-Native -FilePath "scp" -Arguments @("${sshTarget}:${workspace}/${normalized}", $localPath)
        Stop-OnNativeFailure "artifact collection"
    }
    "Logs" {
        $service = if ($Command) { $Command } else { "api" }
        if ($service -notmatch '^[a-z0-9-]+$') { throw "Unsafe service name." }
        Add-ManifestCommand -Kind "Logs" -Value $service
        $logScript = @"
set -euo pipefail
cd $(ConvertTo-ShellLiteral "${remoteBase}/current")
$(Get-ComposeExports)
docker compose -p $(ConvertTo-ShellLiteral $devComposeProject) logs --no-color --tail=200 $(ConvertTo-ShellLiteral $service) \
  | sed -E 's/(authorization:|api[_-]?key=|bearer )[[:graph:]]+/\1<redacted>/Ig'
"@
        Invoke-SshScript $logScript
        Stop-OnNativeFailure "remote logs"
    }
    "Cleanup" {
        Add-ManifestCommand -Kind "Cleanup" -Value "validation project and workspace only"
        $cleanupScript = @"
set -euo pipefail
case $(ConvertTo-ShellLiteral $workspace) in $(ConvertTo-ShellLiteral "${validationRoot}/")*) ;; *) echo unsafe_cleanup_target >&2; exit 64 ;; esac
cd $(ConvertTo-ShellLiteral $workspace)
$(Get-ComposeExports)
docker compose -p $(ConvertTo-ShellLiteral $composeProject) -f docker-compose.validation.yml down --volumes --remove-orphans || true
cd /
rm -rf -- $(ConvertTo-ShellLiteral $workspace)
test -d $(ConvertTo-ShellLiteral $sharedRoot)
test -L $(ConvertTo-ShellLiteral "${remoteBase}/current") -o -d $(ConvertTo-ShellLiteral "${remoteBase}/current")
echo cleanup=validation_only
"@
        Invoke-SshScript $cleanupScript
        Stop-OnNativeFailure "remote validation cleanup"
    }
}

Complete-Manifest -ExitCode 0
if ($Action -in @("Sync", "Test", "Deploy", "Exec", "ImportHistory", "Collect", "Logs")) {
    Write-RemoteManifest
}
Write-Host "Remote action ${Action} completed for session ${SessionId}."
Write-Host "Session manifest: $($script:ManifestPath)"
