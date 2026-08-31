#!/bin/bash
# BookSea CLI - PDF to Audio Converter
# Usage: booksea -p <pdf_path> -a <audio_output_path> [-l <language>]

cd "$(dirname "$0")/.." || exit 1
python3 cli.py "$@"
