@echo off
chcp 65001 >nul
setlocal EnableExtensions

net session >nul 2>&1
if errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

set "TARGET=%ProgramFiles%\Onmer Stok & Finans"
set "SRC=%~dp0"

echo.
echo ========================================
echo   Onmer Stok ^& Finans Kurulum
echo ========================================
echo.
echo Hedef klasor: %TARGET%
echo.

if not exist "%TARGET%" mkdir "%TARGET%"

echo Dosyalar kopyalaniyor...
xcopy /E /I /Y /Q "%SRC%*" "%TARGET%\" >nul
if errorlevel 1 (
    echo HATA: Dosyalar kopyalanamadi.
    pause
    exit /b 1
)

if exist "%TARGET%\KURULUM.bat" del /F /Q "%TARGET%\KURULUM.bat"
if exist "%TARGET%\onmer_install.bat" del /F /Q "%TARGET%\onmer_install.bat"
if exist "%TARGET%\OKU_BENI.txt" del /F /Q "%TARGET%\OKU_BENI.txt"
if exist "%TARGET%\seed_data" rmdir /S /Q "%TARGET%\seed_data"

if exist "%SRC%seed_data\onmer_stok.db" (
    if not exist "%LOCALAPPDATA%\OnmerStokFinans" mkdir "%LOCALAPPDATA%\OnmerStokFinans"
    if not exist "%LOCALAPPDATA%\OnmerStokFinans\onmer_stok.db" (
        echo Mevcut veritabani kopyalaniyor...
        copy /Y "%SRC%seed_data\onmer_stok.db" "%LOCALAPPDATA%\OnmerStokFinans\onmer_stok.db" >nul
    ) else (
        echo UYARI: Hedefte zaten veritabani var, uzerine yazilmadi.
    )
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$w = New-Object -ComObject WScript.Shell; ^
   $start = Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs'; ^
   $lnk = Join-Path $start 'Onmer Stok & Finans.lnk'; ^
   $s = $w.CreateShortcut($lnk); ^
   $s.TargetPath = '%TARGET%\OnmerStokFinans.exe'; ^
   $s.WorkingDirectory = '%TARGET%'; ^
   $s.Save(); ^
   $d = $w.CreateShortcut('%PUBLIC%\Desktop\Onmer Stok & Finans.lnk'); ^
   $d.TargetPath = '%TARGET%\OnmerStokFinans.exe'; ^
   $d.WorkingDirectory = '%TARGET%'; ^
   $d.Save()"

echo.
echo Kurulum tamamlandi.
echo.
echo Verileriniz (guncellemelerde korunur):
echo   %LOCALAPPDATA%\OnmerStokFinans
echo.
set /p RUN=Uygulamayi simdi baslatmak ister misiniz? [E/H]:
if /I "%RUN%"=="E" start "" "%TARGET%\OnmerStokFinans.exe"
exit /b 0
