@echo off
REM BookSea - Update from GitHub
echo =========================================
echo   BookSea - GitHub Update
echo =========================================

cd /d "%~dp0\.."

echo [1/3] Stashing local changes...
git stash

echo [2/3] Pulling latest from GitHub...
git pull origin main

echo [3/3] Installing dependencies...
uv pip install -r requirements.txt
uv pip install python-docx beautifulsoup4 lxml

echo.
echo Update complete! Run 'python run.py' to start the server.
echo =========================================
pause
