param(
  [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path,
  [string]$WorkRoot = (Join-Path $PSScriptRoot 'work_m20'),
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
    throw "Full M20 source reproduction requires $cmd in PATH."
  }
}

if (Test-Path $WorkRoot) { Remove-Item $WorkRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
$SourceBase = Join-Path $WorkRoot 'dssat-csm-os'
$DataBase = Join-Path $WorkRoot 'dssat-csm-data'

Write-Host '=== Fetch exact frozen DSSAT 4.8.5 source/data ==='
& git clone https://github.com/DSSAT/dssat-csm-os.git $SourceBase
if ($LASTEXITCODE -ne 0) { throw 'DSSAT source clone failed.' }
& git -C $SourceBase checkout $SourceCommit
if ($LASTEXITCODE -ne 0) { throw 'DSSAT source checkout failed.' }
& git clone https://github.com/DSSAT/dssat-csm-data.git $DataBase
if ($LASTEXITCODE -ne 0) { throw 'DSSAT data clone failed.' }
& git -C $DataBase checkout $DataCommit
if ($LASTEXITCODE -ne 0) { throw 'DSSAT data checkout failed.' }

$Variants = @{}
foreach ($label in @('M0','M19','M20')) {
  $src = Join-Path $WorkRoot ("src_" + $label)
  Copy-Item $SourceBase $src -Recurse -Force
  $Variants[$label] = @{
    Source = $src
    Build = Join-Path $WorkRoot ("build_" + $label)
    Run = Join-Path $WorkRoot ("run_" + $label)
  }
}

Write-Host '=== Apply M19 weather patch and M20 neutral DTT bridge ==='
python (Join-Path $RepoRoot 'research\dssat_dtr\dssat485\apply_m19_htemp_patch_2call.py') $Variants['M19'].Source
if ($LASTEXITCODE -ne 0) { throw 'M19 source patch failed.' }
python (Join-Path $RepoRoot 'research\dssat_dtr\dssat485\apply_m19_htemp_patch_2call.py') $Variants['M20'].Source
if ($LASTEXITCODE -ne 0) { throw 'M19 prerequisite patch for M20 failed.' }
python (Join-Path $RepoRoot 'research\dssat_dtr\dssat485\apply_m20_dtt_bridge_patch.py') $Variants['M20'].Source
if ($LASTEXITCODE -ne 0) { throw 'M20 DTT bridge patch failed.' }

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
}

