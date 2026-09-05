$ErrorActionPreference = 'Stop'

Write-Host '=== DSSAT temperature Windows environment check ==='
$required = @('git','cmake','python')
foreach ($cmd in $required) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    throw "Missing required command: $cmd"
  }
  Write-Host ("{0}: {1}" -f $cmd,(Get-Command $cmd).Source)
}

$fortran = Get-Command gfortran -ErrorAction SilentlyContinue
if (-not $fortran) {
  Write-Warning 'gfortran was not found in PATH. Temperature-only Python reproduction can run; full DSSAT source rebuild cannot.'
} else {
  Write-Host ("gfortran: {0}" -f $fortran.Source)
  & gfortran --version | Select-Object -First 1
}

$make = Get-Command mingw32-make -ErrorAction SilentlyContinue
if (-not $make) {
  Write-Warning 'mingw32-make was not found. For the default PowerShell full-build path, install a MinGW-w64/MSYS2 toolchain and expose mingw32-make + gfortran in PATH.'
} else {
  Write-Host ("mingw32-make: {0}" -f $make.Source)
}

python --version
cmake --version | Select-Object -First 1
git --version
Write-Host 'Environment inspection complete.'
