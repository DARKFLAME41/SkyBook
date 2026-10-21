from datetime import datetime
from bson import ObjectId
from .. import mongo
from .flight import get_flight_by_id


def create_booking(user_id, flight_id, passenger_details, seat_count, total_price):
    flight = get_flight_by_id(flight_id)
    
    # Embedded document snapshot for flight metadata to preserve booking history
    flight_snapshot = {
        "flight_number": flight.get("flight_number", ""),
        "airline_name": flight.get("airline_name", flight.get("airline", "")),
        "airline_logo": flight.get("airline_logo", ""),
        "origin_city": flight.get("origin_city", flight.get("origin", "")),
        "origin_code": flight.get("origin_code", ""),
        "destination_city": flight.get("destination_city", flight.get("destination", "")),
        "destination_code": flight.get("destination_code", ""),
        "departure_date": flight.get("dep_date", flight.get("departure_date", "")),
        "departure_time": flight.get("dep_time", flight.get("departure_time", "")),
        "arrival_time": flight.get("arr_time", flight.get("arrival_time", "")),
        "flight_class": flight.get("flight_class", flight.get("class", "Economy")),
        "primary_photo": flight.get("primary_photo", ""),
    }

    # Embedded payment document
    payment_info = {
        "unit_price": total_price / max(seat_count, 1),
        "seat_count": seat_count,
        "total_price": total_price,
        "currency": "INR",
        "payment_status": "completed",
        "payment_method": "UPI / Card Online",
        "transaction_id": f"TXN-{int(datetime.utcnow().timestamp())}",
    }

    booking = {
        "user_id": ObjectId(user_id),
        "flight_id": ObjectId(flight_id),
        "flight_snapshot": flight_snapshot,
        "passengers": passenger_details,  # Array of embedded passenger objects
        "payment": payment_info,          # Embedded payment object
        "seat_count": seat_count,
        "total_price": total_price,
        "status": "confirmed",
        "booked_at": datetime.utcnow(),
    }
    result = mongo.db.bookings.insert_one(booking)
    return result.inserted_id


def get_bookings_by_user(user_id):
    """
    Query user bookings using Mongo aggregation pipeline.
    Combines embedded flight snapshot with looked-up flight details if needed.
    """
    pipeline = [
        {"$match": {"user_id": ObjectId(user_id)}},
        {
            "$lookup": {
                "from": "flights",
                "localField": "flight_id",
                "foreignField": "_id",
                "as": "flight_lookup",
            }
        },
        {"$sort": {"booked_at": -1}},
    ]
    results = list(mongo.db.bookings.aggregate(pipeline))
    for b in results:
        if "flight_lookup" in b and b["flight_lookup"]:
            from .flight import format_flight_doc
            b["flight"] = format_flight_doc(b["flight_lookup"][0])
        else:
            # Fallback to embedded snapshot
            b["flight"] = b.get("flight_snapshot", {})
    return results


def get_booking_by_id(booking_id):
    try:
        pipeline = [
            {"$match": {"_id": ObjectId(booking_id)}},
            {
                "$lookup": {
                    "from": "flights",
                    "localField": "flight_id",
                    "foreignField": "_id",
                    "as": "flight_lookup",
                }
            },
        ]
        results = list(mongo.db.bookings.aggregate(pipeline))
        if not results:
            return None
        b = results[0]
        if "flight_lookup" in b and b["flight_lookup"]:
            from .flight import format_flight_doc
            b["flight"] = format_flight_doc(b["flight_lookup"][0])
        else:
            b["flight"] = b.get("flight_snapshot", {})
        return b
    except Exception:
        return None


def get_all_bookings():
    pipeline = [
        {
            "$lookup": {
                "from": "flights",
                "localField": "flight_id",
                "foreignField": "_id",
                "as": "flight_lookup",
            }
        },
        {
            "$lookup": {
                "from": "users",
                "localField": "user_id",
                "foreignField": "_id",
                "as": "user_lookup",
            }
        },
        {"$sort": {"booked_at": -1}},
    ]
    results = list(mongo.db.bookings.aggregate(pipeline))
    for b in results:
        if "flight_lookup" in b and b["flight_lookup"]:
            from .flight import format_flight_doc
            b["flight"] = format_flight_doc(b["flight_lookup"][0])
        else:
            b["flight"] = b.get("flight_snapshot", {})

        if "user_lookup" in b and b["user_lookup"]:
            b["user"] = b["user_lookup"][0]
        else:
            b["user"] = {"name": "Passenger", "email": "n/a"}
    return results


def calculate_cancellation_refund(booking):
    """
    Calculate refund based on policy:
    - Cancelled within 3 hours of booking -> 100% full refund
    - Cancelled after 3 hours of booking -> 50% half refund
    """
    booked_at = booking.get("booked_at")
    total_price = float(booking.get("total_price", 0.0))
    
    if not booked_at:
        return {
            "hours_elapsed": 0.0,
            "refund_percentage": 100,
            "refund_amount": total_price,
            "deduction_amount": 0.0,
            "policy_applied": "Full Refund (within 3 hours of booking)"
        }
    
    if isinstance(booked_at, str):
        try:
            booked_at = datetime.fromisoformat(booked_at)
        except Exception:
            booked_at = datetime.utcnow()
            
    now = datetime.utcnow()
    diff_seconds = max((now - booked_at).total_seconds(), 0)
    hours_elapsed = diff_seconds / 3600.0

    if hours_elapsed <= 3.0:
        refund_pct = 100
        refund_amount = total_price
        deduction = 0.0
        policy = "Full Refund (within 3 hours)"
    else:
        refund_pct = 50
        refund_amount = total_price * 0.5
        deduction = total_price * 0.5
        policy = "50% Half Refund (after 3 hours)"

    return {
        "hours_elapsed": round(hours_elapsed, 2),
        "refund_percentage": refund_pct,
        "refund_amount": refund_amount,
        "deduction_amount": deduction,
        "policy_applied": policy
    }


def cancel_booking(booking_id):
    booking = mongo.db.bookings.find_one({"_id": ObjectId(booking_id)})
    if not booking:
        return None

    refund_info = calculate_cancellation_refund(booking)
    now = datetime.utcnow()

    mongo.db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {
            "$set": {
                "status": "cancelled",
                "cancelled_at": now,
                "refund_amount": refund_info["refund_amount"],
                "refund_percentage": refund_info["refund_percentage"],
                "deduction_amount": refund_info["deduction_amount"],
                "cancellation_policy": refund_info["policy_applied"],
                "refund_status": "Processed",
            }
        },
    )
    return refund_info

