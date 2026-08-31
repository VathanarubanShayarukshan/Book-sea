from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
import bcrypt


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    avatar = db.Column(db.String(256), default="")
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    books = db.relationship("Book", backref="uploader", lazy=True)
    bookmarks = db.relationship("Bookmark", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    filename = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(10), default="pdf")  # pdf, txt, docx, html, xml
    audio_filename = db.Column(db.String(256), default="")
    cover_image = db.Column(db.String(256), default="")
    visibility = db.Column(db.String(20), default="public")  # public, private, share
    share_token = db.Column(db.String(64), unique=True, nullable=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    page_count = db.Column(db.Integer, default=0)
    file_size = db.Column(db.Integer, default=0)
    language = db.Column(db.String(10), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bookmarks = db.relationship("Bookmark", backref="book", lazy=True)


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    page_number = db.Column(db.Integer, default=1)
    audio_position = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "book_id", name="unique_user_book"),)
