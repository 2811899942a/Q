$ErrorActionPreference = "Stop"
$Root = "D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal"
Set-Location $Root
$Runtime = Join-Path $Root "artifacts\a1\runtime"
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$PidPath = Join-Path $Runtime "pid.txt"
if (Test-Path $PidPath) {
    $Existing = Get-Content $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Existing -and (Get-Process -Id $Existing -ErrorAction SilentlyContinue)) { throw "A1 is already running with PID=$Existing" }
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) { throw "project virtualenv Python not found: $Python" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Stdout = Join-Path $Runtime "a1_$Stamp.stdout.log"
$Stderr = Join-Path $Runtime "a1_$Stamp.stderr.log"
$Args = @("-u", "scripts\a1_run_12h.py", "--resume", "--budget-hours", "11.5", "--hard-stop-hours", "12")
$P = Start-Process -FilePath $Python -ArgumentList $Args -WorkingDirectory $Root -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -WindowStyle Hidden -PassThru
$P.Id | Set-Content $PidPath
Write-Host "A1_BACKGROUND_STARTED"
Write-Host "PID=$($P.Id)"
Write-Host "STDOUT=$Stdout"
Write-Host "STDERR=$Stderr"
