[CmdletBinding()]
param(
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptRoot "..")
$ConfigPath = Join-Path $RepoRoot "deploy/remote-dev.env"
$LocalEnvPath = Join-Path $RepoRoot ".env"

function Read-KeyValueFile {
    param([string]$Path)

    $values = @{}
    foreach ($line in Get-Content -Path $Path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed.Length -eq 0 -or $trimmed.StartsWith("#")) {
            continue
        }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2) {
            throw "Invalid config line in ${Path}: ${line}"
        }
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $values
}

function Require-Key {
    param(
        [hashtable]$Values,
        [string]$Key
    )

    if (-not $Values.ContainsKey($Key) -or [string]::IsNullOrWhiteSpace($Values[$Key])) {
        throw "Missing required deployment config key: ${Key}"
    }
    return $Values[$Key]
}

function Test-CommandAvailable {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command is not available: ${Name}"
    }
}

function Invoke-External {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $RepoRoot
    )

    $display = "$FilePath $($Arguments -join ' ')"
    if ($DryRun) {
        Write-Host "[dry-run] ${display}"
        return
    }

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed (${LASTEXITCODE}): ${display}"
        }
    }
    finally {
        Pop-Location
    }
}

function Wait-HttpOk {
    param(
        [string]$Url,
        [string]$Name,
        [int]$Attempts = 30,
        [int]$DelaySeconds = 3
    )

    if ($DryRun) {
        Write-Host "[dry-run] would check ${Name}: ${Url}"
        return
    }

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 10
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
                Write-Host "${Name} OK: ${Url}"
                return
            }
        }
        catch {
            if ($i -eq $Attempts) {
                throw "${Name} did not become healthy at ${Url}: $($_.Exception.Message)"
            }
        }
        Start-Sleep -Seconds $DelaySeconds
    }
}

if (-not (Test-Path $ConfigPath)) {
    throw "Missing deployment config: ${ConfigPath}"
}
if (-not (Test-Path $LocalEnvPath)) {
    throw "Missing local .env. Create it before deploying; it will not be printed."
}

Test-CommandAvailable "git"
Test-CommandAvailable "tar"
Test-CommandAvailable "ssh"
Test-CommandAvailable "scp"

$config = Read-KeyValueFile -Path $ConfigPath
$sshTarget = Require-Key $config "POWER_WEB_OS_REMOTE_SSH_TARGET"
$remotePath = Require-Key $config "POWER_WEB_OS_REMOTE_PATH"
$apiUrl = Require-Key $config "POWER_WEB_OS_REMOTE_API_URL"
$frontendUrl = Require-Key $config "POWER_WEB_OS_REMOTE_FRONTEND_URL"
$apiPort = Require-Key $config "POWER_WEB_OS_REMOTE_API_PORT"
$redisBind = Require-Key $config "POWER_WEB_OS_REMOTE_REDIS_BIND"

$corsOrigins = "${frontendUrl},http://127.0.0.1:5173,http://localhost:5173"
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$archiveName = "power-web-os-remote-dev-${timestamp}.tar.gz"
$archivePath = Join-Path ([System.IO.Path]::GetTempPath()) $archiveName
$remoteArchivePath = "/tmp/${archiveName}"
$remoteEnvPath = "/tmp/power-web-os-remote-dev-${timestamp}.env"

$branch = (git -C $RepoRoot rev-parse --abbrev-ref HEAD).Trim()
$commit = (git -C $RepoRoot rev-parse --short HEAD).Trim()
$status = git -C $RepoRoot status --short --branch

Write-Host "Remote dev deployment target: ${sshTarget}:${remotePath}"
Write-Host "Frontend URL: ${frontendUrl}"
Write-Host "API URL: ${apiUrl}"
Write-Host "Branch/commit: ${branch} ${commit}"
Write-Host "Git status:"
$status | ForEach-Object { Write-Host "  ${_}" }

