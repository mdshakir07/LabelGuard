# pg-local.ps1 — local PostgreSQL dev server (conda-installed binaries).
#   .\scripts\pg-local.ps1 init   -> initialize data dir (first run only)
#   .\scripts\pg-local.ps1 start  -> start server
#   .\scripts\pg-local.ps1 stop   -> stop server
#   .\scripts\pg-local.ps1 status -> is it running?
#
# Binaries come from Anaconda (conda base env): C:\Users\shaki\anaconda3\Library\bin
# Data dir lives OUTSIDE the OneDrive-synced workspace to avoid sync/lock issues.

$ErrorActionPreference = "Stop"

$pgbin = "C:\Users\shaki\anaconda3\Library\bin"
$pgdata = Join-Path $env:USERPROFILE "pgdata\mitrametrology"
$port = 5432
$user = "postgres"
$logfile = Join-Path $env:USERPROFILE "pgdata\mitrametrology.log"
$cmd = $null

switch ($args[0]) {
    "init" {
        if (Test-Path -LiteralPath $pgdata) {
            Write-Host "Data dir already exists: $pgdata"
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path $pgdata) | Out-Null
            & "$pgbin\initdb.exe" -D $pgdata -U $user -E UTF8 --locale=C --auth=trust
            if ($LASTEXITCODE -ne 0) { Write-Error "initdb failed"; exit 1 }
            Write-Host "Initialized PostgreSQL data dir at $pgdata"
        }
        $cmd = "init:done"
    }
    "start" {
        & "$pgbin\pg_ctl.exe" -D $pgdata -l $logfile start
        if ($LASTEXITCODE -ne 0) { Write-Error "pg_ctl start failed"; exit 1 }
        Write-Host "PostgreSQL started on port $port (log: $logfile)"
    }
    "stop" {
        & "$pgbin\pg_ctl.exe" -D $pgdata stop -m fast
    }
    "status" {
        & "$pgbin\pg_ctl.exe" -D $pgdata status
    }
    default {
        Write-Host "Usage: .\scripts\pg-local.ps1 [init|start|stop|status]"
    }
}