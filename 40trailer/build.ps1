[CmdletBinding()]
param(
    [switch]$CleanOnly,
    [string]$Ets2Path,
    [string]$ModDirectory,
    [string]$GameLogPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ModId = "tw40ch"
$McpPort = 9877
$PackageName = "tw40ch_0.2.0-dev.scs"
$ProjectDir = [IO.Path]::GetFullPath($PSScriptRoot)
$WorkspaceDir = [IO.Path]::GetFullPath((Join-Path $ProjectDir ".."))
$BaseDir = Join-Path $ProjectDir "base"
$BuildDir = Join-Path $ProjectDir "build"
$ToolCacheDir = Join-Path $BuildDir "tool-cache"
$StageDir = Join-Path $BuildDir "staging"
$StageBaseDir = Join-Path $StageDir "base"
$DistDir = Join-Path $ProjectDir "dist"
$PackagePath = Join-Path $DistDir $PackageName
$SourceBlend = Join-Path $ProjectDir "source\blender\tw40ch_chassis.blend"
$ExportScript = Join-Path $WorkspaceDir "tools\export_v2_chassis.py"
$ConversionTools = Join-Path $WorkspaceDir "tools\conversion_tools_2_21"
$Extractor = Join-Path $WorkspaceDir "tools\scs_extractor_1_55\scs_extractor.exe"
$ConversionMount = Join-Path $ConversionTools $ModId
$ConversionOutput = Join-Path $ConversionTools "rsrc\$ModId"
$ConvertedCache = Join-Path $ConversionOutput "@cache"
$ResConvert = Join-Path $ConversionTools "bin\win_x64\tools\resconvert.exe"
$AssetDir = Join-Path $BaseDir "vehicle\trailer_owned\tw40ch"
$MidFormatDir = Join-Path $BaseDir ".generated\tw40ch"
$McpResponseLog = Join-Path $BuildDir "blender_mcp_response.log"
$BlenderExportLog = Join-Path $BuildDir "blender_export.log"
$ConversionLog = Join-Path $BuildDir "mass_convert.log"
$ReportPath = Join-Path $BuildDir "build_report.txt"
$ContentManifest = Join-Path $BuildDir "package_content_manifest.tsv"
$InputManifest = Join-Path $BuildDir "package_input_manifest.tsv"
$LastContentManifest = Join-Path $BuildDir "last_package_content_manifest.tsv"
$LastInputManifest = Join-Path $BuildDir "last_package_input_manifest.tsv"

$Parts = @("defaultpart", "brace_on", "brace_off", "cables_on", "cables_off")
$RequiredEffectDefinitions = @(
    "effect_family.sii",
    "eut2_heightmap_transition_config.sui",
    "eut2_interfaces.sui",
    "flavors.sui",
    "inputs.sui",
    "samplers.sui",
    "uniforms.sui",
    "vas.sui"
)
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
    param([string]$Path, [string]$Root)
    $fullPath = [IO.Path]::GetFullPath($Path).TrimEnd("\")
    $fullRoot = [IO.Path]::GetFullPath($Root).TrimEnd("\") + "\"
    if (-not $fullPath.StartsWith($fullRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to modify path outside managed root: $fullPath"
    }
}

function Reset-Directory {
    param([string]$Path, [string]$Root)
    Assert-ManagedPath -Path $Path -Root $Root
    if ([IO.Directory]::Exists($Path)) { [IO.Directory]::Delete($Path, $true) }
    [IO.Directory]::CreateDirectory($Path) | Out-Null
}

function Copy-Tree {
    param([string]$Source, [string]$Destination)
    foreach ($file in [IO.Directory]::EnumerateFiles($Source, "*", [IO.SearchOption]::AllDirectories)) {
        $extension = [IO.Path]::GetExtension($file).ToLowerInvariant()
        if ([IO.Path]::GetFileName($file).StartsWith(".") -or $extension -in @(".blend", ".blend1", ".blend2", ".psd", ".kra", ".xcf", ".tmp", ".bak", ".log", ".md", ".ps1", ".py")) { continue }
        $relative = $file.Substring($Source.TrimEnd("\").Length).TrimStart("\")
        if ($relative.StartsWith(".generated\", [StringComparison]::OrdinalIgnoreCase)) { continue }
        $target = Join-Path $Destination $relative
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
        [IO.File]::Copy($file, $target, $true)
    }
}

function Copy-PreconvertedAssets {
    param([string]$Source, [string]$Destination)
    foreach ($file in [IO.Directory]::EnumerateFiles($Source, "*", [IO.SearchOption]::AllDirectories)) {
        if ([IO.Path]::GetExtension($file).ToLowerInvariant() -notin @(".pmd", ".pmg", ".pmc")) { continue }
        $relative = $file.Substring($Source.TrimEnd("\").Length).TrimStart("\")
        $target = Join-Path $Destination $relative
        if (-not [IO.File]::Exists($target)) {
            [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
            [IO.File]::Copy($file, $target, $false)
        }
    }
}

function Invoke-McpCode {
    param([string]$Code)
    $client = $null
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        $client = [Net.Sockets.TcpClient]::new()
        $client.ReceiveTimeout = 300000
        try {
            $client.Connect("127.0.0.1", $McpPort)
            break
        }
        catch {
            $client.Dispose()
            $client = $null
            if ($attempt -eq 30) { throw "Blender MCP is unavailable on 127.0.0.1:$McpPort after 30 seconds. Start the canonical V2 Blender GUI server before building." }
            Start-Sleep -Seconds 1
        }
    }
    try {
        $request = @{ type = "execute_code"; params = @{ code = $Code } } | ConvertTo-Json -Compress -Depth 5
        $stream = $client.GetStream()
        $bytes = [Text.Encoding]::UTF8.GetBytes($request)
        $stream.Write($bytes, 0, $bytes.Length)
        $buffer = New-Object byte[] 65536
        $count = $stream.Read($buffer, 0, $buffer.Length)
        if ($count -le 0) { throw "Blender MCP returned an empty response." }
        return [Text.Encoding]::UTF8.GetString($buffer, 0, $count)
    }
    finally {
        $client.Dispose()
    }
}

function Get-Ets2Path {
    if ($Ets2Path) { return [IO.Path]::GetFullPath($Ets2Path) }
    $candidate = "C:\Program Files (x86)\Steam\steamapps\common\Euro Truck Simulator 2"
    if ([IO.Directory]::Exists($candidate)) { return $candidate }
    throw "ETS2 was not found in the default Steam library. Provide -Ets2Path <installation-directory>."
}

function Ensure-EffectResources {
    param([string]$GamePath)
    if (-not [IO.File]::Exists($Extractor)) { throw "SCS Game Archive Extractor not found: $Extractor" }
    $toolBase = Join-Path $ConversionTools "base"
    $interfaces = Join-Path $toolBase "effect\eut2_interfaces.sui"
    if (-not [IO.File]::Exists($interfaces)) {
        & $Extractor (Join-Path $GamePath "effect.scs") $toolBase
        if ($LASTEXITCODE -ne 0) { throw "Failed to extract ETS2 effect.scs." }
    }

    $cacheDefinitionDir = Join-Path $ToolCacheDir "ets2-1.60.1.7\effect-def"
    if (-not [IO.File]::Exists((Join-Path $cacheDefinitionDir "effect_family.sii"))) {
        $temporaryExtract = Join-Path $ToolCacheDir "base-extract"
        Reset-Directory -Path $temporaryExtract -Root $ProjectDir
        & $Extractor (Join-Path $GamePath "base.scs") $temporaryExtract
        if ($LASTEXITCODE -ne 0) { throw "Failed to extract ETS2 base.scs." }
        $sourceDefinitionDir = Join-Path $temporaryExtract "effect\def"
        if (-not [IO.File]::Exists((Join-Path $sourceDefinitionDir "effect_family.sii"))) { throw "ETS2 base.scs did not contain effect/def/effect_family.sii." }
        [IO.Directory]::CreateDirectory($cacheDefinitionDir) | Out-Null
        Copy-Item -Path (Join-Path $sourceDefinitionDir "*") -Destination $cacheDefinitionDir -Recurse -Force
        [IO.Directory]::Delete($temporaryExtract, $true)
    }

    foreach ($name in $RequiredEffectDefinitions) {
        if (-not [IO.File]::Exists((Join-Path $cacheDefinitionDir $name))) { throw "Effect cache is incomplete: $name" }
    }

    $mount = Join-Path $toolBase "effect\def"
    if ([IO.Directory]::Exists($mount) -or [IO.File]::Exists($mount)) {
        $item = Get-Item -LiteralPath $mount -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            # Delete only the old junction, never the external cache it targets.
            [IO.Directory]::Delete($mount)
        }
        else {
            Remove-Item -LiteralPath $mount -Force -Recurse
        }
    }
    New-Item -ItemType Junction -Path $mount -Target $cacheDefinitionDir | Out-Null
}

function Assert-ExportContract {
    param([string]$Directory)
    $pim = Join-Path $Directory "chassis.pim"
    $pit = Join-Path $Directory "chassis.pit"
    $pic = Join-Path $Directory "chassis.pic"
    foreach ($path in @($pim, $pit, $pic)) { if (-not [IO.File]::Exists($path)) { throw "Missing export output: $path" } }
    $texts = @{ PIM = [IO.File]::ReadAllText($pim); PIT = [IO.File]::ReadAllText($pit); PIC = [IO.File]::ReadAllText($pic) }
    foreach ($label in $texts.Keys) {
        $text = $texts[$label]
        if ($text -notmatch '(?m)^\s*PartCount:\s+5\s*$') { throw "$label does not declare exactly five parts." }
        foreach ($part in $Parts) {
            if ($text -notmatch ('(?s)Part \{\s+Name: "' + [regex]::Escape($part) + '"')) { throw "$label is missing part $part." }
        }
    }
    if ($texts.PIT -match 'Effect: "(eut2\.default)?"') { throw "PIT contains an empty/default material effect." }
    foreach ($effect in @('eut2.truckpaint', 'eut2.dif.spec')) {
        if ($texts.PIT -notmatch [regex]::Escape('Effect: "' + $effect + '"')) { throw "PIT is missing $effect." }
    }
    if ($texts.PIT -notmatch [regex]::Escape('Value: "/material/environment/vehicle_reflection"')) { throw "PIT is missing vehicle_reflection." }
    $pieceCount = ([regex]::Matches($texts.PIM, '(?m)^Piece \{')).Count
    $positionStreamCount = ([regex]::Matches($texts.PIM, 'Tag: "_POSITION"')).Count
    $uvStreamCount = ([regex]::Matches($texts.PIM, 'Tag: "_UV0"')).Count
    if ($pieceCount -eq 0 -or $positionStreamCount -ne $pieceCount -or $uvStreamCount -ne $pieceCount) { throw "Every PIM piece must contain POSITION and UV0 vertex streams." }
    if (([regex]::Matches($texts.PIC, 'Type: "Cylinder"')).Count -ne 1 -or ([regex]::Matches($texts.PIC, 'Type: "Box"')).Count -ne 6) { throw "PIC must contain one Cylinder and six Box collision locators." }
    if ($texts.PIC -notmatch '(?s)Part \{\s+Name: "defaultpart"\s+PieceCount: 0\s+LocatorCount: 7') { throw "PIC collision locators must belong to defaultpart." }
}

function Write-FileManifest {
    param([string]$Root, [string]$Path)
    $lines = foreach ($file in [IO.Directory]::EnumerateFiles($Root, "*", [IO.SearchOption]::AllDirectories) | Sort-Object) {
        $relative = $file.Substring($Root.TrimEnd("\").Length).TrimStart("\").Replace("\", "/")
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash
        "$relative`t$(([IO.FileInfo]$file).Length)`t$hash"
    }
    [IO.File]::WriteAllLines($Path, $lines, [Text.UTF8Encoding]::new($false))
}

function Write-InputManifest {
    param([string]$Path)
    $inputs = @([pscustomobject]@{ Root = $BaseDir; Label = "base" })
    $lines = @(
        "blend`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $SourceBlend).Hash)",
        "exporter`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $ExportScript).Hash)",
        "build_script`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash)",
        "resconvert`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $ResConvert).Hash)"
    )
    foreach ($input in $inputs) {
        foreach ($file in [IO.Directory]::EnumerateFiles($input.Root, "*", [IO.SearchOption]::AllDirectories) | Sort-Object) {
            $relative = $file.Substring($input.Root.TrimEnd("\").Length).TrimStart("\").Replace("\", "/")
            if ($input.Label -eq "base" -and $relative.StartsWith(".generated/", [StringComparison]::OrdinalIgnoreCase)) { continue }
            $lines += "$($input.Label)/$relative`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $file).Hash)"
        }
    }
    $effectRoot = Join-Path $ConversionTools "base\effect"
    foreach ($name in $RequiredEffectDefinitions + "eut2_interfaces.sui") {
        $path = if ($name -eq "eut2_interfaces.sui") { Join-Path $effectRoot $name } else { Join-Path (Join-Path $effectRoot "def") $name }
        $lines += "effect/$name`t$((Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash)"
    }
    [IO.File]::WriteAllLines($Path, @($lines | Sort-Object), [Text.UTF8Encoding]::new($false))
}

foreach ($directory in @($BuildDir, $ToolCacheDir, $DistDir)) { [IO.Directory]::CreateDirectory($directory) | Out-Null }
if ($CleanOnly) {
    Reset-Directory -Path $StageDir -Root $ProjectDir
    foreach ($path in @($PackagePath, $McpResponseLog, $BlenderExportLog, $ConversionLog, $ReportPath, $ContentManifest, $InputManifest, $LastContentManifest, $LastInputManifest)) { if ([IO.File]::Exists($path)) { [IO.File]::Delete($path) } }
    Reset-Directory -Path $MidFormatDir -Root $ProjectDir
    Reset-Directory -Path $ConversionMount -Root $ConversionTools
    Reset-Directory -Path $ConversionOutput -Root $ConversionTools
    "Cleaned generated build outputs for $ModId."
    exit 0
}

foreach ($path in @($SourceBlend, $ExportScript, $ResConvert)) { if (-not [IO.File]::Exists($path)) { throw "Required build input is missing: $path" } }
$stopwatch = [Diagnostics.Stopwatch]::StartNew()
Reset-Directory -Path $StageDir -Root $ProjectDir
Reset-Directory -Path $MidFormatDir -Root $ProjectDir
Reset-Directory -Path $ConversionMount -Root $ConversionTools
Reset-Directory -Path $ConversionOutput -Root $ConversionTools
if ([IO.File]::Exists($PackagePath)) { [IO.File]::Delete($PackagePath) }
foreach ($path in @($McpResponseLog, $BlenderExportLog, $ConversionLog)) { if ([IO.File]::Exists($path)) { [IO.File]::Delete($path) } }
$sourceCheck = @"
import bpy, json
expected = r'$SourceBlend'
root = bpy.data.objects.get('chassis')
assert bpy.data.filepath == expected, 'MCP is connected to %r, not the canonical source' % bpy.data.filepath
assert not bpy.data.is_dirty, 'canonical source has unsaved Blender changes'
assert root and root.scs_props.empty_object_type == 'SCS_Root', 'canonical SCS root chassis is missing'
parts = [item.name for item in root.scs_object_part_inventory]
assert parts == ['defaultpart', 'brace_on', 'brace_off', 'cables_on', 'cables_off'], parts
print(json.dumps({'source': bpy.data.filepath, 'parts': parts}))
"@
$mcpPreflight = Invoke-McpCode -Code $sourceCheck
if ($mcpPreflight -match '(?i)(error|warning|traceback|assertionerror)') { throw "Blender MCP preflight failed: $mcpPreflight" }

$exportCode = @"
import json, runpy
module = runpy.run_path(r'$ExportScript')
outputs = module['export'](r'$BaseDir', r'$MidFormatDir', r'$BlenderExportLog')
print(json.dumps({'outputs': outputs}))
"@
$mcpExport = Invoke-McpCode -Code $exportCode
[IO.File]::WriteAllText($McpResponseLog, $mcpPreflight + [Environment]::NewLine + $mcpExport, [Text.UTF8Encoding]::new($false))
$blenderExportText = [IO.File]::ReadAllText($BlenderExportLog)
if ($mcpExport -match '(?im)(^\s*(error|warning)\s*[-:]|traceback|cancelled)' -or $blenderExportText -match '(?im)^\s*(error|warning)\s*[-]') { throw "Blender MCP export failed or emitted warnings; inspect $McpResponseLog and $BlenderExportLog." }
Assert-ExportContract -Directory $MidFormatDir

Ensure-EffectResources -GamePath (Get-Ets2Path)
Copy-Tree -Source $BaseDir -Destination $ConversionMount
$conversionAssetDir = Join-Path $ConversionMount "vehicle\trailer_owned\tw40ch"
[IO.Directory]::CreateDirectory($conversionAssetDir) | Out-Null
foreach ($extension in @("pim", "pit", "pic")) { [IO.File]::Copy((Join-Path $MidFormatDir "chassis.$extension"), (Join-Path $conversionAssetDir "chassis.$extension"), $true) }
$toolDirectory = [IO.Path]::GetDirectoryName($ResConvert)
Push-Location $toolDirectory
try {
    $conversionMessages = @(& $ResConvert -update -root $ModId 2>&1 | ForEach-Object { $_.ToString() })
    $conversionExitCode = $LASTEXITCODE
}
finally { Pop-Location }
[IO.File]::WriteAllLines($ConversionLog, $conversionMessages, [Text.UTF8Encoding]::new($false))
if ($conversionExitCode -ne 0 -or $conversionMessages -match '(?i)(\*\*\* (error|warning) \*\*\*|\berror\b|\bwarning\b)') { throw "Conversion Tools failed or emitted warnings; inspect $ConversionLog." }
if (-not [IO.Directory]::Exists($ConvertedCache)) { throw "Conversion output cache was not created: $ConvertedCache" }

Copy-Tree -Source $ConvertedCache -Destination $StageBaseDir
Copy-PreconvertedAssets -Source $BaseDir -Destination $StageBaseDir
foreach ($metadata in @("manifest.sii", "mod_description.txt", "mod_description.zh_tw.txt")) {
    $source = Join-Path $StageBaseDir $metadata
    if (-not [IO.File]::Exists($source)) { throw "Missing package metadata: $metadata" }
    [IO.File]::Move($source, (Join-Path $StageDir $metadata))
}
foreach ($section in $ConditionalFiles.Keys) {
    foreach ($relative in $ConditionalFiles[$section]) {
        $source = Join-Path $StageBaseDir $relative
        $target = Join-Path (Join-Path $StageDir $section) $relative
        if (-not [IO.File]::Exists($source)) { throw "Missing conditional package source: $relative" }
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target)) | Out-Null
        [IO.File]::Move($source, $target)
    }
}
[IO.File]::Copy((Join-Path $BaseDir "mod_icon.jpg"), (Join-Path $StageDir "mod_icon.jpg"), $true)

foreach ($extension in @("pmd", "pmg", "pmc")) {
    if (-not [IO.File]::Exists((Join-Path $StageBaseDir "vehicle\trailer_owned\tw40ch\chassis.$extension"))) { throw "Conversion did not create chassis.$extension" }
}

Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem
$archive = [IO.Compression.ZipFile]::Open($PackagePath, [IO.Compression.ZipArchiveMode]::Create)
try {
    foreach ($directory in [IO.Directory]::EnumerateDirectories($StageDir, "*", [IO.SearchOption]::AllDirectories)) {
        $entry = $archive.CreateEntry($directory.Substring($StageDir.TrimEnd("\").Length).TrimStart("\").Replace("\", "/") + "/")
        $entry.ExternalAttributes = 0x10
    }
    foreach ($file in [IO.Directory]::EnumerateFiles($StageDir, "*", [IO.SearchOption]::AllDirectories)) {
        $relative = $file.Substring($StageDir.TrimEnd("\").Length).TrimStart("\").Replace("\", "/")
        [IO.Compression.ZipFileExtensions]::CreateEntryFromFile($archive, $file, $relative, [IO.Compression.CompressionLevel]::Optimal) | Out-Null
    }
}
finally { $archive.Dispose() }

$zip = [IO.Compression.ZipFile]::OpenRead($PackagePath)
try {
    $entries = @($zip.Entries.FullName)
    foreach ($required in @("base/", "base/vehicle/trailer_owned/tw40ch/chassis.pmd", "base/vehicle/trailer_owned/tw40ch/chassis.pmg", "base/vehicle/trailer_owned/tw40ch/chassis.pmc")) {
        if ($entries -notcontains $required) { throw "Package is missing required entry: $required" }
    }
}
finally { $zip.Dispose() }

Write-FileManifest -Root $StageDir -Path $ContentManifest
Write-InputManifest -Path $InputManifest
if ([IO.File]::Exists($LastInputManifest) -and @((Compare-Object (Get-Content $LastInputManifest) (Get-Content $InputManifest) -SyncWindow 0)).Count -eq 0) {
    if ([IO.File]::Exists($LastContentManifest) -and @((Compare-Object (Get-Content $LastContentManifest) (Get-Content $ContentManifest) -SyncWindow 0)).Count -ne 0) { throw "Identical build inputs produced a different package content manifest." }
}
[IO.File]::Copy($InputManifest, $LastInputManifest, $true)
[IO.File]::Copy($ContentManifest, $LastContentManifest, $true)

if (-not $ModDirectory) { $ModDirectory = Join-Path $env:USERPROFILE "Documents\Euro Truck Simulator 2\mod" }
[IO.Directory]::CreateDirectory($ModDirectory) | Out-Null
Get-ChildItem -LiteralPath $ModDirectory -File -Filter "tw40*.scs" | Remove-Item -Force
[IO.File]::Copy($PackagePath, (Join-Path $ModDirectory $PackageName), $true)

$modErrorCount = -1
if ($GameLogPath) {
    if (-not [IO.File]::Exists($GameLogPath)) { throw "Game log does not exist: $GameLogPath" }
    $modErrors = @(Get-Content $GameLogPath | Where-Object { $_ -match '<ERROR>' -and $_ -match '(?i)tw40ch|tw40ft|tw40ch_0\.2\.0-dev' })
    $modErrorCount = $modErrors.Count
    [IO.File]::Copy($GameLogPath, (Join-Path $BuildDir "game.log.txt"), $true)
    if ($modErrorCount -ne 0) { throw "Game log contains $modErrorCount tw40-related ERROR line(s)." }
}

$stopwatch.Stop()
$report = @(
    "status=success",
    "package=$PackagePath",
    "deployed_to=$(Join-Path $ModDirectory $PackageName)",
    "mcp_port=$McpPort",
    "conversion_exit_code=$conversionExitCode",
    "mod_error_count=$modErrorCount",
    "elapsed_seconds=$([Math]::Round($stopwatch.Elapsed.TotalSeconds, 3))"
)
[IO.File]::WriteAllLines($ReportPath, $report, [Text.UTF8Encoding]::new($false))
$report