Write-Host '=== Build independent M0 / M19 / M20 executables ==='
foreach ($label in @('M0','M19','M20')) {
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

Write-Host '=== Add identical Anningqu weather, soil and 10 maize scenarios ==='
foreach ($label in @('M0','M19','M20')) {
  $v = $Variants[$label]
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

function Run-Mode([string]$Mode) {
  Write-Host "=== Run mode: $Mode ==="
  foreach ($label in @('M0','M19','M20')) {
    $v = $Variants[$label]
    $dest = Join-Path (Join-Path $Results $Mode) $label
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Push-Location (Join-Path $v.Run 'Maize')
    try {
      foreach ($sc in $Scenarios) {
        foreach ($f in @('Summary.OUT','PlantGro.OUT','Evaluate.OUT','ERROR.OUT','WARNING.OUT')) {
          if (Test-Path $f) { Remove-Item $f -Force }
        }
        $stdout = Join-Path $dest ($sc + '.stdout.txt')
        & $v.Exe A ($sc + '.MZX') *> $stdout
        if ($LASTEXITCODE -ne 0) { throw "$Mode $label $sc DSSAT exit code $LASTEXITCODE" }
        if (-not (Test-Path 'Summary.OUT')) { throw "$Mode $label $sc missing Summary.OUT" }
        if (-not (Test-Path 'PlantGro.OUT')) { throw "$Mode $label $sc missing PlantGro.OUT" }
        if ((Test-Path 'ERROR.OUT') -and ((Get-Item 'ERROR.OUT').Length -gt 0)) {
          throw "$Mode $label $sc generated non-empty ERROR.OUT"
        }
        Copy-Item 'Summary.OUT' (Join-Path $dest ($sc + '_Summary.OUT')) -Force
        Copy-Item 'PlantGro.OUT' (Join-Path $dest ($sc + '_PlantGro.OUT')) -Force
        if (Test-Path 'WARNING.OUT') {
          Copy-Item 'WARNING.OUT' (Join-Path $dest ($sc + '_WARNING.OUT')) -Force
        }
      }
    } finally {
      Pop-Location
    }
  }
}

# Natural-weather causal test.
Run-Mode 'NATURAL'

Write-Host '=== Create identical controlled +4 C Tmax / high-DTR weather in all arms ==='
foreach ($label in @('M0','M19','M20')) {
  $v = $Variants[$label]
  foreach ($yy in @('21','22')) {
    python (Join-Path $RepoRoot 'research\dssat_dtr\scripts\build_controlled_dtr_weather.py') `
      (Join-Path $RepoRoot ("research\dssat_dtr\data\anningqu\formal_ghcn_rain\ANQH" + $yy + "01.WTH")) `
      (Join-Path $v.Run ("Weather\ANQH" + $yy + "01.WTH")) `
      --delta-tmax 4.0 --start-doy 121 --end-doy 273
    if ($LASTEXITCODE -ne 0) { throw "$label controlled weather generation failed." }
  }
}

# Controlled causal stress. All three variants receive the same modified daily input.
Run-Mode 'STRESS_DTR4'

$Compact = Join-Path $WorkRoot 'compact_results'
python (Join-Path $RepoRoot 'research\dssat_dtr\scripts\parse_m0_m19_m20_bridge.py') --results-root $Results --output-dir $Compact
if ($LASTEXITCODE -ne 0) { throw 'M20 bridge parser failed.' }

$sum = Import-Csv (Join-Path $Compact 'bridge_summary.csv')
function Get-Row([string]$mode,[string]$model) {
  return $sum | Where-Object { $_.mode -eq $mode -and $_.model -eq $model } | Select-Object -First 1
}
$nat19 = Get-Row 'NATURAL' 'M19'
$str19 = Get-Row 'STRESS_DTR4' 'M19'
$str20 = Get-Row 'STRESS_DTR4' 'M20'
if (-not $nat19 -or -not $str19 -or -not $str20) { throw 'Required bridge summary rows missing.' }
if ([int]$nat19.changed_scenarios -ne 0) { throw 'Interface-control gate failed: natural M19 should not alter CERES-Maize outputs.' }
if ([int]$str19.changed_scenarios -ne 0) { throw 'Interface-control gate failed: stress M19 should not alter CERES-Maize outputs.' }
if ([int]$str20.changed_scenarios -lt 1) { throw 'Causal bridge gate failed: M20 did not alter any crop output under controlled high-DTR weather.' }

$manifest = [ordered]@{
  generated_at = (Get-Date).ToString('o')
  platform = 'Windows'
  reference_linux_run = 33956296856
  dssat_source_commit = $SourceCommit
  dssat_data_commit = $DataCommit
  variants = @('M0','M19','M20')
  weather_modes = @('NATURAL','STRESS_DTR4')
  scenarios_per_variant_per_mode = 10
  total_dssat_runs = 60
  regional_parameter = 'K_RT=1.40 SD'
  bridge_parameter = 'K_LINK=1.0 fixed structural constant'
  m19_natural_changed_scenarios = [int]$nat19.changed_scenarios
  m19_stress_changed_scenarios = [int]$str19.changed_scenarios
  m20_stress_changed_scenarios = [int]$str20.changed_scenarios
  exact_cross_platform_equality_required = $false
  causal_bridge_gate = 'PASS'
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Compact 'manifest.json') -Encoding UTF8

Write-Host '=== Windows M20 full-source reproduction PASS ==='
Write-Host "Compact results: $Compact"
Write-Host "Raw DSSAT outputs: $Results"
Write-Host 'Linux reference: GitHub Actions run 33956296856'
Write-Host 'Reference Linux stress M20: 10/10 changed, mean yield delta -9.8 kg/ha, max abs 224 kg/ha, mean maturity delta +0.2 d.'
Write-Host 'Small cross-platform floating-point/output differences are acceptable; the causal gates above are the required invariant.'
if (-not $KeepWork) {
  Write-Host 'Audit work tree is retained intentionally. Delete work_m20 manually after archiving results.'
}
