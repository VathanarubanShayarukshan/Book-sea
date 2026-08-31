from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Book, Bookmark, User
import secrets
import os

main = Blueprint("main", __name__)


ALLOWED_EXTENSIONS = {"pdf", "txt", "docx", "html", "htm", "xml"}
MIME_TYPES = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "html": "text/html",
    "htm": "text/html",
    "xml": "application/xml",
}


def get_file_extension(filename):
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def allowed_file(filename):
    return "." in filename and get_file_extension(filename) in ALLOWED_EXTENSIONS


def extract_text_from_file(filepath, file_type):
    """Extract text content from various file types."""
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
        return f"Error reading file: {str(e)}"
    return ""


def count_pages_or_lines(filepath, file_type):
    """Count pages for PDF, lines for other files."""
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


@main.route("/book/<int:book_id>")
def view_book(book_id):
    book = Book.query.get_or_404(book_id)

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


@main.route("/book/<int:book_id>/download")
@login_required
def download_book(book_id):
    book = Book.query.get_or_404(book_id)
    if book.visibility == "private" and current_user.id != book.uploader_id:
        abort(403)
    file_path = os.path.join(
        current_app.config["UPLOAD_FOLDER_BOOKS"], book.filename
    )
    ext = get_file_extension(book.filename)
    return send_file(file_path, as_attachment=True, download_name=f"{book.title}.{ext}")


@main.route("/book/<int:book_id>/download-audio")
@login_required
def download_audio(book_id):
    book = Book.query.get_or_404(book_id)
    if not book.audio_filename:
        flash("Audio not available yet.", "warning")
        return redirect(url_for("main.view_book", book_id=book_id))
    audio_path = os.path.join(
        current_app.config["UPLOAD_FOLDER_AUDIO"], book.audio_filename
    )
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
            flash("Book title is required.", "danger")
            return render_template("upload.html")

        if not file or not file.filename:
            flash("Please select a file to upload.", "danger")
            return render_template("upload.html")

        if not allowed_file(file.filename):
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

        flash("Book uploaded successfully!", "success")
        return redirect(url_for("main.view_book", book_id=book.id))

    return render_template("upload.html")


@main.route("/book/<int:book_id>/delete", methods=["POST"])
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
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
