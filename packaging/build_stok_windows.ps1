# Onmer Stok & Finans — Windows exe derlemesi
# PowerShell (proje kökünde):
#   .\packaging\build_stok_windows.ps1
#   .\packaging\build_stok_windows.ps1 -IncludeData    # mevcut veritabanini kuruluma dahil et

param(
    [switch]$IncludeData
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $Root

Write-Host "=== Onmer Stok & Finans derleniyor ===" -ForegroundColor Cyan

function Stop-OnmerProcesses {
    $procs = Get-Process -Name "OnmerStokFinans" -ErrorAction SilentlyContinue
    if ($procs) {
        Write-Host "Acik OnmerStokFinans.exe kapatiliyor..." -ForegroundColor Yellow
        $procs | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
}

function Clear-DistOutput {
    $dist = Join-Path $Root "dist\OnmerStokFinans"
    if (-not (Test-Path $dist)) {
        return
    }

    try {
        Remove-Item $dist -Recurse -Force -ErrorAction Stop
        Write-Host "Eski dist klasoru temizlendi." -ForegroundColor DarkGray
        return
    } catch {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backup = Join-Path $Root "dist\OnmerStokFinans_yedek_$stamp"
        Write-Host "dist silinemedi (dosya kilitli). Yedek adina tasiniyor..." -ForegroundColor Yellow
        try {
            Rename-Item $dist $backup -Force -ErrorAction Stop
            return
        } catch {
            Write-Host ""
            Write-Host "HATA: dist klasoru kullaniliyor, derleme yapilamiyor." -ForegroundColor Red
            Write-Host "Su adimlari deneyin:" -ForegroundColor Yellow
            Write-Host "  1. OnmerStokFinans.exe aciksa kapatın (Gorev Yoneticisi'nden de kontrol edin)"
            Write-Host "  2. dist\OnmerStokFinans klasorunu Dosya Gezgini'nde kapatın"
            Write-Host "  3. Antivirus taramasi bitince tekrar deneyin"
            Write-Host "  4. Scripti yonetici olarak calistirmayin; normal PowerShell yeterli"
            Write-Host ""
            throw
        }
    }
}

Stop-OnmerProcesses

$localData = Join-Path $env:LOCALAPPDATA "OnmerStokFinans"
$localDb = Join-Path $localData "onmer_stok.db"
$oldDistDb = Join-Path $Root "dist\OnmerStokFinans\data\onmer_stok.db"
if ((Test-Path $oldDistDb) -and -not (Test-Path $localDb)) {
    Write-Host "Eski veritabani kalici klasore tasiniyor..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $localData -Force | Out-Null
    Copy-Item $oldDistDb $localDb -Force
}

Clear-DistOutput

python -m pip install -U pip
python -m pip install -r "$Root\onmer_stok_desktop\requirements.txt" "pyinstaller>=6.0"

python -m PyInstaller --noconfirm "$Root\packaging\onmer_stok.spec"

$dist = Join-Path $Root "dist\OnmerStokFinans"
if (-not (Test-Path $dist)) {
    throw "PyInstaller çıktısı bulunamadı: $dist"
}

$assetsSrc = Join-Path $Root "onmer_stok_desktop\assets"
$assetsDst = Join-Path $dist "onmer_stok_desktop\assets"
if (Test-Path $assetsSrc) {
    New-Item -ItemType Directory -Path $assetsDst -Force | Out-Null
    Copy-Item "$assetsSrc\*" $assetsDst -Force -Recurse
}
$readme = @"
Onmer Stok & Finans
===================

Bu klasörü USB ile başka bilgisayara kopyalayabilirsiniz.
OnmerStokFinans.exe dosyasına çift tıklayın.

Veritabanı (güncellemelerde korunur):
  %LOCALAPPDATA%\OnmerStokFinans\onmer_stok.db

Web sitesiyle bağlantı YOKTUR — tüm verileri siz girersiniz.
"@
Set-Content -Path (Join-Path $dist "OKU_BENI.txt") -Value $readme -Encoding UTF8

Write-Host "`n=== Tamam ===" -ForegroundColor Green
Write-Host "Klasör: $dist"
Write-Host "Çalıştır: $dist\OnmerStokFinans.exe"

function Get-InnoSetupCompiler {
    $paths = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 7\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 6\ISCC.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 7\ISCC.exe"),
        (Join-Path $env:ProgramFiles "Inno Setup 7\ISCC.exe")
    )
    foreach ($path in $paths) {
        if (Test-Path $path) { return $path }
    }
    return $null
}

function Export-AppDataForInstaller {
    & (Join-Path $Root "packaging\export_app_data.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "Veritabani disa aktarilamadi."
    }
}

function Build-PortableInstaller {
    param([string]$DistDir)

    $packageDir = Join-Path $Root "dist\OnmerStokFinans_KurulumPaketi"
    $zipPath = Join-Path $Root "dist\OnmerStokFinans_Kurulum.zip"
    $kurulumBat = Join-Path $Root "packaging\KURULUM.bat"
    $readme = @"
Onmer Stok & Finans — Kurulum
=============================

1) Bu klasoru bilgisayara kopyalayin (veya ZIP dosyasini acin)
2) KURULUM.bat dosyasina sag tiklayin
3) "Yonetici olarak calistir" secin
4) Kurulum bitince masaustu kisayolundan uygulamayi acin

