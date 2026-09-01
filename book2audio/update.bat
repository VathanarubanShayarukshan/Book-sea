@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title book2audio Update

echo.
echo ================================================================
echo               book2audio Update Tool
echo ================================================================
echo.

set "INSTALL_DIR=%USERPROFILE%\.book2audio"

if not exist "%INSTALL_DIR%" (
    echo [ERROR] book2audio is not installed!
    echo Please run install.bat first.
    pause
    exit /b 1
)

echo [1/5] Checking internet connection...
ping -n 1 github.com >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] No internet connection!
    pause
    exit /b 1
)
echo [OK] Internet connection is working

echo.
echo [2/5] Backing up current installation...
set "BACKUP_DIR=%USERPROFILE%\.book2audio_backup_%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%"
if exist "%BACKUP_DIR%" rmdir /s /q "%BACKUP_DIR%"
xcopy /E /I /Q "%INSTALL_DIR%" "%BACKUP_DIR%" >nul
echo [OK] Backup created: %BACKUP_DIR%

set "SCRIPT_DIR=%~dp0"

echo.
echo [3/5] Updating files...
if exist "%SCRIPT_DIR%book2audio.py" (
    copy /Y "%SCRIPT_DIR%book2audio.py" "%INSTALL_DIR%\" >nul
    copy /Y "%SCRIPT_DIR%update.bat" "%INSTALL_DIR%\" >nul
    copy /Y "%SCRIPT_DIR%uninstall.bat" "%INSTALL_DIR%\" >nul
    
    echo @echo off > "%INSTALL_DIR%\book2audio.bat"
    echo python "%INSTALL_DIR%\book2audio.py" %%* >> "%INSTALL_DIR%\book2audio.bat"
    
    if exist "%USERPROFILE%\bin" (
        copy /Y "%INSTALL_DIR%\book2audio.bat" "%USERPROFILE%\bin\" >nul
    )
    
    echo [OK] Files updated
) else (
    echo [ERROR] Source files not found!
    echo Restoring backup...
    xcopy /E /I /Q "%BACKUP_DIR%" "%INSTALL_DIR%" >nul
    echo [WARNING] Backup restored
    pause
    exit /b 1
)

echo.
echo [4/5] Updating Python packages...
pip install --upgrade gTTS langdetect beautifulsoup4 python-docx markdown odfpy pydub --quiet >nul 2>&1
echo [OK] Python packages updated

echo.
echo [5/5] Cleaning up backup...
rmdir /s /q "%BACKUP_DIR%" 2>nul

echo.
echo [TEST] Testing update...
python "%INSTALL_DIR%\book2audio.py" --help >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo [SUCCESS] book2audio updated successfully!
    echo ================================================================
) else (
    echo [WARNING] Update completed but test failed
)

echo.
pause
