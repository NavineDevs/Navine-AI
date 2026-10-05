$ai="C:\Users\hitbo\Downloads\Navine AI"
$py="$ai\venv\Scripts\python.exe"
# wait for any text-code train to exit
while (Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "navine\.cli train text-code" }) {
  Start-Sleep 30
}
& $py -u "$ai\scripts\run_760m_train_queue.py" text_enterprise >> "$ai\logs\gpt3_train\queue_wrapper.log" 2>&1
