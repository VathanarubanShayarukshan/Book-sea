@echo off
REM BookSea - Install Script
echo =========================================
echo   BookSea - Digital Library Setup
echo =========================================

cd /d "%~dp0.."

echo [1/4] Creating virtual environment...
uv venv
call venv\Scripts\activate.bat

echo [2/4] Installing dependencies...
uv pip install -r requirements.txt
uv pip install python-docx beautifulsoup4 lxml

echo [3/4] Creating required directories...
if not exist "media\books" mkdir media\books
if not exist "media\audio" mkdir media\audio

echo [4/4] Initializing database...
python -c "from app import create_app; app = create_app(); app.app_context().push(); print('Database created!')"

echo.
echo Setup complete!
echo.
echo To start the server:
echo   venv\Scripts\activate
echo   python run.py
echo.
echo Then open: http://localhost:5000
echo =========================================
pause
