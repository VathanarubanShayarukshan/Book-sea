#!/bin/bash
# Quick test for book2audio

echo "Testing book2audio installation..."

# Test Python version
python3 --version

# Test gTTS import
python3 -c "from gtts import gTTS; print('gTTS OK')"

# Test langdetect import
python3 -c "from langdetect import detect; print('langdetect OK')"

# Test beautifulsoup4 import
python3 -c "from bs4 import BeautifulSoup; print('BeautifulSoup OK')"

# Test help command
python3 book2audio.py -h

echo "Test completed!"
