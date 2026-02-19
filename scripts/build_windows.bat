@echo off
REM Build Windows .exe and Inno Setup installer
REM Run from the project root: scripts\build_windows.bat
setlocal

echo === Building Windows exe ===
python -m PyInstaller patreon_credits.spec --noconfirm
if errorlevel 1 (
    echo ERROR: PyInstaller build failed.
    exit /b 1
)

if not exist "dist\PatreonCredits.exe" (
    echo ERROR: dist\PatreonCredits.exe not found.
    exit /b 1
)

echo === Building installer ===
where ISCC >nul 2>nul
if %errorlevel%==0 (
    ISCC installer\patreon_credits.iss
) else if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\patreon_credits.iss
) else (
    echo WARNING: Inno Setup not found. Skipping installer.
    echo Install from: https://jrsoftware.org/isdl.php
    echo Standalone exe is at: dist\PatreonCredits.exe
    exit /b 0
)

echo.
echo === Done ===
echo Installer: dist\installer\PatreonCredits_Setup_1.1.0.exe
