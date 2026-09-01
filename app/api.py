from flask import Blueprint, request, jsonify, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.models import Book, Bookmark
import os
import tempfile
from gtts import gTTS
from deep_translator import GoogleTranslator

api_bp = Blueprint("api", __name__)

TEMP_DIR = os.path.join(tempfile.gettempdir(), "booksea_audio")

GOOGLE_TTS_MAX = 4500


def chunked_tts(text, lang, output_path):
    """Convert text to MP3 via gTTS, splitting into chunks under GOOGLE_TTS_MAX chars."""
    chunks = []
    sentences = text.replace("\n", " \n ").split(". ")
    current = ""
    for s in sentences:
        if len(current) + len(s) + 2 > GOOGLE_TTS_MAX:
            if current.strip():
                chunks.append(current.strip())
            current = s
        else:
            current = (current + ". " + s) if current else s
    if current.strip():
        chunks.append(current.strip())

    if not chunks:
        raise ValueError("No text to convert")

    tmp_dir = tempfile.mkdtemp(prefix="booksea_tts_")
    part_files = []
    for i, chunk in enumerate(chunks):
        tts = gTTS(text=chunk, lang=lang, slow=False)
        part_path = os.path.join(tmp_dir, f"part_{i:04d}.mp3")
        tts.save(part_path)
        part_files.append(part_path)

    with open(output_path, "wb") as out_f:
        for pf in part_files:
            with open(pf, "rb") as in_f:
                out_f.write(in_f.read())
            os.remove(pf)
    os.rmdir(tmp_dir)


def ensure_temp_dir():
    os.makedirs(TEMP_DIR, exist_ok=True)


def extract_text_from_file(filepath, file_type):
    try:
        if file_type == "pdf":
            import fitz
            doc = fitz.open(filepath)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        elif file_type == "txt":
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif file_type == "docx":
            from docx import Document
            doc = Document(filepath)
            return "\n".join([para.text for para in doc.paragraphs])
        elif file_type in ("html", "htm"):
            from bs4 import BeautifulSoup
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(filepath, "r", encoding=enc) as f:
                        content = f.read()
                    soup = BeautifulSoup(content, "html.parser")
                    text = soup.get_text(separator="\n", strip=True)
                    if text and text.strip():
                        return text
                except (UnicodeDecodeError, UnicodeError):
                    continue
            return ""
        elif file_type == "xml":
            from bs4 import BeautifulSoup
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    with open(filepath, "r", encoding=enc) as f:
                        content = f.read()
                    soup = BeautifulSoup(content, "xml")
                    text = soup.get_text(separator="\n", strip=True)
                    if text and text.strip():
                        return text
                except (UnicodeDecodeError, UnicodeError):
                    continue
            return ""
    except Exception as e:
        print(f"[BookSea] extract_text error for {filepath}: {e}")
        return ""
    return ""


@api_bp.route("/bookmark", methods=["POST"])
@login_required
def save_bookmark():
    data = request.get_json(silent=True) or {}
    book_hash = data.get("book_hash")
    page_number = data.get("page_number", 1)
    audio_position = data.get("audio_position", 0.0)

    book = Book.query.filter_by(hash_id=book_hash).first()
    if not book:
        return jsonify({"error": "Book not found"}), 404

    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id, book_id=book.id
    ).first()

    if bookmark:
        bookmark.page_number = page_number
        bookmark.audio_position = audio_position
    else:
        bookmark = Bookmark(
            user_id=current_user.id,
            book_id=book.id,
            page_number=page_number,
            audio_position=audio_position,
        )
        db.session.add(bookmark)

    db.session.commit()
    return jsonify({"status": "ok"})


@api_bp.route("/bookmark/<string:book_hash>", methods=["GET"])
@login_required
def get_bookmark(book_hash):
    book = Book.query.filter_by(hash_id=book_hash).first()
    if not book:
        return jsonify({"error": "Book not found"}), 404

    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id, book_id=book.id
    ).first()
    if bookmark:
        return jsonify({
            "page_number": bookmark.page_number,
            "audio_position": bookmark.audio_position,
        })
    return jsonify({"page_number": 1, "audio_position": 0.0})


