from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app, abort
from flask_login import login_required, current_user
from app import db
from app.models import Book
from werkzeug.utils import secure_filename
import os
import secrets

admin_bp = Blueprint("admin", __name__)


def admin_required(f):
    from functools import wraps

    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash("Admin access required.", "danger")
            return redirect(url_for("main.home"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@admin_required
def panel():
    base = os.path.abspath(os.path.join(current_app.root_path, ".."))
    pdf_count = len([f for f in os.listdir(current_app.config["UPLOAD_FOLDER_PDF"]) if f.endswith(".pdf")]) if os.path.exists(current_app.config["UPLOAD_FOLDER_PDF"]) else 0
    audio_count = len([f for f in os.listdir(current_app.config["UPLOAD_FOLDER_AUDIO"]) if f.endswith(".mp3")]) if os.path.exists(current_app.config["UPLOAD_FOLDER_AUDIO"]) else 0
    from app.models import User
    user_count = User.query.count()
    book_count = Book.query.count()
    return render_template(
        "admin/panel.html",
        pdf_count=pdf_count,
        audio_count=audio_count,
        user_count=user_count,
        book_count=book_count,
    )


@admin_bp.route("/files")
@admin_required
def file_manager():
    rel_path = request.args.get("path", "")
    base = os.path.abspath(os.path.join(current_app.root_path, ".."))
    target = os.path.normpath(os.path.join(base, rel_path)) if rel_path else base

    if not target.startswith(base):
        flash("Access denied.", "danger")
        return redirect(url_for("admin.file_manager"))

    items = []
    if os.path.isdir(target):
        for name in sorted(os.listdir(target)):
            full = os.path.join(target, name)
            items.append({
                "name": name,
                "is_dir": os.path.isdir(full),
                "size": os.path.getsize(full) if os.path.isfile(full) else 0,
                "path": os.path.relpath(full, base),
            })

    return render_template(
        "admin/files.html",
        items=items,
        current_path=rel_path,
        base_path=base,
    )


@admin_bp.route("/files/upload", methods=["POST"])
@admin_required
def upload_file():
    rel_path = request.form.get("path", "")
    file = request.files.get("file")
    base = os.path.abspath(os.path.join(current_app.root_path, ".."))
    target = os.path.normpath(os.path.join(base, rel_path)) if rel_path else base

    if not target.startswith(base):
        flash("Access denied.", "danger")
        return redirect(url_for("admin.file_manager"))

    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join(target, filename))
        flash(f"Uploaded {filename}", "success")

    return redirect(url_for("admin.file_manager", path=rel_path))


@admin_bp.route("/files/download/<path:filepath>")
@admin_required
def download_file(filepath):
    base = os.path.abspath(os.path.join(current_app.root_path, ".."))
    full = os.path.normpath(os.path.join(base, filepath))

    if not full.startswith(base) or not os.path.isfile(full):
        abort(404)

    return send_file(full, as_attachment=True)


@admin_bp.route("/files/delete", methods=["POST"])
@admin_required
def delete_file():
    data = request.get_json()
    filepath = data.get("path", "")
    base = os.path.abspath(os.path.join(current_app.root_path, ".."))
    full = os.path.normpath(os.path.join(base, filepath))

    if not full.startswith(base):
        return jsonify({"error": "Access denied"}), 403

    try:
        if os.path.isdir(full):
            os.rmdir(full)
        else:
            os.remove(full)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/books")
@admin_required
def manage_books():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template("admin/books.html", books=books)


@admin_bp.route("/users")
@admin_required
def manage_users():
    from app.models import User
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)
