[CmdletBinding()]
param(
    [switch]$CleanOnly,
    [string]$Ets2Path,
    [string]$ModDirectory,
    [string]$GameLogPath,
    [string]$ConfigPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $VenvPython)) {
    throw "Python venv is missing: $VenvPython. Run .\setup.ps1 first."
}

$arguments = @("-m", "tools.build", "--root", $ProjectRoot)
if ($CleanOnly) { $arguments += "--clean" }
if ($Ets2Path) { $arguments += @("--ets2-path", $Ets2Path) }
if ($ModDirectory) { $arguments += @("--mod-directory", $ModDirectory) }
if ($GameLogPath) { $arguments += @("--game-log", $GameLogPath) }
if ($ConfigPath) { $arguments += @("--config", $ConfigPath) }

Push-Location $ProjectRoot
try {
    & $VenvPython @arguments
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
finally {
    Pop-Location
}
