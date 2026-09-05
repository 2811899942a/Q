param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$WorkRoot = (Join-Path $PSScriptRoot 'work'),
  [int]$BuildJobs = 2,
  [switch]$KeepWork
)
$ErrorActionPreference = 'Stop'

$SourceCommit = '0b91373806786b600d89ccfcfff78fa2f82cb26b'
$DataCommit   = '79cb5db71bbca186add92a6a9695866a09c8b51d'
$Scenarios = @('ANQH2101','ANQH2102','ANQH2103','ANQH2104','ANQH2105','ANQH2201','ANQH2202','ANQH2203','ANQH2204','ANQH2205')

& (Join-Path $PSScriptRoot 'environment_check.ps1')
foreach ($cmd in @('gfortran','mingw32-make')) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "Full source reproduction requires $cmd in PATH."
  }
}

if (Test-Path $WorkRoot) {
  Remove-Item $WorkRoot -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
$SourceBase = Join-Path $WorkRoot 'dssat-csm-os'
$DataBase = Join-Path $WorkRoot 'dssat-csm-data'

Write-Host '=== Fetch frozen DSSAT source/data ==='
& git clone https://github.com/DSSAT/dssat-csm-os.git $SourceBase
if ($LASTEXITCODE -ne 0) { throw 'Source clone failed.' }
& git -C $SourceBase checkout $SourceCommit
if ($LASTEXITCODE -ne 0) { throw 'Source checkout failed.' }
& git clone https://github.com/DSSAT/dssat-csm-data.git $DataBase
if ($LASTEXITCODE -ne 0) { throw 'Data clone failed.' }
& git -C $DataBase checkout $DataCommit
if ($LASTEXITCODE -ne 0) { throw 'Data checkout failed.' }

$Variants = @{}
foreach ($label in @('M0','M15','M19')) {
  $src = Join-Path $WorkRoot ("src_" + $label)
  Copy-Item $SourceBase $src -Recurse -Force
  $Variants[$label] = @{
    Source = $src
    Build = Join-Path $WorkRoot ("build_" + $label)
    Run = Join-Path $WorkRoot ("run_" + $label)
  }
}

Write-Host '=== Apply source-isolated temperature patches ==='
python (Join-Path $RepoRoot 'research\dssat_dtr\dssat485\apply_m15_htemp_patch.py') $Variants['M15'].Source
if ($LASTEXITCODE -ne 0) { throw 'M15 source patch failed.' }
python (Join-Path $RepoRoot 'research\dssat_dtr\dssat485\apply_m19_htemp_patch_2call.py') $Variants['M19'].Source
if ($LASTEXITCODE -ne 0) { throw 'M19 source patch failed.' }

function Set-VariantStandardPath([string]$Source,[string]$Runtime) {
  $osdef = Join-Path $Source 'Utilities\OSDefsWINDOWS.for'
  $text = [IO.File]::ReadAllText($osdef)
  $runtimeAbs = [IO.Path]::GetFullPath($Runtime).TrimEnd('\') + '\'
  if ($runtimeAbs.Contains("'")) { throw "Runtime path contains unsupported apostrophe: $runtimeAbs" }
  $rx = "STDPATH\s*=\s*'[^']*'"
  $new = "STDPATH  = '$runtimeAbs'"
  $changed = [regex]::Replace($text,$rx,$new)
  if ($changed -eq $text) { throw "Could not patch Windows STDPATH in $osdef" }
  [IO.File]::WriteAllText($osdef,$changed,[Text.Encoding]::ASCII)
  Write-Host "Windows DSSAT STDPATH => $runtimeAbs"
}

Write-Host '=== Build M0 / M15 / M19 with independent runtime paths ==='
foreach ($label in @('M0','M15','M19')) {
  $v = $Variants[$label]
  Set-VariantStandardPath $v.Source $v.Run
  & cmake -S $v.Source -B $v.Build -G 'MinGW Makefiles' '-DCMAKE_Fortran_COMPILER=gfortran' '-DCMAKE_BUILD_TYPE=RELEASE' ("-DCMAKE_INSTALL_PREFIX=" + $v.Run)
  if ($LASTEXITCODE -ne 0) { throw "$label CMake configure failed." }
  & cmake --build $v.Build --parallel $BuildJobs
  if ($LASTEXITCODE -ne 0) { throw "$label build failed." }
  & cmake --install $v.Build
  if ($LASTEXITCODE -ne 0) { throw "$label install failed." }
  Copy-Item (Join-Path $DataBase '*') $v.Run -Recurse -Force
  $exe = Get-ChildItem $v.Run -Recurse -Filter 'dscsm048.exe' | Select-Object -First 1
  if (-not $exe) { throw "$label dscsm048.exe not found under $($v.Run)" }
  $v.Exe = $exe.FullName
}

Write-Host '=== Add identical Anningqu weather / soil / experiments ==='
foreach ($label in @('M0','M15','M19')) {
  $v=$Variants[$label]
  New-Item -ItemType Directory -Force -Path (Join-Path $v.Run 'Weather') | Out-Null
  New-Item -ItemType Directory -Force -Path (Join-Path $v.Run 'Soil') | Out-Null
  Copy-Item (Join-Path $RepoRoot 'research\dssat_dtr\data\anningqu\formal_ghcn_rain\ANQH2101.WTH') (Join-Path $v.Run 'Weather\ANQH2101.WTH') -Force
  Copy-Item (Join-Path $RepoRoot 'research\dssat_dtr\data\anningqu\formal_ghcn_rain\ANQH2201.WTH') (Join-Path $v.Run 'Weather\ANQH2201.WTH') -Force
  Copy-Item (Join-Path $RepoRoot 'research\dssat_dtr\anningqu\AN.SOL') (Join-Path $v.Run 'Soil\AN.SOL') -Force
  python (Join-Path $RepoRoot 'research\dssat_dtr\anningqu\build_stageA_propagation_experiments.py') (Join-Path $v.Run 'Maize\UFGA8201.MZX') (Join-Path $v.Run 'Maize')
  if ($LASTEXITCODE -ne 0) { throw "$label experiment generation failed." }
}

$Results = Join-Path $WorkRoot 'results'
New-Item -ItemType Directory -Force -Path $Results | Out-Null
Write-Host '=== Run 30 DSSAT simulations ==='
foreach ($label in @('M0','M15','M19')) {
  $v=$Variants[$label]
  $dest=Join-Path $Results $label
  New-Item -ItemType Directory -Force -Path $dest | Out-Null
  Push-Location (Join-Path $v.Run 'Maize')
  try {
    foreach ($sc in $Scenarios) {
      foreach ($f in @('Summary.OUT','PlantGro.OUT','Evaluate.OUT','ERROR.OUT','WARNING.OUT')) {
        if (Test-Path $f) { Remove-Item $f -Force }
      }
      $stdout=Join-Path $dest ($sc + '.stdout.txt')
      & $v.Exe A ($sc + '.MZX') *> $stdout
      if ($LASTEXITCODE -ne 0) { throw "$label $sc DSSAT exit code $LASTEXITCODE" }
      if (-not (Test-Path 'Summary.OUT')) { throw "$label $sc missing Summary.OUT" }
      if (-not (Test-Path 'PlantGro.OUT')) { throw "$label $sc missing PlantGro.OUT" }
      if ((Test-Path 'ERROR.OUT') -and ((Get-Item 'ERROR.OUT').Length -gt 0)) {
        throw "$label $sc generated non-empty ERROR.OUT"
      }
      Copy-Item 'Summary.OUT' (Join-Path $dest ($sc + '_Summary.OUT')) -Force
      Copy-Item 'PlantGro.OUT' (Join-Path $dest ($sc + '_PlantGro.OUT')) -Force
      if (Test-Path 'WARNING.OUT') { Copy-Item 'WARNING.OUT' (Join-Path $dest ($sc + '_WARNING.OUT')) -Force }
    }
  } finally {
    Pop-Location
  }
}

$Compact = Join-Path $WorkRoot 'compact_results'
python (Join-Path $PSScriptRoot 'parse_crop_ab.py') $Results $Compact
if ($LASTEXITCODE -ne 0) { throw 'Crop-output parser failed.' }

$sum = Import-Csv (Join-Path $Compact 'propagation_summary.csv')
$m19 = $sum | Where-Object {$_.model -eq 'M19'}
if (-not $m19) { throw 'M19 propagation summary missing.' }
if ([int]$m19.changed_scenarios -lt 1) { throw 'Mechanism gate failed: M19 did not alter any crop output.' }

$manifest = [ordered]@{
  generated_at = (Get-Date).ToString('o')
  platform = 'Windows'
  dssat_source_commit = $SourceCommit
  dssat_data_commit = $DataCommit
  variants = @('M0','M15','M19')
  scenarios_per_variant = 10
  total_dssat_runs = 30
  m19_changed_scenarios = [int]$m19.changed_scenarios
  exact_cross_platform_equality_required = $false
  mechanism_gate = 'PASS'
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Compact 'manifest.json') -Encoding UTF8

Write-Host '=== Full Windows source reproduction PASS ==='
Write-Host "Compact results: $Compact"
Write-Host "Raw run outputs: $Results"
if (-not $KeepWork) {
  Write-Host 'Work tree retained intentionally for audit. Delete the work folder manually after inspection.'
}
