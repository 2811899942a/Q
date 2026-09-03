$ErrorActionPreference = "Stop"
$Root = "D:\SWAT+_3V3\Q\projects\SWATPlus-PISO-Cal"
Set-Location -LiteralPath $Root
$Runtime = Join-Path $Root "artifacts\a3\runtime"
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$PidPath = Join-Path $Runtime "pid.txt"
if (Test-Path -LiteralPath $PidPath) {
    $Existing = Get-Content -LiteralPath $PidPath -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($Existing -and (Get-Process -Id $Existing -ErrorAction SilentlyContinue)) { throw "A3 is already running with PID=$Existing" }
}
$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path -LiteralPath $Python)) { throw "project virtualenv Python not found: $Python" }
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Stdout = Join-Path $Runtime "a3_$Stamp.stdout.log"
$Stderr = Join-Path $Runtime "a3_$Stamp.stderr.log"
$Args = @("-u", "scripts\a3_optimizer_guidance_benchmark.py", "--resume")
$P = Start-Process -FilePath $Python -ArgumentList $Args -WorkingDirectory $Root -RedirectStandardOutput $Stdout -RedirectStandardError $Stderr -WindowStyle Hidden -PassThru
$P.Id | Set-Content -LiteralPath $PidPath
Write-Host "A3_BACKGROUND_STARTED"
Write-Host "PID=$($P.Id)"
Write-Host "STDOUT=$Stdout"
Write-Host "STDERR=$Stderr"
