$ErrorActionPreference = "Stop"
$port = 8000
$busy = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
if ($busy) {
    Write-Host "Port $port is already in use. Using port 8001 instead."
    $port = 8001
}
Write-Host "Starting AquaMindAI-Agent on http://127.0.0.1:$port"
python -m uvicorn web_app:app --host 127.0.0.1 --port $port
