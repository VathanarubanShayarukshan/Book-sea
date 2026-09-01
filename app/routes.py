from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Book, Bookmark, User
import secrets
import os
import threading
import tempfile

main = Blueprint("main", __name__)

GOOGLE_TTS_MAX = 4500


def chunked_tts(text, lang, output_path):
    """Convert text to MP3 via gTTS, splitting into chunks under GOOGLE_TTS_MAX chars."""
    from gtts import gTTS
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


ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "html", "htm", "xml"}


def get_file_extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def allowed_file(filename):
    return "." in filename and get_file_extension(filename) in ALLOWED_EXTENSIONS


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


def count_pages_or_lines(filepath, file_type):
    try:
        if file_type == "pdf":
            import fitz
            doc = fitz.open(filepath)
            count = len(doc)
            doc.close()
            return count
        else:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                return max(1, len(f.readlines()))
    except:
        return 1


def convert_book_to_audio(book_id, file_path, ext, app_ref):
    """Background audio conversion for uploaded books."""
    with app_ref.app_context():
        try:
            print(f"[BookSea] Starting audio conversion for book {book_id}, file: {file_path}, type: {ext}")
            full_text = extract_text_from_file(file_path, ext)
            if not full_text or not full_text.strip():
                print(f"[BookSea] No text extracted from {file_path} (type={ext}), skipping audio conversion")
                return

            print(f"[BookSea] Extracted {len(full_text)} chars from {file_path}")
            if len(full_text) > 50000:
                full_text = full_text[:50000]

            audio_filename = f"{book_id}_en.mp3"
            audio_path = os.path.join(app_ref.config["UPLOAD_FOLDER_AUDIO"], audio_filename)
            chunked_tts(full_text, "en", audio_path)

            book = Book.query.get(book_id)
            if book:
                book.audio_filename = audio_filename
                db.session.commit()
                print(f"[BookSea] Audio conversion complete: {audio_filename}")
        except Exception as e:
            print(f"[BookSea] Audio conversion failed for book {book_id}: {e}")


@main.route("/")
def home():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "").strip()
    query = Book.query

    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f"%{search}%"),
                Book.description.ilike(f"%{search}%"),
            )
        )

    if current_user.is_authenticated:
        query = query.filter(
            db.or_(
                Book.visibility == "public",
                Book.uploader_id == current_user.id,
                Book.visibility == "share",
            )
        )
    else:
        query = query.filter(Book.visibility == "public")

    books = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=12)
    return render_template("home.html", books=books, search=search)


@main.route("/book/<string:hash_id>")
def view_book(hash_id):
    book = Book.query.filter_by(hash_id=hash_id).first_or_404()

    if book.visibility == "private" and (
        not current_user.is_authenticated or current_user.id != book.uploader_id
    ):
        abort(403)

    bookmark = None
    if current_user.is_authenticated:
        bookmark = Bookmark.query.filter_by(
            user_id=current_user.id, book_id=book.id
        ).first()

    return render_template("book_view.html", book=book, bookmark=bookmark)


@main.route("/book/shared/<token>")
def view_book_shared(token):
    book = Book.query.filter_by(share_token=token, visibility="share").first_or_404()

    bookmark = None
    if current_user.is_authenticated:
        bookmark = Bookmark.query.filter_by(
            user_id=current_user.id, book_id=book.id
        ).first()

    return render_template("book_view.html", book=book, bookmark=bookmark)


@main.route("/book/<string:hash_id>/download")
@login_required
def download_book(hash_id):
    book = Book.query.filter_by(hash_id=hash_id).first_or_404()
    if book.visibility == "private" and current_user.id != book.uploader_id:
        abort(403)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)
    ext = get_file_extension(book.filename)
    return send_file(file_path, as_attachment=True, download_name=f"{book.title}.{ext}")


@main.route("/book/<string:hash_id>/download-audio")
@login_required
def download_audio(hash_id):
    book = Book.query.filter_by(hash_id=hash_id).first_or_404()
    if not book.audio_filename:
        flash("Audio not available yet.", "warning")
        return redirect(url_for("main.view_book", hash_id=hash_id))
    audio_path = os.path.join(current_app.config["UPLOAD_FOLDER_AUDIO"], book.audio_filename)
    return send_file(audio_path, as_attachment=True, download_name=f"{book.title}.mp3")


@main.route("/library")
@login_required
def my_library():
    page = request.args.get("page", 1, type=int)
    books = Book.query.filter_by(uploader_id=current_user.id).order_by(
        Book.created_at.desc()
    ).paginate(page=page, per_page=12)
    return render_template("library.html", books=books)


@main.route("/bookmarks")
@login_required
def my_bookmarks():
    bookmarks = (
        db.session.query(Bookmark, Book)
        .join(Book, Bookmark.book_id == Book.id)
        .filter(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.updated_at.desc())
        .all()
    )
    return render_template("bookmarks.html", bookmarks=bookmarks)


@main.route("/upload", methods=["GET", "POST"])
@login_required
def upload_book():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        visibility = request.form.get("visibility", "public")
        file = request.files.get("book_file")

        if not title:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Book title is required."}), 400
            flash("Book title is required.", "danger")
            return render_template("upload.html")

        if not file or not file.filename:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Please select a file to upload."}), 400
            flash("Please select a file to upload.", "danger")
            return render_template("upload.html")

        if not allowed_file(file.filename):
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"error": "Allowed file types: PDF, TXT, DOCX, HTML, XML"}), 400
            flash("Allowed file types: PDF, TXT, DOCX, HTML, XML", "danger")
            return render_template("upload.html")

        filename = secure_filename(file.filename)
        ext = get_file_extension(filename)
        unique_name = f"{secrets.token_hex(8)}_{filename}"
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], unique_name)
        file.save(file_path)

        page_count = count_pages_or_lines(file_path, ext)
        file_size = os.path.getsize(file_path)
        share_token = secrets.token_urlsafe(32) if visibility == "share" else None

        book = Book(
            title=title,
            description=description,
            filename=unique_name,
            file_type=ext,
            visibility=visibility,
            share_token=share_token,
            uploader_id=current_user.id,
            page_count=page_count,
            file_size=file_size,
        )
        db.session.add(book)
        db.session.commit()

        threading.Thread(
            target=convert_book_to_audio,
            args=(book.id, file_path, ext, current_app._get_current_object()),
            daemon=True,
        ).start()

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({
                "status": "ok",
                "redirect": url_for("main.view_book", hash_id=book.hash_id),
                "hash_id": book.hash_id,
            })

        flash("Book uploaded successfully!", "success")
        return redirect(url_for("main.view_book", hash_id=book.hash_id))

    return render_template("upload.html")


@main.route("/book/<string:hash_id>/delete", methods=["POST"])
@login_required
def delete_book(hash_id):
    book = Book.query.filter_by(hash_id=hash_id).first_or_404()
    if book.uploader_id != current_user.id and not current_user.is_admin:
        abort(403)

    file_path = os.path.join(current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    if book.audio_filename:
        audio_path = os.path.join(current_app.config["UPLOAD_FOLDER_AUDIO"], book.audio_filename)
        if os.path.exists(audio_path):
            os.remove(audio_path)

    Bookmark.query.filter_by(book_id=book.id).delete()
    db.session.delete(book)
    db.session.commit()

    flash("Book deleted.", "info")
    return redirect(url_for("main.home"))