Verileriniz su konumda saklanir:
  %LOCALAPPDATA%\OnmerStokFinans

Not: Tek EXE kurulum sihirbazi icin Inno Setup kurup
     packaging\build_stok_windows.ps1 scriptini calistirin.
"@

    if (Test-Path $packageDir) {
        Remove-Item $packageDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $packageDir -Force | Out-Null
    Copy-Item "$DistDir\*" $packageDir -Recurse -Force
    Copy-Item $kurulumBat (Join-Path $packageDir "KURULUM.bat") -Force
    $seedDb = Join-Path $Root "packaging\seed_data\onmer_stok.db"
    if (Test-Path $seedDb) {
        $seedDst = Join-Path $packageDir "seed_data"
        New-Item -ItemType Directory -Path $seedDst -Force | Out-Null
        Copy-Item $seedDb (Join-Path $seedDst "onmer_stok.db") -Force
    }
    Set-Content -Path (Join-Path $packageDir "OKU_BENI.txt") -Value $readme -Encoding UTF8

    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }
    Compress-Archive -Path $packageDir -DestinationPath $zipPath -Force

    Write-Host ""
    Write-Host "=== Kurulum paketi hazir ===" -ForegroundColor Green
    Write-Host "ZIP: $zipPath"
    Write-Host "Klasor: $packageDir"
    Write-Host "Kurulum: KURULUM.bat dosyasini yonetici olarak calistirin"
}

function Build-Installer {
    if ($IncludeData) {
        Write-Host ""
        Write-Host "=== Mevcut veritabani kuruluma ekleniyor ===" -ForegroundColor Cyan
        Export-AppDataForInstaller
    }

    $iscc = Get-InnoSetupCompiler
    if ($iscc) {
        $iss = Join-Path $Root "packaging\onmer_stok_setup.iss"
        Write-Host ""
        Write-Host "=== Kurulum sihirbazi derleniyor (Inno Setup) ===" -ForegroundColor Cyan
        if (Test-Path (Join-Path $Root "packaging\seed_data\onmer_stok.db")) {
            Write-Host "Kuruluma veritabani dahil edilecek." -ForegroundColor Green
        }
        & $iscc $iss
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup derlemesi basarisiz (cikis kodu: $LASTEXITCODE)"
        }

        $setupExe = Join-Path $Root "dist\OnmerStokFinans_Kurulum.exe"
        if (-not (Test-Path $setupExe)) {
            throw "Kurulum dosyasi bulunamadi: $setupExe"
        }

        Write-Host ""
        Write-Host "=== Kurulum EXE hazir (Inno Setup) ===" -ForegroundColor Green
        Write-Host "Kurulum: $setupExe"
        return
    }

    Write-Host ""
    Write-Host "Inno Setup bulunamadi — ZIP kurulum paketi olusturuluyor..." -ForegroundColor Yellow
    Write-Host "Tek EXE sihirbazi icin: https://jrsoftware.org/isdl.php" -ForegroundColor DarkGray
    Build-PortableInstaller -DistDir $dist
}

Build-Installer
