#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
book2audio - Convert books to audio files
Uses Microsoft Edge TTS (free, no rate limits)
"""

import argparse
import os
import sys
import subprocess
import importlib
import asyncio
import tempfile
import shutil
import time
from pathlib import Path

VERSION = "2.1.0"

LANGUAGES = {
    "ta": "Tamil", "en": "English", "fr": "French", "de": "German",
    "es": "Spanish", "it": "Italian", "pt": "Portuguese", "ru": "Russian",
    "ja": "Japanese", "ko": "Korean", "zh": "Chinese", "ar": "Arabic",
    "hi": "Hindi", "bn": "Bengali", "te": "Telugu", "ml": "Malayalam",
    "kn": "Kannada", "mr": "Marathi", "gu": "Gujarati", "pa": "Punjabi",
    "ur": "Urdu", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
    "ms": "Malay", "tr": "Turkish", "pl": "Polish", "nl": "Dutch",
    "sv": "Swedish", "da": "Danish", "fi": "Finnish", "no": "Norwegian",
    "cs": "Czech", "el": "Greek", "he": "Hebrew", "hu": "Hungarian",
    "ro": "Romanian", "uk": "Ukrainian", "bg": "Bulgarian", "hr": "Croatian",
    "sk": "Slovak", "sl": "Slovenian", "et": "Estonian", "lv": "Latvian",
    "lt": "Lithuanian", "sw": "Swahili", "af": "Afrikaans", "ca": "Catalan"
}

VOICES = {
    "ta": "ta-IN-ValluvarNeural",
    "en": "en-US-GuyNeural",
    "fr": "fr-FR-HenriNeural",
    "de": "de-DE-ConradNeural",
    "es": "es-ES-AlvaroNeural",
    "it": "it-IT-DiegoNeural",
    "pt": "pt-BR-AntonioNeural",
    "ru": "ru-RU-DmitryNeural",
    "ja": "ja-JP-KeitaNeural",
    "ko": "ko-KR-InJoonNeural",
    "zh": "zh-CN-YunxiNeural",
    "ar": "ar-SA-HamedNeural",
    "hi": "hi-IN-MadhurNeural",
    "th": "th-TH-NiwatNeural",
    "vi": "vi-VN-NamMinhNeural",
}

def check_deps():
    import importlib.util
    pkgs = {'edge_tts': 'edge-tts', 'langdetect': 'langdetect', 'bs4': 'beautifulsoup4', 'docx': 'python-docx', 'PyPDF2': 'PyPDF2'}
    missing = [p for m, p in pkgs.items() if importlib.util.find_spec(m) is None]
    if missing:
        print(f"[*] Installing: {', '.join(missing)}")
        # Try with --break-system-packages for externally managed environments
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet"] + missing)
        except subprocess.CalledProcessError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--break-system-packages"] + missing)
            except subprocess.CalledProcessError:
                print("[X] Failed to install packages")
                print("    Try: pip install --break-system-packages edge-tts langdetect beautifulsoup4 python-docx PyPDF2")
                sys.exit(1)

def read_pdf(f):
    from PyPDF2 import PdfReader
    return '\n'.join(p.extract_text() or '' for p in PdfReader(f).pages)

def read_txt(f):
    return open(f, 'r', encoding='utf-8').read()

def read_html(f):
    from bs4 import BeautifulSoup
    s = BeautifulSoup(open(f, 'r', encoding='utf-8').read(), 'html.parser')
    for x in s(["script", "style"]): x.decompose()
    return s.get_text('\n', strip=True)

def read_docx(f):
    from docx import Document
    return '\n'.join(p.text for p in Document(f).paragraphs if p.text.strip())

def read_md(f):
    import markdown
    from bs4 import BeautifulSoup
    return BeautifulSoup(markdown.markdown(open(f, 'r', encoding='utf-8').read()), 'html.parser').get_text('\n', strip=True)

def read_file(f):
    ext = Path(f).suffix.lower()
    readers = {'.txt': read_txt, '.html': read_html, '.htm': read_html, '.docx': read_docx, '.md': read_md, '.pdf': read_pdf}
    if ext not in readers:
        print(f"[X] Unsupported: {ext}. Use: {', '.join(readers.keys())}")
        sys.exit(1)
    print(f"[*] Reading: {f}")
    text = readers[ext](f)
    if not text.strip():
        print("[X] No text found")
        sys.exit(1)
    return text

def detect_lang(text):
    try:
        from langdetect import detect
        import re
        cleaned = re.sub(r'[^\w\s]', '', re.sub(r'\d+', '', text[:2000]))
        return detect(cleaned[:500]) if cleaned.strip() else "en"
    except: return "en"

async def convert_chunk(text, voice, rate, output_file):
    """Convert single chunk to audio file"""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_file)

def text_to_audio(text, lang, output_path, slow=False, silent=False):
    voice = VOICES.get(lang, "en-US-GuyNeural")
    rate = "-20%" if slow else "-10%"
    
    if not silent:
        print(f"[*] Voice: {voice}")
    
    # Split text
    chunk_size = 2000
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    total = len(chunks)
    
    if not silent:
        print(f"[*] {len(text)} chars -> {total} chunks")
    
    # Create temp dir
    temp_dir = tempfile.mkdtemp()
    temp_files = []
    failed = 0
    
    # Process each chunk
    for i, chunk in enumerate(chunks):
        if not silent:
            print(f"    [{i+1}/{total}] Working...", end='', flush=True)
        
        temp_file = os.path.join(temp_dir, f"chunk_{i:04d}.mp3")
        
        success = False
        for attempt in range(3):
            try:
                asyncio.run(convert_chunk(chunk, voice, rate, temp_file))
                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                    temp_files.append(temp_file)
                    success = True
                    if not silent:
                        print(" OK")
                    break
                else:
                    if not silent:
                        print(f" retry({attempt+1})...", end='', flush=True)
            except Exception as e:
                if not silent:
                    print(f" retry({attempt+1})...", end='', flush=True)
            time.sleep(1)
        
        if not success:
            if not silent:
                print(" SKIP")
            failed += 1
        
        # Delay between chunks
        time.sleep(0.3)
    
    if not silent:
        print(f"[*] Converted: {len(temp_files)}/{total} chunks")
    
    if not temp_files:
        if not silent:
            print("[X] No chunks converted")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return False
    
    if not silent:
        print(f"[*] Merging...")
    
    # Try pydub first, then ffmpeg
    try:
        from pydub import AudioSegment
        audio = AudioSegment.empty()
        for tf in temp_files:
            audio += AudioSegment.from_mp3(tf)
        audio.export(output_path, format="mp3", bitrate="192k")
    except Exception as e:
        if not silent:
            print(f"[*] Pydub failed, trying ffmpeg...")
        try:
            concat = os.path.join(temp_dir, "files.txt")
            with open(concat, 'w') as f:
                for tf in temp_files:
                    f.write(f"file '{tf}'\n")
            subprocess.run(['ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat, '-c:a', 'libmp3lame', '-q:a', '2', output_path], check=True, capture_output=True)
        except Exception as e2:
            if not silent:
                print(f"[*] ffmpeg failed, copying first chunk")
            shutil.copy2(temp_files[0], output_path)
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    if failed > 0 and not silent:
        print(f"[!] {failed} chunks failed (partial audio)")
    
    return True

def show_help():
    print(f"""
