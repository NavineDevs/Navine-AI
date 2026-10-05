$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Py = Join-Path $Root 'venv\Scripts\python.exe'
$LogDir = Join-Path $Root 'logs'
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$Out = Join-Path $LogDir 'hf_pipeline.out.log'
$Err = Join-Path $LogDir 'hf_pipeline.err.log'
$FetchScript = Join-Path $Root 'scripts\hf_fetch_and_train.py'
$TrainScript = Join-Path $Root 'scripts\hf_train_only.py'
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content $Out "[$ts] Starting HF fetch + train pipeline"
& $Py -u $FetchScript 2>&1 | Tee-Object -FilePath $Out -Append
if ($LASTEXITCODE -ne 0) {
    Add-Content $Out "[$ts] Fetch failed (exit $LASTEXITCODE); trying train-only"
    & $Py -u $TrainScript 2>&1 | Tee-Object -FilePath $Out -Append
}
$code = $LASTEXITCODE
$ts = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
Add-Content $Out "[$ts] Pipeline finished exit=$code"
