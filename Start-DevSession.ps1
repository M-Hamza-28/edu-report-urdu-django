# === CONFIG ===
$backend   = "C:\Users\hp\OneDrive\Documents\GitHub\edu-report-urdu-django"
$frontend  = "C:\Users\hp\OneDrive\Documents\GitHub\reporting-frontend\reporting-frontend"
# You normally run: .\venv\scripts\activate from C:\Users\hp  -> use the PS activate path:
$venvAct   = "$HOME\venv\Scripts\Activate.ps1"     # fallback to $backend\venv if not found
$helperDir = Join-Path $env:LOCALAPPDATA "DevSessionHelpers"

# Ensure helper dir
New-Item -ItemType Directory -Force -Path $helperDir | Out-Null

# --- Tab 1: Django + venv ---
$tab1Path = Join-Path $helperDir "tab1-django-venv.ps1"
@'
Set-Location "{0}"

if (Test-Path "{1}") {{
  & "{1}"
}} elseif (Test-Path "{0}\venv\Scripts\Activate.ps1") {{
  & "{0}\venv\Scripts\Activate.ps1"
}} else {{
  Write-Host "Venv not found at: {1} or {0}\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
}}

Write-Host "Django tab ready in: {0}" -ForegroundColor Green
'@ -f $backend, $venvAct | Set-Content -Encoding UTF8 -Path $tab1Path

# --- Tab 2: Django Files helpers ---
$tab2Path = Join-Path $helperDir "tab2-django-files.ps1"
@'
Set-Location "{0}"

function mkfile([string]$p) {{
  New-Item -ItemType File -Path $p -Force | Out-Null
  Write-Host ("Created: {0}" -f $p) -ForegroundColor Green
}}

function mkpy([string]$p) {{
  if (-not $p.ToLower().EndsWith('.py')) {{ $p = "$p.py" }}
  mkfile $p
}}

Write-Host "Try: mkpy reports\management\commands\seed_sessions.py" -ForegroundColor Cyan
'@ -f $backend | Set-Content -Encoding UTF8 -Path $tab2Path

# --- Tab 3: React dev ---
$tab3Path = Join-Path $helperDir "tab3-react-dev.ps1"
@'
Set-Location "{0}"
Write-Host "Starting: npm start" -ForegroundColor Green
npm start
'@ -f $frontend | Set-Content -Encoding UTF8 -Path $tab3Path

# --- Tab 4: Frontend Files helpers ---
$tab4Path = Join-Path $helperDir "tab4-frontend-files.ps1"
@'
Set-Location "{0}"

function mkfile([string]$p) {{
  New-Item -ItemType File -Path $p -Force | Out-Null
  Write-Host ("Created: {0}" -f $p) -ForegroundColor Green
}}

function mkjs([string]$p) {{
  if (-not $p.ToLower().EndsWith('.js')) {{ $p = "$p.js" }}
  mkfile $p
}}

Write-Host "Try: mkjs src\pages\StudentMarksManager.js" -ForegroundColor Cyan
'@ -f $frontend | Set-Content -Encoding UTF8 -Path $tab4Path

# --- Launch all 4 tabs in Windows Terminal (pass args as array) ---
$wt = "$Env:LOCALAPPDATA\Microsoft\Windows Terminal\wt.exe"
if (-not (Test-Path $wt)) { $wt = "wt.exe" }  # if wt.exe is on PATH

$argv = @(
  'new-tab','--title','Django (venv)','powershell','-NoExit','-File', $tab1Path,
  ';',
  'new-tab','--title','Django Files','powershell','-NoExit','-File', $tab2Path,
  ';',
  'new-tab','--title','React Dev','powershell','-NoExit','-File', $tab3Path,
  ';',
  'new-tab','--title','Frontend Files','powershell','-NoExit','-File', $tab4Path
)

& $wt @argv | Out-Null
