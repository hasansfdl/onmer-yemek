# Mevcut uygulama veritabanini kurulum paketine kopyalar.
# PowerShell: .\packaging\export_app_data.ps1

$ErrorActionPreference = "Stop"
$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$sources = @(
    (Join-Path $env:LOCALAPPDATA "OnmerStokFinans\onmer_stok.db"),
    (Join-Path $Root "data\onmer_stok.db"),
    (Join-Path $Root "dist\OnmerStokFinans\data\onmer_stok.db")
)

$source = $null
foreach ($path in $sources) {
    if (Test-Path $path) {
        $source = $path
        break
    }
}

if (-not $source) {
    Write-Host "HATA: Veritabani bulunamadi." -ForegroundColor Red
    Write-Host "Aranan konumlar:" -ForegroundColor Yellow
    foreach ($path in $sources) {
        Write-Host "  - $path"
    }
    exit 1
}

$destDir = Join-Path $Root "packaging\seed_data"
$dest = Join-Path $destDir "onmer_stok.db"
New-Item -ItemType Directory -Path $destDir -Force | Out-Null
Copy-Item $source $dest -Force

$item = Get-Item $dest
Write-Host "Veritabani kurulum paketine eklendi." -ForegroundColor Green
Write-Host "Kaynak: $source"
Write-Host "Hedef:  $dest"
Write-Host "Boyut:  $([math]::Round($item.Length / 1KB, 1)) KB"
Write-Host "Tarih:  $($item.LastWriteTime)"
exit 0
