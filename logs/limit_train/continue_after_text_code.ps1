$root = "C:\Users\hitbo\Downloads\Navine AI"
$py = Join-Path $root "venv\Scripts\python.exe"
while (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "navine\.cli.*train text-code" }) {
  Start-Sleep -Seconds 30
}
Remove-Item (Join-Path $root "logs\limit_train\marathon.lock") -Force -ErrorAction SilentlyContinue
Start-Process -FilePath $py -ArgumentList @("-u","scripts\run_limit_train_marathon.py","text_enterprise") -WorkingDirectory $root -WindowStyle Hidden
