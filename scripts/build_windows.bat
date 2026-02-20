@echo off
REM Build Windows .exe and Inno Setup installer
REM Run from the project root: scripts\build_windows.bat
setlocal enabledelayedexpansion

REM Extract version from installer .iss file
for /f "tokens=3 delims= " %%A in ('findstr /C:"#define MyAppVersion" installer\patreon_credits.iss') do set "VERSION=%%~A"

echo === Building Windows exe (v%VERSION%) ===
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
set "ISCC_EXE="
where ISCC >nul 2>nul && set "ISCC_EXE=ISCC"
if not defined ISCC_EXE (
    if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" (
        set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    )
)

if defined ISCC_EXE (
    "%ISCC_EXE%" installer\patreon_credits.iss
    echo:
    echo === Done ===
    echo Installer: dist\installer\PatreonCredits_Setup_%VERSION%.exe
) else (
    echo WARNING: Inno Setup not found. Skipping installer.
    echo Install from: https://jrsoftware.org/isdl.php
    echo Standalone exe is at: dist\PatreonCredits.exe
)
