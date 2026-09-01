@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title book2audio Uninstall

echo.
echo ================================================================
echo               book2audio Uninstall Tool
echo ================================================================
echo.

set "INSTALL_DIR=%USERPROFILE%\.book2audio"
set "BIN_DIR=%USERPROFILE%\bin"

echo WARNING: This will remove book2audio from your system.
echo.
echo Files to be removed:
echo     - %INSTALL_DIR%
echo     - %BIN_DIR%\book2audio.bat
echo.
set /p "CONFIRM=Do you want to continue? (Y/N): "

if /I not "%CONFIRM%"=="Y" (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Removing from bin directory...
if exist "%BIN_DIR%\book2audio.bat" (
    del /f /q "%BIN_DIR%\book2audio.bat"
    echo [OK] Removed %BIN_DIR%\book2audio.bat
) else (
    echo [OK] File not found, skipping
)

echo.
echo [2/3] Removing installation directory...
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%"
    echo [OK] Removed %INSTALL_DIR%
) else (
    echo [OK] Directory not found, skipping
)

echo.
echo [3/3] PATH note...
echo.
echo NOTE: To remove from PATH manually:
echo     1. Search "Environment Variables" in Windows Search
echo     2. Click "Edit the system environment variables"
echo     3. Select "Path" and click "Edit"
echo     4. Remove %BIN_DIR%
echo     5. Click OK

echo.
echo ================================================================
echo [SUCCESS] book2audio has been removed!
echo ================================================================
echo.
echo To reinstall: run install.bat
echo.
pause
