param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [switch]$SkipInstall
)
$ErrorActionPreference = 'Stop'

& (Join-Path $PSScriptRoot 'environment_check.ps1')

if (-not $SkipInstall) {
  python -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
}

$script = Join-Path $RepoRoot 'research\dssat_dtr\scripts\m19_regional_anomaly_threshold.py'
if (-not (Test-Path $script)) { throw "M19 script not found: $script" }

Write-Host '=== Re-running M19 temperature mechanism ==='
python $script
if ($LASTEXITCODE -ne 0) { throw 'M19 Python reproduction failed.' }

$out = Join-Path $RepoRoot 'research\dssat_dtr\data\m19_regional_anomaly_threshold'
$params = Get-Content (Join-Path $out 'parameters.json') -Raw | ConvertFrom-Json
$checks = Import-Csv (Join-Path $out 'physical_checks.csv')
$bad = @($checks | Where-Object {
  ([double]$_.below -gt 1e-6) -or
  ([double]$_.above -gt 1e-6) -or
  ([int]$_.rise_bad -ne 0) -or
  ([int]$_.fall_bad -ne 0)
}).Count

if ([math]::Abs([double]$params.K_RT - 1.4) -gt 1e-8) {
  throw "Unexpected K_RT: $($params.K_RT); expected approximately 1.40 SD."
}
if ([math]::Abs([double]$params.closure_max_abs_c_at_K_RT_99) -gt 1e-10) {
  throw "Official-closure check failed: $($params.closure_max_abs_c_at_K_RT_99) C"
}
if ($bad -ne 0) { throw "Physical curve check failed on $bad validation days." }

Write-Host '=== Temperature reproduction PASS ==='
Write-Host ("K_RT = {0:N2} SD" -f [double]$params.K_RT)
Write-Host ("Inactive-trigger closure max abs error = {0:E3} C" -f [double]$params.closure_max_abs_c_at_K_RT_99)
Write-Host "Physical violations = $bad"
Write-Host "Results: $out"
