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
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                return soup.get_text(separator="\n", strip=True)
        elif file_type == "xml":
            from bs4 import BeautifulSoup
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f.read(), "xml")
                return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return ""
    return ""


@api_bp.route("/bookmark", methods=["POST"])
@login_required
def save_bookmark():
    data = request.get_json()
    book_id = data.get("book_id")
    page_number = data.get("page_number", 1)
    audio_position = data.get("audio_position", 0.0)

    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id, book_id=book_id
    ).first()

    if bookmark:
        bookmark.page_number = page_number
        bookmark.audio_position = audio_position
    else:
        bookmark = Bookmark(
            user_id=current_user.id,
            book_id=book_id,
            page_number=page_number,
            audio_position=audio_position,
        )
        db.session.add(bookmark)

    db.session.commit()
    return jsonify({"status": "ok"})


@api_bp.route("/bookmark/<int:book_id>", methods=["GET"])
@login_required
def get_bookmark(book_id):
    bookmark = Bookmark.query.filter_by(
        user_id=current_user.id, book_id=book_id
    ).first()
    if bookmark:
        return jsonify({
            "page_number": bookmark.page_number,
            "audio_position": bookmark.audio_position,
        })
    return jsonify({"page_number": 1, "audio_position": 0.0})


@api_bp.route("/convert-audio/<int:book_id>", methods=["POST"])
def convert_to_audio(book_id):
    book = Book.query.get_or_404(book_id)

    if book.visibility == "private":
        if not current_user.is_authenticated or current_user.id != book.uploader_id:
            return jsonify({"error": "Access denied"}), 403

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    data = request.get_json() or {}
    lang = data.get("language", "en")

    try:
        full_text = extract_text_from_file(file_path, book.file_type)

        if not full_text or not full_text.strip():
            return jsonify({"error": "No text found in file. The file might be image-based or empty."}), 400

        if len(full_text) > 50000:
            full_text = full_text[:50000]

        tts = gTTS(text=full_text, lang=lang, slow=False)
        audio_filename = f"{book.id}_{lang}.mp3"
        audio_path = os.path.join(current_app.config["UPLOAD_FOLDER_AUDIO"], audio_filename)
        tts.save(audio_path)

        book.audio_filename = audio_filename
        db.session.commit()

        return jsonify({"status": "ok", "audio_url": f"/media/audio/{audio_filename}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/extract-text/<int:book_id>", methods=["GET"])
def extract_text(book_id):
    book = Book.query.get_or_404(book_id)

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
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                if page_num < 0 or page_num >= len(lines):
                    return jsonify({"error": "Invalid line number"}), 400
                text = lines[page_num]

        return jsonify({"text": text, "page": page_num + 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/full-text/<int:book_id>", methods=["GET"])
def get_full_text(book_id):
    book = Book.query.get_or_404(book_id)

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


@api_bp.route("/translate", methods=["POST"])
def translate_text():
    data = request.get_json()
    text = data.get("text", "")
    target_lang = data.get("target", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
        return jsonify({"translated": translated, "target": target_lang})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/text-to-speech", methods=["POST"])
def text_to_speech():
    data = request.get_json()
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
