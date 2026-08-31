from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User
import bcrypt
import secrets

auth = Blueprint("auth", __name__)


@auth.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        errors = []
        if not username or len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if not email or "@" not in email:
            errors.append("Valid email is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")
        if User.query.filter_by(username=username).first():
            errors.append("Username already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/signup.html")

        user = User(username=username, email=email)
        user.set_password(password)

        if User.query.count() == 0:
            user.is_admin = True

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created successfully!", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/signup.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter(
            (User.email == login_id.lower()) | (User.username == login_id)
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get("next")
            flash("Logged in successfully!", "success")
            return redirect(next_page or url_for("main.home"))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("auth/login.html")


@auth.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("main.home"))


@auth.route("/google/callback")
def google_callback():
    code = request.args.get("code")
    if not code:
        flash("Google authentication failed.", "danger")
        return redirect(url_for("auth.login"))

    from app import Config
    import requests

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": Config.GOOGLE_CLIENT_ID,
        "client_secret": Config.GOOGLE_CLIENT_SECRET,
        "redirect_uri": url_for("auth.google_callback", _external=True),
        "grant_type": "authorization_code",
    }
    resp = requests.post(token_url, data=data)
    if resp.status_code != 200:
        flash("Google authentication failed.", "danger")
        return redirect(url_for("auth.login"))

    access_token = resp.json().get("access_token")
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(userinfo_url, headers=headers)
    if resp.status_code != 200:
        flash("Google authentication failed.", "danger")
        return redirect(url_for("auth.login"))

    google_user = resp.json()
    google_id = google_user.get("id")
    email = google_user.get("email", "").lower()
    name = google_user.get("name", "")
    avatar = google_user.get("picture", "")

    user = User.query.filter_by(google_id=google_id).first()
    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            user.google_id = google_id
            user.avatar = avatar
        else:
            username = name.replace(" ", "").lower() + "_" + secrets.token_hex(3)
            while User.query.filter_by(username=username).first():
                username = name.replace(" ", "").lower() + "_" + secrets.token_hex(3)
            user = User(
                username=username,
                email=email,
                google_id=google_id,
                avatar=avatar,
                password_hash="",
            )
            user.set_password(secrets.token_hex(16))
            db.session.add(user)
        db.session.commit()

    login_user(user)
    flash("Signed in with Google!", "success")
    return redirect(url_for("main.home"))
