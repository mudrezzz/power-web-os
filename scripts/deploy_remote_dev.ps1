[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$SessionId = ""
)

$arguments = @(
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $PSScriptRoot "remote_dev.ps1"),
    "-Action", "Deploy"
)
if ($SessionId) { $arguments += @("-SessionId", $SessionId) }
if ($DryRun) { $arguments += "-DryRun" }

& powershell @arguments
exit $LASTEXITCODE
