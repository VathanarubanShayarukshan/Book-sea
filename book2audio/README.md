# book2audio

Convert any text format books to audio files. Supports multiple languages including Tamil, English, French, and many more.

## Features

- Convert text files (.txt) to audio
- Convert HTML files (.html, .htm) to audio
- Convert Word documents (.docx) to audio
- Convert OpenDocument files (.odt) to audio
- Convert Markdown files (.md, .markdown) to audio
- Convert RTF files (.rtf) to audio
- Convert EPUB files (.epub) to audio
- Convert FB2 files (.fb2) to audio
- Support for 60+ languages
- Automatic language detection
- Simple command-line interface
- Free and open source (no API keys required)

## Installation

### Quick Install (Termux/Kali/Ubuntu/Debian)

```bash
# Download and run the installer
git clone https://github.com/username/book2audio.git
cd book2audio
chmod +x install.sh
./install.sh
```

### Manual Install

```bash
# Install Python dependencies
pip install gTTS langdetect beautifulsoup4 python-docx markdown odfpy pydub

# Install ffmpeg (required for audio merging)
# Termux:
pkg install ffmpeg

# Kali/Ubuntu/Debian:
sudo apt install ffmpeg

# Make the script executable
chmod +x book2audio.py

# Create a symlink (optional)
sudo ln -s $(pwd)/book2audio.py /usr/local/bin/book2audio
```

## Usage

### Basic Usage

```bash
# Convert a text file to audio (auto-detect language)
book2audio -i book.txt -o audiobook.mp3

# Convert with specific language
book2audio -i book.txt -o audiobook.mp3 -l ta

# Convert HTML to audio
book2audio -i book.html -o audiobook.mp3

# Convert Word document to audio
book2audio -i book.docx -o audiobook.mp3
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `-h, --help` | Show help menu |
| `-i, --input FILE` | Input file path |
| `-o, --output FILE` | Output audio file path |
| `-l, --language LANG` | Output language code |
| `-lh, --lang_help` | Show available languages |
| `-u, --update` | Update from GitHub repository |
| `-r, --remove` | Uninstall the application |
| `-s, --slow` | Slow audio speed |

### Supported Languages

Use `book2audio -lh` to see all supported languages. Some examples:

- `ta` - Tamil
- `en` - English
- `fr` - French
- `de` - German
- `es` - Spanish
- `hi` - Hindi
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- `ar` - Arabic

### Examples

```bash
# Convert a Tamil book to audio
book2audio -i thirukkural.txt -o thirukkural.mp3 -l ta

# Convert an English novel to audio
book2audio -i novel.docx -o novel_audiobook.mp3 -l en

# Auto-detect language and convert
book2audio -i unknown_book.html -o output.mp3

# Slow speed audio (useful for learning)
book2audio -i lesson.txt -o lesson_slow.mp3 -l ta -s

# Show help
book2audio -h

# Show available languages
book2audio -lh

# Update the application
book2audio -u https://github.com/username/book2audio

# Uninstall the application
book2audio -r
```

## Supported File Formats

| Format | Extension | Description |
|--------|-----------|-------------|
| Plain Text | `.txt` | Text files |
| HTML | `.html`, `.htm` | Web pages |
| Word | `.docx` | Microsoft Word documents |
| OpenDocument | `.odt` | LibreOffice Writer documents |
| Markdown | `.md`, `.markdown` | Markdown files |
| RTF | `.rtf` | Rich Text Format |
| EPUB | `.epub` | E-book format |
| FB2 | `.fb2` | FictionBook format |

## Updating

To update to the latest version:

```bash
book2audio -u https://github.com/username/book2audio
```

Or manually:

```bash
cd ~/.book2audio
git pull
```

## Uninstalling

To remove book2audio:

```bash
book2audio -r
```

Or manually:

```bash
rm -rf ~/.book2audio
sudo rm /usr/local/bin/book2audio
```

## Requirements

- Python 3.6 or higher
- ffmpeg (for audio merging)
- Internet connection (for Google Text-to-Speech)

## Troubleshooting

### "Command not found" error

Make sure the installation directory is in your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Language detection issues

If automatic language detection fails, specify the language explicitly:

```bash
book2audio -i book.txt -o output.mp3 -l ta
```

### Audio quality issues

For better quality, you can use the slow option:

```bash
book2audio -i book.txt -o output.mp3 -s
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

book2audio

## Acknowledgments

- gTTS - Google Text-to-Speech library
- langdetect - Language detection library
- BeautifulSoup - Web scraping library
- python-docx - Word document reader
- odfpy - OpenDocument reader
