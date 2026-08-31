from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Book, Bookmark
import os
import fitz  # PyMuPDF
from gtts import gTTS
from deep_translator import GoogleTranslator
import tempfile

api_bp = Blueprint("api", __name__)


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
    return jsonify({"status": "ok", "page": page_number, "position": audio_position})


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
@login_required
def convert_to_audio(book_id):
    book = Book.query.get_or_404(book_id)
    pdf_path = os.path.join(current_app.config["UPLOAD_FOLDER_PDF"], book.filename)

    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF file not found"}), 404

    data = request.get_json() or {}
    lang = data.get("language", "en")

    try:
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        doc.close()

        if not full_text.strip():
            return jsonify({"error": "No text found in PDF"}), 400

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
@login_required
def extract_text(book_id):
    book = Book.query.get_or_404(book_id)
    pdf_path = os.path.join(current_app.config["UPLOAD_FOLDER_PDF"], book.filename)
    page_num = request.args.get("page", 1, type=int) - 1

    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF not found"}), 404

    try:
        doc = fitz.open(pdf_path)
        if page_num < 0 or page_num >= len(doc):
            doc.close()
            return jsonify({"error": "Invalid page number"}), 400
        text = doc[page_num].get_text()
        doc.close()
        return jsonify({"text": text, "page": page_num + 1})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@api_bp.route("/translate", methods=["POST"])
@login_required
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
@login_required
def text_to_speech():
    data = request.get_json()
    text = data.get("text", "")
    lang = data.get("language", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tts.save(f.name)
            return jsonify({"audio_url": f"/api/audio-temp/{os.path.basename(f.name)}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
