#!/usr/bin/env python3
"""
BookSea CLI - PDF to Audio Converter
Usage: booksea -p <pdf_path> -a <audio_output_path> [-l <language>]
"""
import argparse
import sys
import os

def main():
    parser = argparse.ArgumentParser(
        description="BookSea - Convert PDF books to audio (MP3)"
    )
    parser.add_argument("-p", "--pdf", required=True, help="Path to input PDF file")
    parser.add_argument("-a", "--audio", required=True, help="Path for output audio file (MP3)")
    parser.add_argument("-l", "--language", default="en", help="Language code for TTS (default: en)")
    args = parser.parse_args()

    if not os.path.isfile(args.pdf):
        print(f"Error: PDF file not found: {args.pdf}")
        sys.exit(1)

    if not args.pdf.lower().endswith(".pdf"):
        print("Error: Input file is not a PDF")
        sys.exit(1)

    try:
        import fitz
        from gtts import gTTS
    except ImportError:
        print("Error: Required packages not installed.")
        print("Run: pip install PyMuPDF gTTS")
        sys.exit(1)

    print(f"Reading PDF: {args.pdf}")
    doc = fitz.open(args.pdf)
    full_text = ""
    for i, page in enumerate(doc):
        text = page.get_text()
        full_text += text
        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(doc)} pages...")
    doc.close()

    if not full_text.strip():
        print("Error: No text found in PDF. The PDF might be image-based.")
        sys.exit(1)

    print(f"Converting to audio (language: {args.language})...")
    tts = gTTS(text=full_text, lang=args.language, slow=False)

    os.makedirs(os.path.dirname(os.path.abspath(args.audio)), exist_ok=True)
    tts.save(args.audio)

    size_mb = os.path.getsize(args.audio) / (1024 * 1024)
    print(f"Done! Audio saved to: {args.audio} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
