# h2-install.ps1 — Windows PowerShell bootstrap for harness-helm install.
# Mirrors release/install-package/h2-install.sh with a Go binary first flow.

$ErrorActionPreference = 'Stop'

if ($PSScriptRoot) {
    $ScriptDir = $PSScriptRoot
} else {
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$PackageRoot = Join-Path $ScriptDir 'h2-install'
$Manifest = Join-Path $PackageRoot 'MANIFEST.txt'
if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
    [Console]::Error.WriteLine("h2-install: MANIFEST.txt not found at $Manifest")
    exit 1
}

function Get-PackageVersion {
    $markers = Get-ChildItem -LiteralPath $PackageRoot -Filter 'h2-install-v*.txt' -File
    $versions = @()
    foreach ($m in $markers) {
        $v = [System.IO.Path]::GetFileNameWithoutExtension($m.Name).Substring('h2-install-'.Length)
        if ($v -match '^v?(\d+)\.(\d+)\.(\d+)$') {
            $versions += [pscustomobject]@{
                Text = $v
                Major = [int]$Matches[1]
                Minor = [int]$Matches[2]
                Patch = [int]$Matches[3]
            }
        }
    }
    if ($versions.Count -eq 0) {
        [Console]::Error.WriteLine("h2-install: version marker not found in $PackageRoot")
        exit 1
    }
    return ($versions | Sort-Object Major, Minor, Patch | Select-Object -Last 1).Text
}

$Version = Get-PackageVersion
$Arch = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString().ToLowerInvariant()
switch ($Arch) {
    'x64' { $GoArch = 'amd64' }
    'amd64' { $GoArch = 'amd64' }
    default {
        [Console]::Error.WriteLine("h2-install: unsupported platform: windows/$Arch")
        exit 1
    }
}

$Asset = "harness-$Version-windows-$GoArch.exe"
$ReleaseBase = $env:H2_HARNESS_RELEASE_BASE
if (-not $ReleaseBase) {
    $ReleaseBase = "https://github.com/dandihera/harness-helm-claude-plugin/releases/download/$Version"
}
$ReleaseBase = $ReleaseBase.TrimEnd('/', '\')

$TempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("h2-install-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $TempDir | Out-Null
$RuntimeBinary = Join-Path $TempDir $Asset
$ChecksumFile = Join-Path $TempDir "$Asset.sha256"

function Copy-Or-Download($Source, $Destination) {
    if ($Source -match '^https?://') {
        Invoke-WebRequest -Uri $Source -OutFile $Destination
    } elseif ($Source.StartsWith('file://')) {
        Copy-Item -LiteralPath $Source.Substring(7) -Destination $Destination
    } else {
        Copy-Item -LiteralPath $Source -Destination $Destination
    }
}

try {
    Copy-Or-Download "$ReleaseBase/$Asset" $RuntimeBinary
    Copy-Or-Download "$ReleaseBase/$Asset.sha256" $ChecksumFile

    $Expected = ((Get-Content -LiteralPath $ChecksumFile -Raw) -split '\s+')[0]
    if ($Expected -notmatch '^[0-9a-fA-F]+$') {
        [Console]::Error.WriteLine("h2-install: malformed checksum sidecar: $ChecksumFile")
        exit 1
    }
    $Actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $RuntimeBinary).Hash.ToLowerInvariant()
    if ($Expected.ToLowerInvariant() -ne $Actual) {
        [Console]::Error.WriteLine("h2-install: checksum mismatch for $Asset")
        exit 1
    }

    & $RuntimeBinary --help *> $null
    if ($LASTEXITCODE -ne 0) {
        [Console]::Error.WriteLine("h2-install: downloaded binary launch check failed: $Asset")
        exit 1
    }

    $HasTarget = $false
    foreach ($a in $Args) {
        if ($a -eq '--target' -or ($a -is [string] -and $a.StartsWith('--target='))) {
            $HasTarget = $true
            break
        }
    }
    if (-not $HasTarget) {
        $ForwardedArgs = @('--target', '.') + $Args
    } else {
        $ForwardedArgs = $Args
    }

    & $RuntimeBinary install --manifest $Manifest --runtime-binary $RuntimeBinary @ForwardedArgs
    exit $LASTEXITCODE
} finally {
    Remove-Item -LiteralPath $TempDir -Recurse -Force -ErrorAction SilentlyContinue
}
