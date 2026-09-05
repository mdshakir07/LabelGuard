# psql-setup.ps1 — create the local mitrametrology database.
# psql is NOT on PATH; resolve the bindir via pg_config.

$ErrorActionPreference = "Stop"

if (-not (Get-Command pg_config -ErrorAction SilentlyContinue)) {
    Write-Error "pg_config not found. Add PostgreSQL bin to PATH or install PostgreSQL."
    exit 1
}

$psql = Join-Path (pg_config --bindir) "psql"
if (-not (Test-Path -LiteralPath $psql)) {
    Write-Error "psql not found at $psql"
    exit 1
}

$user = if ($env:PGUSER) { $env:PGUSER } else { "postgres" }
$db = "mitrametrology"

# Check if server is reachable and whether DB exists (use 127.0.0.1 — localhost hits IPv6/GSSAPI).
Write-Host "Using psql: $psql"
$exists = & $psql -U $user -h 127.0.0.1 -tAc "SELECT 1 FROM pg_database WHERE datname='$db';" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Error "Could not connect to PostgreSQL on 127.0.0.1:5432 as '$user'. Run .\scripts\pg-local.ps1 start first."
    exit 1
}

if ($exists -eq "1") {
    Write-Host "Database '$db' already exists."
} else {
    & $psql -U $user -h 127.0.0.1 -c "CREATE DATABASE $db;"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Created database '$db'."
    } else {
        Write-Error "Failed to create database '$db'."
        exit 1
    }
}

Write-Host "Done. Connect with: postgresql://$user@127.0.0.1:5432/$db"