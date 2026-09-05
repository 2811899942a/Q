param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$WorkRoot = (Join-Path $PSScriptRoot 'work_m20'),
  [int]$BuildJobs = 2,
  [switch]$KeepWork
)
$ErrorActionPreference = 'Stop'

Write-Warning 'The legacy M0/M15/M19 crop gate was retired after source audit showed CERES-Maize v4.8.5 does not consume Weather%TAIRHR/TGRO directly.'
Write-Host 'Forwarding to the validated M0/M19/M20 neutral-DTT bridge reproduction.'

& (Join-Path $PSScriptRoot 'run_m20_bridge.ps1') -RepoRoot $RepoRoot -WorkRoot $WorkRoot -BuildJobs $BuildJobs -KeepWork:$KeepWork
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
