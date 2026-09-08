$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$app = Join-Path $root "frontend\app"

# Remove partial/incorrect stub dirs (keep layout.tsx, globals.css, favicon, root page.tsx)
$remove = @("(auth)", "admin", "dashboard", "inspections", "login", "products", "rules")
foreach ($d in $remove) {
    $p = Join-Path $app $d
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Recurse -Force }
}

$stubs = [ordered]@{
    "(auth)\login\page.tsx"                 = "S01 Login"
    "dashboard\page.tsx"                    = "S02 Dashboard"
    "inspections\new\page.tsx"              = "S03 New Inspection"
    "inspections\[id]\upload\page.tsx"      = "S04 Evidence Capture"
    "inspections\[id]\processing\page.tsx"  = "S05 Processing"
    "inspections\[id]\assessment\page.tsx"  = "S06 Assessment + S07 Evidence Viewer + S08 Review"
    "inspections\[id]\report\page.tsx"      = "S09 Report"
    "inspections\page.tsx"                  = "S10 History"
    "products\[id]\page.tsx"                = "S11 Product Detail"
    "admin\rules\page.tsx"                  = "S12 Rule Admin"
}

$template = @'
export default function Page() {
  return (
    <main className="flex min-h-screen items-center justify-center p-8">
      <div className="rounded-xl border border-gray-200 bg-white p-10 text-center shadow-sm">
        <h1 className="text-2xl font-semibold text-gray-900">{TITLE}</h1>
        <p className="mt-2 text-sm text-gray-500">LabelGuard AI — route stub (Phase 0). Full screen lands in C1–C8.</p>
      </div>
    </main>
  );
}
'@

foreach ($rel in $stubs.Keys) {
    $full = Join-Path $app ($rel -replace "/", "\")
    $dir = Split-Path $full
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    $content = $template.Replace("{TITLE}", $stubs[$rel])
    Set-Content -LiteralPath $full -Value $content -Encoding UTF8
}

Write-Host "Wrote $($stubs.Count) stubs cleanly."
Get-ChildItem $app -Recurse -File -Filter *.tsx | ForEach-Object { $_.FullName.Replace($root + "\", "") }