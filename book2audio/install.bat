@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title book2audio Installer

echo.
echo ================================================================
echo         book2audio - Convert Books to Audio Files
echo                     Version 1.0.0
echo ================================================================
echo.

echo [1/7] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed!
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python version: %PYTHON_VERSION%

echo.
echo [2/7] Checking pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing pip...
    python -m ensurepip --default-pip
    python -m pip install --upgrade pip
)
echo [OK] pip is ready

echo.
echo [3/7] Installing Python packages...
echo       Installing gTTS...
pip install gTTS --quiet >nul 2>&1
echo       Installing langdetect...
pip install langdetect --quiet >nul 2>&1
echo       Installing beautifulsoup4...
pip install beautifulsoup4 --quiet >nul 2>&1
echo       Installing python-docx...
pip install python-docx --quiet >nul 2>&1
echo       Installing markdown...
pip install markdown --quiet >nul 2>&1
echo       Installing odfpy...
pip install odfpy --quiet >nul 2>&1
echo       Installing pydub...
pip install pydub --quiet >nul 2>&1
echo [OK] All Python packages installed

echo.
echo [4/7] Checking ffmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] ffmpeg is not installed!
    echo Please install ffmpeg from: https://ffmpeg.org/download.html
    echo Or run: winget install ffmpeg
) else (
    echo [OK] ffmpeg is installed
)

set "INSTALL_DIR=%USERPROFILE%\.book2audio"
set "BIN_DIR=%USERPROFILE%\bin"

echo.
echo [5/7] Creating installation directory: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul
mkdir "%BIN_DIR%" 2>nul

set "SCRIPT_DIR=%~dp0"

echo.
echo [6/7] Copying files...
copy /Y "%SCRIPT_DIR%book2audio.py" "%INSTALL_DIR%\" >nul
copy /Y "%SCRIPT_DIR%update.bat" "%INSTALL_DIR%\" >nul
copy /Y "%SCRIPT_DIR%uninstall.bat" "%INSTALL_DIR%\" >nul

echo       Creating launcher script...
echo @echo off > "%INSTALL_DIR%\book2audio.bat"
echo python "%INSTALL_DIR%\book2audio.py" %%* >> "%INSTALL_DIR%\book2audio.bat"

copy /Y "%INSTALL_DIR%\book2audio.bat" "%BIN_DIR%\book2audio.bat" >nul

echo.
echo [7/7] Updating PATH...
echo %PATH% | findstr /I /C:"%BIN_DIR%" >nul
if %errorlevel% neq 0 (
    setx PATH "%BIN_DIR%;%PATH%" >nul 2>&1
    echo [OK] PATH updated. Please restart your terminal.
) else (
    echo [OK] PATH already contains bin directory
)

echo.
echo [TEST] Testing installation...
python "%INSTALL_DIR%\book2audio.py" --help >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ================================================================
    echo [SUCCESS] book2audio installed successfully!
    echo ================================================================
    echo.
    echo Usage examples:
    echo     book2audio -h              Show help menu
    echo     book2audio -lh             Show language list
    echo     book2audio -i book.txt -o audiobook.mp3
    echo.
    echo Or run directly:
    echo     python "%INSTALL_DIR%\book2audio.py" -h
    echo.
) else (
    echo [WARNING] Installation completed but test failed
    echo Try: python "%INSTALL_DIR%\book2audio.py" -h
)

echo.
pause
