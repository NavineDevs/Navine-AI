$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($args.Count -eq 0) {
    & (Join-Path $Root "scripts\navine-launcher.ps1")
    exit $LASTEXITCODE
}

$Python = Join-Path $Root "venv\Scripts\python.exe"
if (Test-Path $Python) {
    & $Python -m navine.cli @args
} else {
    python -m navine.cli @args
}
exit $LASTEXITCODE