$excludeArgs = @(
    "--exclude=.git",
    "--exclude=.external",
    "--exclude=.venv",
    "--exclude=venv",
    "--exclude=node_modules",
    "--exclude=frontend/node_modules",
    "--exclude=frontend/dist",
    "--exclude=demo/output",
    "--exclude=.pytest_cache",
    "--exclude=.wiki-build",
    "--exclude=__pycache__",
    "--exclude=*.pyc",
    "--exclude=.env"
)

if ($DryRun) {
    Write-Host "[dry-run] would create archive ${archivePath}"
    Write-Host "[dry-run] archive excludes: $($excludeArgs -join ', ')"
}
else {
    if (Test-Path $archivePath) {
        Remove-Item -LiteralPath $archivePath -Force
    }
    Push-Location $RepoRoot
    try {
        & tar -czf $archivePath @excludeArgs -C $RepoRoot "."
        if ($LASTEXITCODE -ne 0) {
            throw "tar failed with exit code ${LASTEXITCODE}"
        }
    }
    finally {
        Pop-Location
    }
}

Invoke-External -FilePath "scp" -Arguments @($archivePath, "${sshTarget}:${remoteArchivePath}")
if ($DryRun) {
    Write-Host "[dry-run] would copy local .env to remote temporary env file (contents redacted)"
}
else {
    Invoke-External -FilePath "scp" -Arguments @($LocalEnvPath, "${sshTarget}:${remoteEnvPath}")
}

$remoteCommand = @"
set -euo pipefail
mkdir -p '$remotePath'
tar -xzf '$remoteArchivePath' -C '$remotePath'
mv '$remoteEnvPath' '$remotePath/.env'
chmod 600 '$remotePath/.env'
cd '$remotePath'
python3 - "`$PWD/.env" '$apiPort' '$redisBind' '$apiUrl' '$corsOrigins' <<'PY'
import sys
from pathlib import Path

env_path = Path(sys.argv[1])
api_port = sys.argv[2]
redis_bind = sys.argv[3]
api_url = sys.argv[4]
cors_origins = sys.argv[5]

overrides = {
    "POWER_WEB_OS_API_HOST_PORT": api_port,
    "POWER_WEB_OS_REDIS_HOST_PORT": redis_bind,
    "VITE_POWER_WEB_OS_API_BASE_URL": api_url,
    "POWER_WEB_OS_CORS_ORIGINS": cors_origins,
}

lines = env_path.read_text(encoding="utf-8").splitlines()
seen = set()
updated = []
for line in lines:
    if not line or line.lstrip().startswith("#") or "=" not in line:
        updated.append(line)
        continue
    key = line.split("=", 1)[0].strip()
    if key in overrides:
        updated.append(f"{key}={overrides[key]}")
        seen.add(key)
    else:
        updated.append(line)

for key, value in overrides.items():
    if key not in seen:
        updated.append(f"{key}={value}")

env_path.write_text("\n".join(updated) + "\n", encoding="utf-8")
PY
docker compose config --quiet
docker compose up --build -d
docker compose ps
rm -f '$remoteArchivePath'
"@

Invoke-External -FilePath "ssh" -Arguments @($sshTarget, $remoteCommand)

Wait-HttpOk -Url "${apiUrl}/health" -Name "API health"
Wait-HttpOk -Url "${apiUrl}/api/radars" -Name "Radar catalog"
Wait-HttpOk -Url $frontendUrl -Name "Frontend"

if (-not $DryRun -and (Test-Path $archivePath)) {
    Remove-Item -LiteralPath $archivePath -Force
}

if ($DryRun) {
    Write-Host "Remote dev deploy dry-run completed."
}
else {
    Write-Host "Remote dev deploy completed."
}
Write-Host "Logs:"
Write-Host "  ssh ${sshTarget} `"cd ${remotePath} && docker compose logs --tail=100 api`""
Write-Host "  ssh ${sshTarget} `"cd ${remotePath} && docker compose logs --tail=100 worker`""
Write-Host "  ssh ${sshTarget} `"cd ${remotePath} && docker compose logs --tail=100 frontend`""
