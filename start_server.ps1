$ErrorActionPreference = "Continue"
cd $PSScriptRoot
Write-Host "Starting Flask server on http://127.0.0.1:5000" -ForegroundColor Green
.\venv\Scripts\python.exe app.py











