from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from .. import bcrypt
from ..models.user import get_user_by_email, create_user, User

from ..models.flight import get_featured_flights

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    featured_flights = get_featured_flights()
    return render_template("index.html", featured_flights=featured_flights)



@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not all([name, email, password, confirm]):
            flash("All fields are required.", "danger")
            return render_template("auth/register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("auth/register.html")

        if get_user_by_email(email):
            flash("Email already registered.", "danger")
            return render_template("auth/register.html")

        hashed = bcrypt.generate_password_hash(password).decode("utf-8")
        create_user(name, email, hashed)
        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user_doc = get_user_by_email(email)
        if user_doc and bcrypt.check_password_hash(user_doc["password"], password):
            user = User(user_doc)
            login_user(user)
            next_page = request.args.get("next")
            flash(f"Welcome back, {user.name}!", "success")
            return redirect(next_page or url_for("auth.index"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.index"))
