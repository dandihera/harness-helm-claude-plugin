# h2-auto-apply.ps1 — apply newer h2 plugin payloads to already bootstrapped targets.

$ErrorActionPreference = 'Stop'

function Write-AutoApplyLog {
    param(
        [string]$Result,
        [string]$Reason,
        [string]$ErrorText = ''
    )
    New-Item -ItemType Directory -Path $DoctorDir -Force | Out-Null
    $now = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
    $payload = [ordered]@{
        schema_version = 1
        mode = 'auto-apply'
        target = $Target
        target_version = $script:TargetVersion
        payload_version = $script:PayloadVersion
        result = $Result
        reason = $Reason
        install_manifest = '.harness-helm/install-manifest.json'
        started_at = $script:StartedAt
        completed_at = $now
        errors = @()
    }
    if ($ErrorText) {
        $payload.errors = @($ErrorText)
    }
    $payload | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $LogPath -Encoding UTF8
}

function Test-SemVer([string]$Version) {
    return $Version -match '^v?\d+\.\d+\.\d+$'
}

function Compare-SemVer([string]$Left, [string]$Right) {
    $l = $Left.TrimStart('v').Split('.') | ForEach-Object { [int]$_ }
    $r = $Right.TrimStart('v').Split('.') | ForEach-Object { [int]$_ }
    for ($i = 0; $i -lt 3; $i++) {
        if ($l[$i] -gt $r[$i]) { return 1 }
        if ($l[$i] -lt $r[$i]) { return -1 }
    }
    return 0
}

$inputText = [Console]::In.ReadToEnd()
$PluginRoot = $env:CLAUDE_PLUGIN_ROOT
if (-not $PluginRoot) {
    $PluginRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}

$Target = $env:CLAUDE_PROJECT_DIR
if (-not $Target -and $inputText -match '"cwd"\s*:\s*"([^"]+)"') {
    $Target = $Matches[1]
}
if (-not $Target) {
    $Target = (Get-Location).Path
}

try {
    $gitRoot = git -C $Target rev-parse --show-toplevel 2>$null
    if ($LASTEXITCODE -eq 0 -and $gitRoot) {
        $Target = $gitRoot.Trim()
    }
} catch {}

$Manifest = Join-Path $Target '.harness-helm/install-manifest.json'
$DoctorDir = Join-Path $Target '.harness-helm/doctor'
$LogPath = Join-Path $DoctorDir 'auto-apply-latest.json'
$LockDir = Join-Path $DoctorDir 'auto-apply.lock'
$script:StartedAt = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')
$script:TargetVersion = ''
$script:PayloadVersion = ''

if (-not (Test-Path -LiteralPath $Manifest -PathType Leaf)) {
    exit 0
}

New-Item -ItemType Directory -Path $DoctorDir -Force | Out-Null
try {
    New-Item -ItemType Directory -Path $LockDir -ErrorAction Stop | Out-Null
} catch {
    exit 0
}

try {
    $manifestJson = Get-Content -LiteralPath $Manifest -Raw | ConvertFrom-Json
    $status = [string]$manifestJson.status
    $script:TargetVersion = [string]$manifestJson.package_version
    if ($status -ne 'ok') {
        Write-AutoApplyLog -Result 'skipped-recovery-required' -Reason 'install-manifest status is not ok'
        [Console]::Error.WriteLine('h2 auto-apply skipped: target recovery required. Run /h2:doctor.')
        exit 0
    }
    if (-not (Test-SemVer $script:TargetVersion)) {
        Write-AutoApplyLog -Result 'skipped-recovery-required' -Reason 'target package_version is invalid'
        [Console]::Error.WriteLine('h2 auto-apply skipped: invalid target package_version. Run /h2:doctor.')
        exit 0
    }

    $PackageRoot = Join-Path $PluginRoot 'release/h2-install'
    $markers = Get-ChildItem -LiteralPath $PackageRoot -Filter 'h2-install-v*.txt' -File -ErrorAction SilentlyContinue
    foreach ($marker in $markers) {
        $candidate = [System.IO.Path]::GetFileNameWithoutExtension($marker.Name).Substring('h2-install-'.Length)
        if (Test-SemVer $candidate) {
            if (-not $script:PayloadVersion -or (Compare-SemVer $candidate $script:PayloadVersion) -gt 0) {
                $script:PayloadVersion = $candidate
            }
        }
    }
    if (-not $script:PayloadVersion) {
        Write-AutoApplyLog -Result 'failed' -Reason 'plugin payload marker missing' -ErrorText 'release/h2-install/h2-install-v*.txt not found'
        [Console]::Error.WriteLine('h2 auto-apply failed: plugin payload marker missing. Run /h2:doctor.')
        exit 0
    }

    $cmp = Compare-SemVer $script:TargetVersion $script:PayloadVersion
    if ($cmp -gt 0) {
        Write-AutoApplyLog -Result 'skipped-downgrade' -Reason 'target version is newer than plugin payload'
        exit 0
    }
    if ($cmp -eq 0) {
        Write-AutoApplyLog -Result 'skipped-noop' -Reason 'target version matches plugin payload'
        exit 0
    }

    $Wrapper = Join-Path $PluginRoot 'release/h2-install.ps1'
    if (-not (Test-Path -LiteralPath $Wrapper -PathType Leaf)) {
        Write-AutoApplyLog -Result 'failed' -Reason 'plugin install wrapper missing' -ErrorText $Wrapper
        [Console]::Error.WriteLine('h2 auto-apply failed: install wrapper missing. Run /h2:doctor.')
        exit 0
    }

    & $Wrapper --target $Target --backup
    if ($LASTEXITCODE -eq 0) {
        Write-AutoApplyLog -Result 'applied' -Reason 'target package_version < plugin payload version'
        exit 0
    }
    Write-AutoApplyLog -Result 'failed' -Reason 'install wrapper failed' -ErrorText "exit code $LASTEXITCODE"
    [Console]::Error.WriteLine('h2 auto-apply failed. Run /h2:doctor to recover.')
    exit 0
} finally {
    Remove-Item -LiteralPath $LockDir -Recurse -Force -ErrorAction SilentlyContinue
}
