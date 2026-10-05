$ai = "C:\Users\hitbo\Downloads\Navine AI"
Set-Location $ai
& "$ai\scripts\run_760m_train_queue.ps1" *>> "$ai\logs\gpt3_train\queue_wrapper.log"
