# dev.ps1 — start backend (and optionally frontend) for local development.
#   .\scripts\dev.ps1 backend
#   .\scripts\dev.ps1 frontend
#   .\scripts\dev.ps1 all

$ErrorActionPreference = "Stop"
$mode = if ($args.Count -gt 0) { $args[0] } else { "backend" }

function Start-Backend {
    if (-not (Test-Path "backend\.venv")) {
        Write-Error "Backend venv missing. Run: python -m venv backend\.venv"
        exit 1
    }
    Write-Host "Starting FastAPI on http://localhost:8000 ..."
    & "backend\.venv\Scripts\uvicorn.exe" app.main:app --reload --port 8000
}

function Start-Frontend {
    Write-Host "Starting Next.js on http://localhost:3000 ..."
    npm run dev --prefix frontend
}

switch ($mode) {
    "backend" { Start-Backend }
    "frontend" { Start-Frontend }
    "all" {
        $root = Split-Path -Parent $PSScriptRoot
        Start-Job -ScriptBlock { Set-Location $using:root; & (Join-Path $using:root "scripts\dev.ps1") backend }
        Start-Frontend
    }
    default { Write-Host "Usage: .\scripts\dev.ps1 [backend|frontend|all]" }
}