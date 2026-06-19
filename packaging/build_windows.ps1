# Onmer Admin Panel — Windows kurulum paketi derlemesi
# Kullanım (PowerShell, proje kökünde):
#   .\packaging\build_windows.ps1
# Gereksinim: Python 3.11+ PATH'te veya `py` başlatıcısı

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Host "=== Proje kökü: $Root ===" -ForegroundColor Cyan

python -m pip install -U pip
python -m pip install -r "$Root\onmer_admin_desktop\requirements.txt" "pyinstaller>=6.0"

python -m PyInstaller --noconfirm --clean "$Root\packaging\onmer_admin_panel.spec"

$dist = Join-Path $Root "dist\OnmerAdminPanel"
if (-not (Test-Path $dist)) {
    throw "PyInstaller çıktısı bulunamadı: $dist"
}

$copyDirs = @(
    "onmer", "core", "accounts", "menu", "orders",
    "reservations", "portfolio", "inventory", "templates", "static"
)

foreach ($d in $copyDirs) {
    $src = Join-Path $Root $d
    if (Test-Path $src) {
        $dst = Join-Path $dist $d
        Write-Host "Kopyalanıyor: $d" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dst -Force | Out-Null
        robocopy $src $dst /E /XD __pycache__ .mypy_cache .git /XF *.pyc /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
        if ($LASTEXITCODE -gt 8) { throw "robocopy hata: $d (kod $LASTEXITCODE)" }
    }
}

Copy-Item (Join-Path $Root "manage.py") $dist -Force
Copy-Item (Join-Path $Root "packaging\README_BUILD.txt") $dist -Force -ErrorAction SilentlyContinue
Copy-Item (Join-Path $Root "packaging\onmer_database.env.example") (Join-Path $dist "onmer_database.env.example") -Force -ErrorAction SilentlyContinue

if (Test-Path (Join-Path $Root "db.sqlite3")) {
    Write-Host "db.sqlite3 kopyalanıyor (geliştirme veritabanı)." -ForegroundColor Yellow
    Copy-Item (Join-Path $Root "db.sqlite3") $dist -Force
}

if (Test-Path (Join-Path $Root "media")) {
    $md = Join-Path $dist "media"
    New-Item -ItemType Directory -Path $md -Force | Out-Null
    robocopy (Join-Path $Root "media") $md /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
    if ($LASTEXITCODE -gt 8) { throw "robocopy hata: media" }
}

Write-Host "`n=== Tamam ===" -ForegroundColor Green
Write-Host "Çalıştırılabilir klasör: $dist"
Write-Host "Setup .exe için Inno Setup kurulumuyla şu komutu deneyin:"
Write-Host "  ISCC.exe `"$Root\packaging\OnmerAdminSetup.iss`"" -ForegroundColor DarkGray
