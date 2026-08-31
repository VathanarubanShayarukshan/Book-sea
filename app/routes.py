from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Book, Bookmark, User
import secrets
import os
import fitz

main = Blueprint("main", __name__)


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
    pdf_path = os.path.join(
        current_app.config["UPLOAD_FOLDER_PDF"], book.filename
    )
    return send_file(pdf_path, as_attachment=True, download_name=f"{book.title}.pdf")


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
        file = request.files.get("pdf_file")

        if not title:
            flash("Book title is required.", "danger")
            return render_template("upload.html")

        if not file or not file.filename.lower().endswith(".pdf"):
            flash("Please upload a valid PDF file.", "danger")
            return render_template("upload.html")

        filename = secure_filename(file.filename)
        unique_name = f"{secrets.token_hex(8)}_{filename}"
        pdf_path = os.path.join(current_app.config["UPLOAD_FOLDER_PDF"], unique_name)
        file.save(pdf_path)

        doc = fitz.open(pdf_path)
        page_count = len(doc)
        doc.close()

        file_size = os.path.getsize(pdf_path)
        share_token = secrets.token_urlsafe(32) if visibility == "share" else None

        book = Book(
            title=title,
            description=description,
            filename=unique_name,
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

    pdf_path = os.path.join(current_app.config["UPLOAD_FOLDER_PDF"], book.filename)
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

    if book.audio_filename:
        audio_path = os.path.join(current_app.config["UPLOAD_FOLDER_AUDIO"], book.audio_filename)
        if os.path.exists(audio_path):
            os.remove(audio_path)

    Bookmark.query.filter_by(book_id=book.id).delete()
    db.session.delete(book)
    db.session.commit()

    flash("Book deleted.", "info")
    return redirect(url_for("main.home"))