book2audio v{VERSION} - Convert Books to Audio (Edge TTS)

Usage: book2audio -i <input> -o <output> [-l <lang>]

Options:
  -i, --input     Input file path
  -o, --output    Output audio file path  
  -l, --language  Language code (ta, en, fr, etc.)
  -s, --silent    Silent mode (no output until done)
  --slow          Slow speed
  -lh             List all languages
  -h              Show this help
  -r              Uninstall

Supported: .txt, .html, .htm, .docx, .md, .pdf

Examples:
  book2audio -i book.pdf -o book.mp3 -l ta
  book2audio -i book.txt -o book.mp3 -l en
  book2audio -i book.pdf -o book.mp3 -s
""")

def main():
    check_deps()
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-h', '--help', action='store_true')
    parser.add_argument('-i', '--input')
    parser.add_argument('-o', '--output')
    parser.add_argument('-l', '--language')
    parser.add_argument('-lh', '--lang_help', action='store_true')
    parser.add_argument('--slow', action='store_true')
    parser.add_argument('-s', '--silent', action='store_true')
    parser.add_argument('-r', '--remove', action='store_true')
    
    args = parser.parse_args()
    
    if args.help: show_help(); sys.exit(0)
    if args.lang_help:
        print("\nLanguages:")
        for k, v in sorted(LANGUAGES.items(), key=lambda x: x[1]):
            print(f"  {k:4s} = {v}")
        sys.exit(0)
    if args.remove:
        if input("Uninstall? (y/n): ").lower() == 'y':
            shutil.rmtree(Path(__file__).parent, ignore_errors=True)
            print("[OK] Uninstalled")
        sys.exit(0)
    
    if not args.input:
        print("[X] Input required: book2audio -i <file> -o <output>")
        sys.exit(1)
    
    if not os.path.exists(args.input):
        print(f"[X] File not found: {args.input}")
        sys.exit(1)
    
    if not args.output:
        args.output = str(Path(args.input).with_suffix('.mp3'))
        print(f"[*] Output: {args.output}")
    
    text = read_file(args.input)
    
    if not args.silent:
        print(f"[*] Characters: {len(text)}")
    
    if args.language:
        lang = args.language.lower()
        if lang not in LANGUAGES:
            print(f"[X] Unknown: {lang}. Use -lh for list")
            sys.exit(1)
    else:
        if not args.silent:
            print("[*] Detecting language...")
        lang = detect_lang(text)
        if not args.silent:
            print(f"[*] Detected: {LANGUAGES.get(lang, lang)} ({lang})")
    
    if not args.silent:
        print("[*] Converting to audio...")
    
    success = text_to_audio(text, lang, args.output, args.slow, args.silent)
    
    if success:
        size = os.path.getsize(args.output) / (1024*1024)
        if args.silent:
            print(f"Done. Path is [{args.output}]")
        else:
            print(f"\n[OK] Done!")
            print(f"    File: {args.output}")
            print(f"    Size: {size:.2f} MB")
    else:
        print("\n[X] Failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
