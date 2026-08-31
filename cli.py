#!/usr/bin/env python3
"""
BookSea CLI - Book to Audio Converter
Usage: booksea -p <file_path> -a <audio_output_path> [-l <language>]
Supports: PDF, TXT, DOCX, HTML, XML
"""
import argparse
import sys
import os


ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".html", ".htm", ".xml"}


def extract_text(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".pdf":
        import fitz
        doc = fitz.open(filepath)
        text = ""
        for i, page in enumerate(doc):
            text += page.get_text()
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(doc)} pages...")
        doc.close()
        return text

    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    elif ext == ".docx":
        from docx import Document
        doc = Document(filepath)
        return "\n".join([para.text for para in doc.paragraphs])

    elif ext in (".html", ".htm"):
        from bs4 import BeautifulSoup
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
            return soup.get_text(separator="\n", strip=True)

    elif ext == ".xml":
        from bs4 import BeautifulSoup
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "xml")
            return soup.get_text(separator="\n", strip=True)

    return ""


def main():
    parser = argparse.ArgumentParser(
        description="BookSea - Convert books to audio (MP3)"
    )
    parser.add_argument("-p", "--path", required=True, help="Path to input file (PDF, TXT, DOCX, HTML, XML)")
    parser.add_argument("-a", "--audio", required=True, help="Path for output audio file (MP3)")
    parser.add_argument("-l", "--language", default="en", help="Language code for TTS (default: en)")
    args = parser.parse_args()

    if not os.path.isfile(args.path):
        print(f"Error: File not found: {args.path}")
        sys.exit(1)

    ext = os.path.splitext(args.path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        print(f"Error: Unsupported file type: {ext}")
        print(f"Supported: {', '.join(ALLOWED_EXTENSIONS)}")
        sys.exit(1)

    try:
        from gtts import gTTS
    except ImportError:
        print("Error: gTTS not installed.")
        print("Run: uv pip install gtts")
        sys.exit(1)

    if ext == ".pdf":
        try:
            import fitz
        except ImportError:
            print("Error: PyMuPDF not installed.")
            print("Run: uv pip install PyMuPDF")
            sys.exit(1)

    if ext == ".docx":
        try:
            import docx
        except ImportError:
            print("Error: python-docx not installed.")
            print("Run: uv pip install python-docx")
            sys.exit(1)

    if ext in (".html", ".htm", ".xml"):
        try:
            import bs4
        except ImportError:
            print("Error: beautifulsoup4 not installed.")
            print("Run: uv pip install beautifulsoup4 lxml")
            sys.exit(1)

    print(f"Reading file: {args.path}")
    full_text = extract_text(args.path)

    if not full_text.strip():
        print("Error: No text found in file.")
        sys.exit(1)

    print(f"Converting to audio (language: {args.language})...")
    tts = gTTS(text=full_text, lang=args.language, slow=False)

    os.makedirs(os.path.dirname(os.path.abspath(args.audio)), exist_ok=True)
    tts.save(args.audio)

    size_mb = os.path.getsize(args.audio) / (1024 * 1024)
    print(f"Done! Audio saved to: {args.audio} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
