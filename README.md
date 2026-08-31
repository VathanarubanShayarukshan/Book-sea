# BookSea - Digital Library

A Python-based web application for managing and reading PDF books online with audio conversion support.

## Features

- **PDF Reading** - Read PDF books directly in your browser with a built-in viewer
- **PDF to Audio** - Convert PDF books to audio (MP3) using Google Text-to-Speech
- **Audio Player** - Listen to audio books online or download as MP3
- **Bookmarks** - Auto-saves your reading position (like YouTube video bookmarks)
- **User Authentication** - Sign up with email/password or Google account
- **Book Upload** - Upload PDF books with title, description, and visibility settings
- **Visibility Options** - Public, Private, or Share Link only
- **Book Sharing** - Share books via URL, WhatsApp, or copy link
- **Search** - Search books by title or description
- **Translation** - Translate and listen to books in any language (16+ languages)
- **Admin Panel** - Full file manager, book management, and user management

## Quick Start

### Linux/Mac
```bash
chmod +x scripts/install.sh
./scripts/install.sh
python run.py
```

### Windows
```batch
scripts\install.bat
python run.py
```

### CLI Tool - PDF to Audio
```bash
# Install CLI
pip install -e .

# Convert PDF to audio
booksea -p /path/to/book.pdf -a /path/to/output.mp3
booksea -p book.pdf -a output.mp3 -l ta  # Tamil

# Or use the script directly
python cli.py -p book.pdf -a output.mp3 -l en
```

### Update from GitHub
```bash
./scripts/update.sh      # Linux/Mac
scripts\update.bat       # Windows
```

## Tech Stack

- **Backend**: Flask + SQLAlchemy + SQLite
- **Frontend**: Bootstrap 5 + pdf.js
- **Auth**: Flask-Login + bcrypt + Google OAuth
- **PDF**: PyMuPDF (fitz) + pdf.js
- **Audio**: gTTS (Google Text-to-Speech)
- **Translation**: deep-translator

## Configuration

Copy `.env.example` to `.env` and configure:

```env
SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

## Project Structure

```
book-sea/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── models.py        # Database models
│   ├── routes.py        # Main routes
│   ├── auth.py          # Authentication
│   ├── api.py           # REST API (bookmarks, audio, translation)
│   ├── admin.py         # Admin panel
│   ├── static/css/      # Styles
│   ├── static/js/       # JavaScript
│   └── templates/       # HTML templates
├── media/
│   ├── pdf/             # Uploaded PDF files
│   └── audio/           # Generated audio files
├── scripts/
│   ├── install.sh/bat   # Setup script
│   ├── update.sh/bat    # GitHub update script
│   ├── booksea-audio.sh/bat  # CLI audio converter
│   └── update.sh/bat    # GitHub update
├── cli.py               # CLI entry point
├── run.py               # Web server entry point
├── setup.py             # Package setup
├── requirements.txt     # Python dependencies
└── .env.example         # Configuration template
```

## License

MIT
