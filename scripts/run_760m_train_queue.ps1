$ai = 'C:\Users\hitbo\Downloads\Navine AI'
$py = Join-Path $ai 'venv\Scripts\python.exe'
$logDir = Join-Path $ai 'logs\gpt3_train'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$env:PYTORCH_CUDA_ALLOC_CONF = 'expandable_segments:True'
$env:PYTHONUNBUFFERED = '1'
$queueLog = Join-Path $logDir 'queue.log'

function Write-Queue([string]$msg) {
  $line = "$(Get-Date -Format o) $msg"
  Add-Content -Path $queueLog -Value $line
  Write-Output $line
}

function Run-Train([string]$name, [string[]]$trainArgs) {
  $out = Join-Path $logDir "$name.out.log"
  $err = Join-Path $logDir "$name.err.log"
  Write-Queue "START $name"
  $p = Start-Process -FilePath $py -ArgumentList $trainArgs -WorkingDirectory $ai -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err -PassThru
  Wait-Process -Id $p.Id
  Write-Queue "END $name code=$($p.ExitCode)"
}

Write-Queue 'QUEUE BEGIN'
Run-Train 'text_code' @('-u', '-m', 'navine.cli', 'train', 'text-code', '--steps', '1200', '--require-cuda')
Run-Train 'text_enterprise' @('-u', '-m', 'navine.cli', 'train', 'text', '--steps', '1200', '--require-cuda')
Run-Train 'image' @('-u', '-m', 'navine.cli', 'train', 'image', '--steps', '800', '--require-cuda')
Run-Train 'video' @('-u', '-m', 'navine.cli', 'train', 'video', '--steps', '600', '--require-cuda')
Write-Queue 'QUEUE DONE'
