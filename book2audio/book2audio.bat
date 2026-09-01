@echo off
chcp 65001 >nul

:: book2audio Quick Launch Script
:: Double-click to run book2audio commands

set "INSTALL_DIR=%USERPROFILE%\.book2audio"

if not exist "%INSTALL_DIR%\book2audio.py" (
    echo book2audio நிறுவப்படவில்லை!
    echo முதலில் install.bat ஐ இயக்கவும்.
    pause
    exit /b 1
)

echo.
echo book2audio - Convert Books to Audio Files
echo ==========================================
echo.
echo பயன்பாடு:
echo     book2audio -i [உள்ளீட்டு கோப்பு] -o [வெளியீட்டு கோப்பு] -l [மொழி]
echo.
echo எடுத்துக்காட்டுகள்:
echo     book2audio -i book.txt -o audiobook.mp3
echo     book2audio -i book.txt -o audiobook.mp3 -l ta
echo     book2audio -h
echo.

set /p "INPUT=உள்ளீட்டு கோப்பு பாதை: "

if "%INPUT%"=="" (
    echo ரத்து செய்யப்பட்டது.
    pause
    exit /b 0
)

set /p "OUTPUT=வெளியீட்டு கோப்பு பாதை (default: output.mp3): "
if "%OUTPUT%"=="" set "OUTPUT=output.mp3"

set /p "LANG=மொழி குறியீடு (default: auto-detect): "

if "%LANG%"=="" (
    python "%INSTALL_DIR%\book2audio.py" -i "%INPUT%" -o "%OUTPUT%"
) else (
    python "%INSTALL_DIR%\book2audio.py" -i "%INPUT%" -o "%OUTPUT%" -l "%LANG%"
)

echo.
pause