@api_bp.route("/convert-audio/<string:book_hash>", methods=["POST"])
def convert_to_audio(book_hash):
    book = Book.query.filter_by(hash_id=book_hash).first()
    if not book:
        return jsonify({"error": "Book not found"}), 404

    if book.visibility == "private":
        if not current_user.is_authenticated or current_user.id != book.uploader_id:
            return jsonify({"error": "Access denied"}), 403

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)

    if not os.path.exists(file_path):
        return jsonify({"error": f"File not found: {book.filename}"}), 404

    data = request.get_json(silent=True) or {}
    lang = data.get("language", "en")

    try:
        print(f"[BookSea] Manual convert-audio: {file_path} (type={book.file_type})")
        full_text = extract_text_from_file(file_path, book.file_type)

        if not full_text or not full_text.strip():
            print(f"[BookSea] Manual convert: no text from {file_path}")
            return jsonify({"error": "No text found in file. The file might be image-based or empty. Try uploading a PDF with selectable text (not a scanned/image PDF)."}), 400

        if len(full_text) > 50000:
            full_text = full_text[:50000]

        print(f"[BookSea] Manual convert: {len(full_text)} chars, lang={lang}")
        audio_filename = f"{book.id}_{lang}.mp3"
        audio_path = os.path.join(current_app.config["UPLOAD_FOLDER_AUDIO"], audio_filename)
        chunked_tts(full_text, lang, audio_path)

        book.audio_filename = audio_filename
        db.session.commit()

        print(f"[BookSea] Manual convert done: {audio_filename}")
        return jsonify({"status": "ok", "audio_url": f"/media/audio/{audio_filename}"})
    except Exception as e:
        print(f"[BookSea] Manual convert failed: {e}")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/extract-text/<string:book_hash>", methods=["GET"])
def extract_text(book_hash):
    book = Book.query.filter_by(hash_id=book_hash).first_or_404()

    if book.visibility == "private":
        if not current_user.is_authenticated or current_user.id != book.uploader_id:
            return jsonify({"error": "Access denied"}), 403

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)
    page_num = request.args.get("page", 1, type=int) - 1

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        if book.file_type == "pdf":
            import fitz
            doc = fitz.open(file_path)
            if page_num < 0 or page_num >= len(doc):
                doc.close()
                return jsonify({"error": "Invalid page number"}), 400
            text = doc[page_num].get_text()
            doc.close()
        elif book.file_type in ("html", "htm", "xml"):
            from bs4 import BeautifulSoup
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                text = soup.get_text(separator="\n", strip=True)
                text_lines = text.split("\n")
                start = max(0, page_num)
                end = min(len(text_lines), start + 50)
                text = "\n".join(text_lines[start:end])
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if page_num < 0 or page_num >= len(lines):
                    return jsonify({"error": "Invalid line number"}), 400
                text = lines[page_num]

        return jsonify({"text": text, "page": page_num + 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/full-text/<string:book_hash>", methods=["GET"])
def get_full_text(book_hash):
    book = Book.query.filter_by(hash_id=book_hash).first_or_404()

    if book.visibility == "private":
        if not current_user.is_authenticated or current_user.id != book.uploader_id:
            return jsonify({"error": "Access denied"}), 403

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        text = extract_text_from_file(file_path, book.file_type)
        return jsonify({"text": text, "file_type": book.file_type})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/raw-file/<string:book_hash>", methods=["GET"])
def get_raw_file(book_hash):
    book = Book.query.filter_by(hash_id=book_hash).first_or_404()

    if book.visibility == "private":
        if not current_user.is_authenticated or current_user.id != book.uploader_id:
            return jsonify({"error": "Access denied"}), 403

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return jsonify({"content": content, "file_type": book.file_type})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/translate", methods=["POST"])
def translate_text():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    target_lang = data.get("target", "en")

    if not text or not text.strip():
        return jsonify({"error": "No text provided"}), 400

    try:
        max_chunk = 4500
        if len(text) <= max_chunk:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
            return jsonify({"translated": translated, "target": target_lang})

        chunks = []
        sentences = text.replace("\n", " \n ").split(". ")
        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 > max_chunk:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = current_chunk + ". " + sentence if current_chunk else sentence
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        translated_chunks = []
        for chunk in chunks:
            try:
                t = GoogleTranslator(source="auto", target=target_lang).translate(chunk)
                translated_chunks.append(t)
            except Exception:
                translated_chunks.append(chunk)

        return jsonify({"translated": " ".join(translated_chunks), "target": target_lang})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/text-to-speech", methods=["POST"])
def text_to_speech():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "")
    lang = data.get("language", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        if len(text) > 5000:
            text = text[:5000]

        ensure_temp_dir()
        tts = gTTS(text=text, lang=lang, slow=False)
        filename = f"tts_{os.urandom(8).hex()}.mp3"
        filepath = os.path.join(TEMP_DIR, filename)
        tts.save(filepath)
        return jsonify({"audio_url": f"/api/audio-temp/{filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/audio-temp/<filename>")
def serve_temp_audio(filename):
    filepath = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    return send_file(filepath, mimetype="audio/mpeg")
