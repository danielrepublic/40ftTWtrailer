[CmdletBinding()]
param(
    [switch]$InstallVendorTools
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = [IO.Path]::GetFullPath($PSScriptRoot)
$Venv = Join-Path $Root ".venv"
$Vendor = Join-Path $Root "tools\vendor"
$ConversionTools = Join-Path $Vendor "conversion_tools"
$Extractor = Join-Path $Vendor "scs_extractor\scs_extractor.exe"
$ConverterPix = Join-Path $Vendor "converter_pix.exe"
$LegacyConversion = Join-Path $Root "tools\conversion_tools_2_21"
$LegacyExtractor = Join-Path $Root "tools\scs_extractor_1_55\scs_extractor.exe"
$LegacyConverterPix = Join-Path $Root "tools\converter_pix.exe"

function Find-Python312 {
    $commands = @(
        (Get-Command python -ErrorAction SilentlyContinue),
        (Get-Command py -ErrorAction SilentlyContinue)
    )
    foreach ($command in $commands) {
        if (-not $command) { continue }
        if ($command.Name -eq "py.exe") {
            $candidate = @("-3.12")
            $version = (& $command.Source "-3.12" "--version" 2>$null | Out-String).Trim()
        } else {
            $candidate = @()
            $version = (& $command.Source "--version" 2>$null | Out-String).Trim()
        }
        if ($version -match "Python 3\.12\.") {
            return @{ Path = $command.Source; Arguments = $candidate }
        }
    }
    return $null
}

function Install-Python312 {
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        & winget install --id Python.Python.3.12 --scope machine --exact --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) {
            throw "winget could not install Python 3.12. Rerun setup.ps1 from an elevated terminal or install Python manually."
        }
        return
    }

    $installerUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-amd64.exe"
    $installer = Join-Path ([IO.Path]::GetTempPath()) "python-3.12.10-amd64.exe"
    Invoke-WebRequest -Uri $installerUrl -OutFile $installer
    & $installer /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    if ($LASTEXITCODE -ne 0) {
        throw "The official Python 3.12 installer failed. Rerun setup.ps1 from an elevated terminal or install Python manually."
    }
    Remove-Item -LiteralPath $installer -Force
}

function Copy-LegacyVendorFiles {
    New-Item -ItemType Directory -Path $Vendor -Force | Out-Null
    if (-not (Test-Path -LiteralPath $ConversionTools) -and (Test-Path -LiteralPath $LegacyConversion)) {
        New-Item -ItemType Directory -Path $ConversionTools -Force | Out-Null
        Get-ChildItem -LiteralPath $LegacyConversion -Force | Copy-Item -Destination $ConversionTools -Recurse -Force
    }
    if (-not (Test-Path -LiteralPath $Extractor) -and (Test-Path -LiteralPath $LegacyExtractor)) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $Extractor) -Force | Out-Null
        Copy-Item -LiteralPath $LegacyExtractor -Destination $Extractor -Force
    }
    if (-not (Test-Path -LiteralPath $ConverterPix) -and (Test-Path -LiteralPath $LegacyConverterPix)) {
        Copy-Item -LiteralPath $LegacyConverterPix -Destination $ConverterPix -Force
    }
}

function Install-VendorTools {
    Copy-LegacyVendorFiles
    if (-not (Test-Path -LiteralPath $ConversionTools)) {
        throw "Conversion Tools 2.21 is missing. Download https://download.eurotrucksimulator2.com/conversion_tools_2_21.zip and extract it to $ConversionTools."
    }
    if (-not (Test-Path -LiteralPath $Extractor)) {
        throw "SCS Extractor is missing. Download https://download.eurotrucksimulator2.com/scs_extractor_1_55.zip and place scs_extractor.exe at $Extractor."
    }
    if (-not (Test-Path -LiteralPath $ConverterPix)) {
        throw "ConverterPIX is missing. Place converter_pix.exe at $ConverterPix."
    }
    if (Test-Path -LiteralPath $LegacyConversion) { Remove-Item -LiteralPath $LegacyConversion -Recurse -Force }
    if (Test-Path -LiteralPath (Split-Path -Parent $LegacyExtractor)) { Remove-Item -LiteralPath (Split-Path -Parent $LegacyExtractor) -Recurse -Force }
    if (Test-Path -LiteralPath $LegacyConverterPix) { Remove-Item -LiteralPath $LegacyConverterPix -Force }
}

$python = Find-Python312
if (-not $python) {
    Install-Python312
    $python = Find-Python312
    if (-not $python) { throw "Python 3.12 was installed but is not visible in the current PATH. Restart the terminal and rerun setup.ps1." }
}

& $python.Path @($python.Arguments) -m venv $Venv
if ($LASTEXITCODE -ne 0) { throw "Failed to create Python venv at $Venv" }

$venvPython = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) { throw "Python venv executable was not created: $venvPython" }
& $venvPython -c "import sys; import tools.build; print(sys.version)"
if ($LASTEXITCODE -ne 0) { throw "The project build package could not be imported from the venv." }

if ($InstallVendorTools) { Install-VendorTools }

Write-Output "Python 3.12 venv ready: $Venv"
if (-not $InstallVendorTools) { Write-Output "Run .\setup.ps1 -InstallVendorTools to migrate/check external SCS tools." }
