[CmdletBinding()]
param(
    [switch]$CleanOnly,
    [string]$GameLogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ModId = "tw40ch"
$Timestamp = Get-Date -Format "MMdd_HHmm"
$PackageVersion = "tw40ft_dev01"
$ProjectDir = [IO.Path]::GetFullPath($PSScriptRoot)
$WorkspaceDir = [IO.Path]::GetFullPath((Join-Path $ProjectDir ".."))
$BaseDir = Join-Path $ProjectDir "base"
$SourceDir = Join-Path $ProjectDir "source"
$BuildDir = Join-Path $ProjectDir "build"
$StageDir = Join-Path $BuildDir "staging"
$StageBaseDir = Join-Path $StageDir "base"
$DistDir = Join-Path $ProjectDir "dist"
$PackagePath = Join-Path $DistDir ("{0}.scs" -f $PackageVersion)
$ReportPath = Join-Path $BuildDir "build_report.txt"
$ConversionTools = Join-Path $WorkspaceDir "tools\conversion_tools_2_21"
$ConversionMount = Join-Path $ConversionTools $ModId
$ConversionOutput = Join-Path $ConversionTools ("rsrc\{0}" -f $ModId)
$ConvertedCache = Join-Path $ConversionOutput "@cache"
$ResConvert = Join-Path $ConversionTools "bin\win_x64\tools\resconvert.exe"
$ConversionLog = Join-Path $BuildDir "mass_convert.log"
$MetadataFiles = @("manifest.sii", "mod_description.txt", "mod_description.zh_tw.txt")
$ConditionalFiles = @{
    "dlc_goodyear" = @(
        "def\vehicle\trailer_wheel\r_tire\t40_gfmx.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_gkmx.sii"
    )
    "dlc_michelin" = @(
        "def\vehicle\trailer_wheel\r_tire\t40_mxd.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxd8.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxdp.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxez.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxhd.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxld.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxlz.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxz2.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxz8.sii",
        "def\vehicle\trailer_wheel\r_tire\t40_mxze.sii"
    )
    "dlc_rims" = @(
        "def\vehicle\trailer_wheel\r_disc\t40_d01c.sii",
        "def\vehicle\trailer_wheel\r_disc\t40_d01h.sii",
        "def\vehicle\trailer_wheel\r_disc\t40_d01p.sii",
        "def\vehicle\trailer_wheel\r_disc\t40_d02c.sii",
        "def\vehicle\trailer_wheel\r_disc\t40_d02p.sii",
        "def\vehicle\trailer_wheel\r_disc\t40_d08h.sii",
        "def\vehicle\trailer_wheel\r_hub\t40_h01p.sii",
        "def\vehicle\trailer_wheel\r_hub\t40_h02p.sii",
        "def\vehicle\trailer_wheel\r_nuts\t40_n02p.sii",
        "def\vehicle\trailer_wheel\r_nuts\t40_n03c.sii",
        "def\vehicle\trailer_wheel\r_nuts\t40_n03p.sii",
        "def\vehicle\trailer_wheel\r_nuts\t40_n04c.sii",
        "def\vehicle\trailer_wheel\r_nuts\t40_n04p.sii",
        "def\vehicle\trailer_wheel\r_nuts\t40_n05p.sii"
    )
}

function Assert-ManagedPath {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd("\")
    $fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd("\") + "\"
    if (-not $fullPath.StartsWith($fullRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify path outside managed root: $fullPath"
    }
}

function Reset-Directory {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    Assert-ManagedPath -Path $Path -Root $Root
    if ([IO.Directory]::Exists($Path)) {
        [IO.Directory]::Delete($Path, $true)
    }
    [IO.Directory]::CreateDirectory($Path) | Out-Null
}

function Copy-Tree {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    if (-not [IO.Directory]::Exists($Source)) {
        throw "Source directory does not exist: $Source"
    }

    [IO.Directory]::CreateDirectory($Destination) | Out-Null
    foreach ($file in [IO.Directory]::EnumerateFiles($Source, "*", [IO.SearchOption]::AllDirectories)) {
        $relativePath = $file.Substring($Source.TrimEnd("\").Length).TrimStart("\")
        $name = [IO.Path]::GetFileName($file)
        $extension = [IO.Path]::GetExtension($file).ToLowerInvariant()
        if ($name.StartsWith(".") -or $extension -in @(".blend", ".blend1", ".blend2", ".psd", ".kra", ".xcf", ".tmp", ".bak", ".log", ".md", ".ps1", ".py")) {
            continue
        }

        $target = Join-Path $Destination $relativePath
        $targetParent = [IO.Path]::GetDirectoryName($target)
        [IO.Directory]::CreateDirectory($targetParent) | Out-Null
        [IO.File]::Copy($file, $target, $true)
    }
}

function Copy-PreconvertedAssets {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Destination
    )

    $allowedExtensions = @(".pmd", ".pmg", ".pmc")
    foreach ($file in [IO.Directory]::EnumerateFiles($Source, "*", [IO.SearchOption]::AllDirectories)) {
        if ([IO.Path]::GetExtension($file).ToLowerInvariant() -notin $allowedExtensions) {
            continue
        }

        $relativePath = $file.Substring($Source.TrimEnd("\").Length).TrimStart("\")
        $target = Join-Path $Destination $relativePath
        $targetParent = [IO.Path]::GetDirectoryName($target)
        [IO.Directory]::CreateDirectory($targetParent) | Out-Null
        if (-not [IO.File]::Exists($target)) {
            [IO.File]::Copy($file, $target, $false)
        }
    }
}

function Remove-ManagedFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Root
    )

    Assert-ManagedPath -Path $Path -Root $Root
    if ([IO.File]::Exists($Path)) {
        [IO.File]::Delete($Path)
    }
}

function Move-StagedFile {
    param(
        [Parameter(Mandatory = $true)][string]$RelativePath,
        [Parameter(Mandatory = $true)][string]$DestinationRoot
    )

    $source = Join-Path $StageBaseDir $RelativePath
    $destination = Join-Path $DestinationRoot $RelativePath
    Assert-ManagedPath -Path $source -Root $StageDir
    Assert-ManagedPath -Path $destination -Root $StageDir
    if (-not [IO.File]::Exists($source)) {
        throw "Conditional package source is missing: $RelativePath"
    }
    if ([IO.File]::Exists($destination)) {
        throw "Conditional package destination already exists: $destination"
    }

    $destinationParent = [IO.Path]::GetDirectoryName($destination)
    [IO.Directory]::CreateDirectory($destinationParent) | Out-Null
    [IO.File]::Move($source, $destination)
}

foreach ($directory in @(
    $BaseDir,
    (Join-Path $BaseDir "def"),
    (Join-Path $BaseDir "vehicle"),
    (Join-Path $BaseDir "material"),
    (Join-Path $BaseDir "locale\zh_tw"),
    (Join-Path $SourceDir "blender"),
    (Join-Path $SourceDir "textures"),
    $BuildDir,
    $DistDir
)) {
    [IO.Directory]::CreateDirectory($directory) | Out-Null
}

if ($CleanOnly) {
    Reset-Directory -Path $BuildDir -Root $ProjectDir
    Remove-ManagedFile -Path $PackagePath -Root $ProjectDir
    Reset-Directory -Path $ConversionMount -Root $ConversionTools
    Reset-Directory -Path $ConversionOutput -Root $ConversionTools
    "Cleaned build outputs for $ModId."
    exit 0
}

if (-not [IO.File]::Exists($ResConvert)) {
    throw "Conversion Tools executable not found: $ResConvert"
}

$stopwatch = [Diagnostics.Stopwatch]::StartNew()
Reset-Directory -Path $BuildDir -Root $ProjectDir
Reset-Directory -Path $StageDir -Root $ProjectDir
Reset-Directory -Path $ConversionMount -Root $ConversionTools
Reset-Directory -Path $ConversionOutput -Root $ConversionTools
Remove-ManagedFile -Path $PackagePath -Root $ProjectDir

Copy-Tree -Source $BaseDir -Destination $ConversionMount

$conversionToolDir = [IO.Path]::GetDirectoryName($ResConvert)
$previousLocation = Get-Location
try {
    Set-Location -LiteralPath $conversionToolDir
    $conversionMessages = @(& $ResConvert -update -root $ModId 2>&1 | ForEach-Object { $_.ToString() })
    $conversionExitCode = $LASTEXITCODE
}
finally {
    Set-Location -LiteralPath $previousLocation
}

if ($conversionMessages.Count -gt 0) {
    [IO.File]::WriteAllLines($ConversionLog, $conversionMessages, [Text.UTF8Encoding]::new($false))
}
elseif (-not [IO.File]::Exists($ConversionLog)) {
    [IO.File]::WriteAllText($ConversionLog, "Conversion completed without console output.`r`n", [Text.UTF8Encoding]::new($false))
}

if ($conversionExitCode -ne 0) {
    throw "Conversion Tools failed with exit code $conversionExitCode."
}
if (-not [IO.Directory]::Exists($ConvertedCache)) {
    throw "Converted cache was not created: $ConvertedCache"
}

Copy-Tree -Source $ConvertedCache -Destination $StageBaseDir
Copy-PreconvertedAssets -Source $BaseDir -Destination $StageBaseDir

foreach ($metadataFile in $MetadataFiles) {
    Move-StagedFile -RelativePath $metadataFile -DestinationRoot $StageDir
}

$manifestPath = Join-Path $StageDir "manifest.sii"
if ([IO.File]::Exists($manifestPath)) {
    $manifestContent = [IO.File]::ReadAllText($manifestPath, [Text.Encoding]::ASCII)
    $displayNameTimestamp = Get-Date -Format "MMddHHmm"
    $manifestContent = $manifestContent -replace '(display_name:\s*").*?(")', "`${1}TW40ft_$displayNameTimestamp`$2"
    [IO.File]::WriteAllText($manifestPath, $manifestContent, [Text.Encoding]::ASCII)
}

foreach ($section in $ConditionalFiles.Keys) {
    $sectionRoot = Join-Path $StageDir $section
    foreach ($relativePath in $ConditionalFiles[$section]) {
        Move-StagedFile -RelativePath $relativePath -DestinationRoot $sectionRoot
    }
}

$previewImage = Join-Path $BaseDir "mod_icon.jpg"
if ([IO.File]::Exists($previewImage)) {
    [IO.File]::Copy($previewImage, (Join-Path $StageDir "mod_icon.jpg"), $true)
}

foreach ($requiredFile in $MetadataFiles) {
    $requiredPath = Join-Path $StageDir $requiredFile
    if (-not [IO.File]::Exists($requiredPath)) {
        throw "Required package file is missing after conversion: $requiredFile"
    }
}

$manifestText = [IO.File]::ReadAllText((Join-Path $StageDir "manifest.sii"))
if ($manifestText -match 'dlc_dependencies\[\]') {
    throw "Conditional package must not declare hard DLC dependencies."
}

foreach ($section in $ConditionalFiles.Keys) {
    foreach ($relativePath in $ConditionalFiles[$section]) {
        if ([IO.File]::Exists((Join-Path $StageBaseDir $relativePath))) {
            throw "Conditional file remained in base package: $relativePath"
        }
        if (-not [IO.File]::Exists((Join-Path (Join-Path $StageDir $section) $relativePath))) {
            throw "Conditional file is missing from $section package: $relativePath"
        }
    }
}

foreach ($unexpectedRoot in @("def", "vehicle", "material", "automat")) {
    if ([IO.Directory]::Exists((Join-Path $StageDir $unexpectedRoot))) {
        throw "Game content must be inside a conditional package section: $unexpectedRoot"
    }
}

$invalidMaterialSources = @(
    [IO.Directory]::EnumerateFiles($StageDir, "*.mat", [IO.SearchOption]::AllDirectories) |
        Where-Object { [IO.File]::ReadAllText($_) -match 'source\s*:\s*"\.tobj"' }
)
if ($invalidMaterialSources.Count -gt 0) {
    Write-Warning "Converted materials contain empty texture paths (conversion tools placeholder): $($invalidMaterialSources -join ', ')"
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::Open($PackagePath, [System.IO.Compression.ZipArchiveMode]::Create)
try {
    # SCS scanners enumerate virtual directories. Explicit entries are required;
    # CreateFromDirectory only writes files and makes dealer definitions invisible.
    foreach ($directory in [IO.Directory]::EnumerateDirectories($StageDir, "*", [IO.SearchOption]::AllDirectories)) {
        $relativeDirectory = $directory.Substring($StageDir.TrimEnd("\").Length).TrimStart("\").Replace("\", "/") + "/"
        $directoryEntry = $archive.CreateEntry($relativeDirectory)
        $directoryEntry.ExternalAttributes = 0x10
    }

    foreach ($file in [IO.Directory]::EnumerateFiles($StageDir, "*", [IO.SearchOption]::AllDirectories)) {
        $relativeFile = $file.Substring($StageDir.TrimEnd("\").Length).TrimStart("\").Replace("\", "/")
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile(
            $archive,
            $file,
            $relativeFile,
            [IO.Compression.CompressionLevel]::Optimal
        ) | Out-Null
    }
}
finally {
    $archive.Dispose()
}

$conversionLogText = [IO.File]::ReadAllText($ConversionLog)
$conversionErrorCount = [regex]::Matches($conversionLogText, "(?im)\berror\b").Count
$gameErrorCount = -1
$modErrorCount = -1
if ($GameLogPath) {
    $resolvedGameLog = [IO.Path]::GetFullPath($GameLogPath)
    if (-not [IO.File]::Exists($resolvedGameLog)) {
        throw "Game log does not exist: $resolvedGameLog"
    }

    $gameLogLines = [IO.File]::ReadAllLines($resolvedGameLog)
    $gameErrorLines = @($gameLogLines | Where-Object { $_ -match "<ERROR>" })
    $modErrorLines = @($gameErrorLines | Where-Object { $_ -match $ModId })
    $gameErrorCount = $gameErrorLines.Count
    $modErrorCount = $modErrorLines.Count
    [IO.File]::Copy($resolvedGameLog, (Join-Path $BuildDir "game.log.txt"), $true)
}

$stopwatch.Stop()
$packageInfo = [IO.FileInfo]::new($PackagePath)
$report = @(
    "status=success",
    "mod_id=$ModId",
    "package=$PackagePath",
    "package_bytes=$($packageInfo.Length)",
    "elapsed_seconds=$([Math]::Round($stopwatch.Elapsed.TotalSeconds, 3))",
    "conversion_exit_code=$conversionExitCode",
    "conversion_error_count=$conversionErrorCount",
    "game_error_count=$gameErrorCount",
    "mod_error_count=$modErrorCount"
)
[IO.File]::WriteAllLines($ReportPath, $report, [Text.UTF8Encoding]::new($false))

$report
