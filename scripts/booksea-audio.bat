@echo off
REM BookSea CLI - PDF to Audio Converter
REM Usage: booksea -p <pdf_path> -a <audio_output_path> [-l <language>]

cd /d "%~dp0\.."
python cli.py %*
