# One-time setup for the RAG project virtualenv (keeps deps isolated from other projects).
# Run from project root: .\scripts\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

Write-Host "Creating .venv (if missing)..."
py -m venv .venv

Write-Host "Installing pinned dependencies..."
.\.venv\Scripts\pip install --upgrade pip
.\.venv\Scripts\pip install -r requirements.txt

Write-Host ""
Write-Host "Done. Activate with:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "Then start:"
Write-Host "  docker compose --profile vllm up -d vllm"
Write-Host "  py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"
Write-Host "  py -m frontend.app"
