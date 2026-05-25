# ============================================================
# Varsany VPS Setup Script
# Run this ONCE on the VPS as Administrator
# Right-click PowerShell → "Run as Administrator" → paste this
# ============================================================

$downloads = "$env:TEMP\varsany_setup"
New-Item -ItemType Directory -Force -Path $downloads | Out-Null

Write-Host "`n[1/5] Downloading Python 3.11..." -ForegroundColor Cyan
Invoke-WebRequest "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe" -OutFile "$downloads\python.exe" -UseBasicParsing
Write-Host "Installing Python..."
Start-Process "$downloads\python.exe" -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1 Include_pip=1" -Wait
Write-Host "Python installed." -ForegroundColor Green

Write-Host "`n[2/5] Downloading Git..." -ForegroundColor Cyan
Invoke-WebRequest "https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/Git-2.45.2-64-bit.exe" -OutFile "$downloads\git.exe" -UseBasicParsing
Write-Host "Installing Git..."
Start-Process "$downloads\git.exe" -ArgumentList "/SILENT /NORESTART" -Wait
Write-Host "Git installed." -ForegroundColor Green

Write-Host "`n[3/5] Downloading ODBC Driver 17 for SQL Server..." -ForegroundColor Cyan
Invoke-WebRequest "https://go.microsoft.com/fwlink/?linkid=2249006" -OutFile "$downloads\msodbcsql17.msi" -UseBasicParsing
Write-Host "Installing ODBC Driver 17..."
Start-Process msiexec.exe -ArgumentList "/i `"$downloads\msodbcsql17.msi`" /quiet IACCEPTMSODBCSQLLICENSETERMS=YES" -Wait
Write-Host "ODBC Driver installed." -ForegroundColor Green

Write-Host "`n[4/5] Downloading Google Chrome..." -ForegroundColor Cyan
Invoke-WebRequest "https://dl.google.com/chrome/install/ChromeStandaloneSetup64.exe" -OutFile "$downloads\chrome.exe" -UseBasicParsing
Write-Host "Installing Chrome (needed for special fonts)..."
Start-Process "$downloads\chrome.exe" -ArgumentList "/silent /install" -Wait
Write-Host "Chrome installed." -ForegroundColor Green

Write-Host "`n[5/5] Downloading Visual C++ Redistributable..." -ForegroundColor Cyan
Invoke-WebRequest "https://aka.ms/vs/17/release/vc_redist.x64.exe" -OutFile "$downloads\vc_redist.exe" -UseBasicParsing
Write-Host "Installing VC++ Redistributable (needed for numpy/rembg)..."
Start-Process "$downloads\vc_redist.exe" -ArgumentList "/quiet /norestart" -Wait
Write-Host "VC++ Redistributable installed." -ForegroundColor Green

Write-Host "`nAll system software installed. Now refreshing PATH..." -ForegroundColor Yellow
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "`nCloning project from GitHub..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path "C:\Varsany" | Out-Null
git clone https://github.com/yedhu438/chronosV1 C:\Varsany\v4
Write-Host "Project cloned." -ForegroundColor Green

Write-Host "`nInstalling Python packages..." -ForegroundColor Cyan
Set-Location C:\Varsany\v4
py -m pip install -r requirements.txt
Write-Host "Python packages installed." -ForegroundColor Green

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host " DONE — All software installed successfully!" -ForegroundColor Green
Write-Host "============================================================"
Write-Host ""
Write-Host "NEXT STEPS:"
Write-Host "  1. Copy your .env file to C:\Varsany\v4\.env"
Write-Host "  2. Copy C:\Varsany\Fonts\ folder to C:\Varsany\Fonts\"
Write-Host "  3. Test DB: py C:\Varsany\v4\db.py"
Write-Host "  4. Test order: py C:\Varsany\v4\batch_processor.py --limit 3 --dry-run"
Write-Host "  5. Set up Task Scheduler (see below)"
Write-Host ""
Write-Host "TASK SCHEDULER (run once, sets up auto-polling every 60s):"
Write-Host '  schtasks /create /tn "VarsanyAutomation" /tr "py C:\Varsany\v4\batch_processor.py --mark" /sc minute /mo 1 /ru SYSTEM /f'
