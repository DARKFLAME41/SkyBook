from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from bson import ObjectId
from ..models.flight import get_flight_by_id, decrement_seats, increment_seats
from ..models.booking import (
    create_booking,
    get_bookings_by_user,
    get_booking_by_id,
    cancel_booking,
    calculate_cancellation_refund,
)

bookings_bp = Blueprint("bookings", __name__, url_prefix="/bookings")



@bookings_bp.route("/")
@login_required
def list_bookings():
    bookings = get_bookings_by_user(current_user.id)
    return render_template("bookings/list.html", bookings=bookings)


@bookings_bp.route("/new/<flight_id>", methods=["GET", "POST"])
@login_required
def new_booking(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        flash("Flight not found.", "danger")
        return redirect(url_for("flights.search"))

    if flight["seats_available"] <= 0:
        flash("No seats available on this flight.", "danger")
        return redirect(url_for("flights.detail", flight_id=flight_id))

    if request.method == "POST":
        seat_count = int(request.form.get("seat_count", 1))
        passengers = []

        for i in range(seat_count):
            passenger = {
                "name": request.form.get(f"passenger_name_{i}", "").strip(),
                "age": request.form.get(f"passenger_age_{i}", "").strip(),
                "gender": request.form.get(f"passenger_gender_{i}", "").strip(),
            }
            if not passenger["name"]:
                flash(f"Passenger {i + 1} name is required.", "danger")
                return render_template(
                    "bookings/confirm.html",
                    flight=flight,
                    seat_count=seat_count,
                )
            passengers.append(passenger)

        if seat_count > flight["seats_available"]:
            flash(
                f"Only {flight['seats_available']} seats available.", "danger"
            )
            return render_template(
                "bookings/confirm.html", flight=flight, seat_count=1
            )

        total_price = flight["price"] * seat_count

        # Decrement seats first
        decrement_seats(flight_id, seat_count)

        booking_id = create_booking(
            current_user.id,
            flight_id,
            passengers,
            seat_count,
            total_price,
        )

        flash("Booking confirmed!", "success")
        return redirect(url_for("bookings.booking_success", booking_id=str(booking_id)))

    seat_count = int(request.args.get("seats", 1))
    return render_template("bookings/confirm.html", flight=flight, seat_count=seat_count)


@bookings_bp.route("/success/<booking_id>")
@login_required
def booking_success(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking or str(booking["user_id"]) != current_user.id:
        flash("Booking not found.", "danger")
        return redirect(url_for("bookings.list_bookings"))
    return render_template("bookings/success.html", booking=booking)


@bookings_bp.route("/<booking_id>/cancel", methods=["GET", "POST"])
@login_required
def cancel(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking or str(booking["user_id"]) != current_user.id:
        flash("Booking not found.", "danger")
        return redirect(url_for("bookings.list_bookings"))

    if booking["status"] == "cancelled":
        flash("Booking is already cancelled.", "warning")
        return redirect(url_for("bookings.list_bookings"))

    refund_preview = calculate_cancellation_refund(booking)

    if request.method == "POST":
        refund_info = cancel_booking(booking_id)
        increment_seats(str(booking["flight_id"]), booking["seat_count"])
        flash(
            f"Booking cancelled successfully. Refund of ₹{refund_info['refund_amount']:,.0f} ({refund_info['refund_percentage']}% refund) has been credited.",
            "success",
        )
        return redirect(url_for("bookings.list_bookings"))

    return render_template(
        "bookings/cancel_confirm.html",
        booking=booking,
        refund=refund_preview
    )

