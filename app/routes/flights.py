from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from ..models.flight import get_all_flights, search_flights, get_flight_by_id, get_featured_flights

flights_bp = Blueprint("flights", __name__, url_prefix="/flights")


@flights_bp.route("/search")
def search():
    origin = request.args.get("origin", "").strip()
    destination = request.args.get("destination", "").strip()
    date = request.args.get("date", "").strip()
    flight_class = request.args.get("flight_class", "").strip()
    max_price = request.args.get("max_price", "").strip()

    flights = []
    searched = False

    if origin or destination or date or flight_class or max_price:
        searched = True
        flights = search_flights(
            origin=origin,
            destination=destination,
            date=date,
            flight_class=flight_class if flight_class else None,
            max_price=max_price if max_price else None,
        )
        if not flights:
            flash("No flights found for the given search criteria.", "info")
    else:
        # Show all active flights by default if user navigates to search page
        flights = get_all_flights(status="active")

    return render_template(
        "flights/search.html",
        flights=flights,
        searched=searched,
        origin=origin,
        destination=destination,
        date=date,
        flight_class=flight_class,
        max_price=max_price,
    )


@flights_bp.route("/<flight_id>")
def detail(flight_id):
    flight = get_flight_by_id(flight_id)
    if not flight:
        flash("Flight not found.", "danger")
        return redirect(url_for("flights.search"))
    return render_template("flights/detail.html", flight=flight)
