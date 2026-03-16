# tq — Tutorial Queue  Windows Installer
# Usage: powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/yohamza/tq/main/install.ps1 | iex"

$ErrorActionPreference = "Stop"

$REPO    = "yohamza/tq"          # ← change to your GitHub user/repo
$EXE_URL = "https://github.com/$REPO/releases/latest/download/tq-windows.exe"
$INSTALL_DIR = "$env:LOCALAPPDATA\tq"
$EXE_PATH    = "$INSTALL_DIR\tq.exe"

function Write-Step  { param($msg) Write-Host "  • $msg" -ForegroundColor Cyan    }
function Write-Ok    { param($msg) Write-Host "  ✓ $msg" -ForegroundColor Green   }
function Write-Warn  { param($msg) Write-Host "  ! $msg" -ForegroundColor Yellow  }
function Write-Fail  { param($msg) Write-Host "  ✗ $msg" -ForegroundColor Red; exit 1 }

Write-Host ""
Write-Host "  📚 tq — Tutorial Queue Installer" -ForegroundColor White
Write-Host ""

# ── Check OS ──────────────────────────────────────────────────────────────────

if (-not $IsWindows -and $env:OS -notmatch "Windows") {
    Write-Fail "This script is for Windows. On macOS/Linux use the curl installer."
}
Write-Step "Platform: Windows"

# ── Download exe ──────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Downloading tq..." -ForegroundColor White

New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

Write-Step "Fetching latest release from GitHub..."
try {
    Invoke-WebRequest -Uri $EXE_URL -OutFile $EXE_PATH -UseBasicParsing
    Write-Ok "Downloaded tq.exe → $EXE_PATH"
} catch {
    Write-Fail "Download failed: $_`n  Check your internet connection or visit https://github.com/$REPO/releases"
}

# ── Add to PATH ───────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Setting up PATH..." -ForegroundColor White

$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$INSTALL_DIR*") {
    Write-Step "Adding $INSTALL_DIR to user PATH..."
    $newPath = "$currentPath;$INSTALL_DIR"
    [System.Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    $env:Path += ";$INSTALL_DIR"   # active for this session immediately
    Write-Ok "PATH updated"
} else {
    Write-Ok "$INSTALL_DIR already in PATH"
}

# ── Verify ────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  Verifying..." -ForegroundColor White

try {
    $ver = & "$EXE_PATH" --help 2>&1
    Write-Ok "tq is working!"
} catch {
    Write-Warn "tq installed but couldn't verify. Try: tq --help"
}

# ── Done ──────────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  🎉 tq is ready!" -ForegroundColor Green
Write-Host ""
Write-Host "  tq                     → Open the TUI dashboard"    -ForegroundColor White
Write-Host "  tq add `"My Tutorial`"   → Add your first tutorial"  -ForegroundColor White
Write-Host "  tq pick                → Smart-pick what to watch"  -ForegroundColor White
Write-Host "  tq --help              → All commands"              -ForegroundColor White
Write-Host ""
Write-Warn "Open a new terminal window for PATH changes to take effect."
Write-Host ""