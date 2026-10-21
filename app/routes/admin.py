import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from functools import wraps
from .. import mongo
from ..models.flight import (
    get_all_flights,
    create_flight,
    get_flight_by_id,
    update_flight,
    delete_flight,
    add_photo_to_flight,
    remove_photo_from_flight,
)
from ..models.booking import get_all_bookings

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin():
            flash("Admin access required.", "danger")
            return redirect(url_for("auth.index"))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route("/")
@admin_required
def dashboard():
    total_flights = mongo.db.flights.count_documents({"status": "active"})
    total_bookings = mongo.db.bookings.count_documents({})
    confirmed = mongo.db.bookings.count_documents({"status": "confirmed"})
    cancelled = mongo.db.bookings.count_documents({"status": "cancelled"})
    total_users = mongo.db.users.count_documents({"role": "user"})

    stats = {
        "total_flights": total_flights,
        "total_bookings": total_bookings,
        "confirmed": confirmed,
        "cancelled": cancelled,
        "total_users": total_users,
    }
    recent_bookings = get_all_bookings()[:5]
    return render_template("admin/dashboard.html", stats=stats, recent_bookings=recent_bookings)


@admin_bp.route("/flights")
@admin_required
def flights():
    all_flights = get_all_flights(status=None)
    return render_template("admin/flights.html", flights=all_flights)


@admin_bp.route("/flights/add", methods=["GET", "POST"])
@admin_required
def add_flight():
    if request.method == "POST":
        flight_number = request.form.get("flight_number", "").strip().upper()
        airline = request.form.get("airline", "").strip()
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        departure_date = request.form.get("departure_date", "").strip()
        departure_time = request.form.get("departure_time", "").strip()
        arrival_time = request.form.get("arrival_time", "").strip()
        seats_total = int(request.form.get("seats_total", 100))
        price = float(request.form.get("price", 0))
        flight_class = request.form.get("flight_class", "Economy")
        aircraft_model = request.form.get("aircraft_model", "Boeing 737-800")
        photo_url = request.form.get("photo_url", "").strip()

        # Handle file upload if provided
        file = request.files.get("photo_file")
        if file and file.filename != "" and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.root_path, "static", "uploads", "flights")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, filename)
            file.save(file_path)
            photo_url = url_for("static", filename=f"uploads/flights/{filename}")

        if not all([flight_number, airline, origin, destination, departure_date]):
            flash("Please fill all required fields.", "danger")
            return render_template("admin/add_flight.html")

        data = {
            "flight_number": flight_number,
            "airline": airline,
            "origin": origin,
            "destination": destination,
            "departure_date": departure_date,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "seats_total": seats_total,
            "seats_available": seats_total,
            "price": price,
            "class": flight_class,
            "aircraft_model": aircraft_model,
            "photo_url": photo_url or "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80",
            "status": "active",
        }

        try:
            create_flight(data)
            flash(f"Flight {flight_number} added with embedded documents & photos successfully!", "success")
            return redirect(url_for("admin.flights"))
        except Exception as e:
            flash(f"Error adding flight: {str(e)}", "danger")

    return render_template("admin/add_flight.html")


@admin_bp.route("/flights/<flight_id>/photos/add", methods=["POST"])
@admin_required
def add_flight_photo(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        flash("Flight not found.", "danger")
        return redirect(url_for("admin.flights"))

    caption = request.form.get("caption", "Flight Photo").strip()
    is_primary = request.form.get("is_primary") == "on"
    photo_url = request.form.get("photo_url", "").strip()

    file = request.files.get("photo_file")
    if file and file.filename != "" and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, "static", "uploads", "flights")
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))
        photo_url = url_for("static", filename=f"uploads/flights/{filename}")

    if not photo_url:
        flash("Please provide an image URL or upload an image file.", "danger")
        return redirect(url_for("admin.flights"))

    add_photo_to_flight(flight_id, photo_url, caption, is_primary)
    flash("Photo added to flight embedded document!", "success")
    return redirect(url_for("admin.flights"))


@admin_bp.route("/flights/<flight_id>/photos/remove", methods=["POST"])
@admin_required
def remove_flight_photo(flight_id):
    photo_url = request.form.get("photo_url", "").strip()
    if photo_url:
        remove_photo_from_flight(flight_id, photo_url)
        flash("Photo removed from flight embedded document.", "info")
    return redirect(url_for("admin.flights"))


@admin_bp.route("/flights/<flight_id>/toggle", methods=["POST"])
@admin_required
def toggle_flight(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        flash("Flight not found.", "danger")
        return redirect(url_for("admin.flights"))
    new_status = "inactive" if flight.get("status") == "active" else "active"
    update_flight(flight_id, {"status": new_status})
    flash(f"Flight status updated to {new_status}.", "success")
    return redirect(url_for("admin.flights"))


@admin_bp.route("/bookings")
@admin_required
def bookings():
    all_bookings = get_all_bookings()
    return render_template("admin/bookings.html", bookings=all_bookings)
