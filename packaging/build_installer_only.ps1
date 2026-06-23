# Yalnizca kurulum dosyasini olusturur (dist\OnmerStokFinans hazir olmali).
# PowerShell:
#   .\packaging\build_installer_only.ps1
#   .\packaging\build_installer_only.ps1 -IncludeData

param(
    [switch]$IncludeData
)

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$dist = Join-Path $Root "dist\OnmerStokFinans"

if (-not (Test-Path (Join-Path $dist "OnmerStokFinans.exe"))) {
    throw "Once uygulamayi derleyin: .\packaging\build_stok_windows.ps1"
}

. {
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
}

if ($IncludeData) {
    & (Join-Path $Root "packaging\export_app_data.ps1")
    if ($LASTEXITCODE -ne 0) { exit 1 }
}

$iscc = Get-InnoSetupCompiler
if ($iscc) {
    if (Test-Path (Join-Path $Root "packaging\seed_data\onmer_stok.db")) {
        Write-Host "Kuruluma veritabani dahil edilecek." -ForegroundColor Green
    }
    & $iscc (Join-Path $Root "packaging\onmer_stok_setup.iss")
    Write-Host "Hazir: $Root\dist\OnmerStokFinans_Kurulum.exe" -ForegroundColor Green
    exit 0
}

Write-Host "Inno Setup yok; tam derleme scripti IExpress kullanir." -ForegroundColor Yellow
& (Join-Path $Root "packaging\build_stok_windows.ps1")
