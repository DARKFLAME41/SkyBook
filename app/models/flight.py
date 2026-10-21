from bson import ObjectId
from datetime import datetime
from .. import mongo


def format_flight_doc(doc):
    """
    Ensures backwards compatibility and convenient access for both
    top-level and embedded document fields.
    """
    if not doc:
        return doc

    # Embedded document structures with defaults
    airline = doc.get("airline", {})
    if isinstance(airline, str):
        airline = {"name": airline, "code": "", "logo_url": ""}

    route = doc.get("route", {})
    origin_info = route.get("origin", {}) if isinstance(route, dict) else {}
    dest_info = route.get("destination", {}) if isinstance(route, dict) else {}

    schedule = doc.get("schedule", {}) if isinstance(doc.get("schedule"), dict) else {}
    aircraft = doc.get("aircraft", {}) if isinstance(doc.get("aircraft"), dict) else {}
    pricing = doc.get("pricing", {}) if isinstance(doc.get("pricing"), dict) else {}
    seat_info = doc.get("seat_info", {}) if isinstance(doc.get("seat_info"), dict) else {}

    # Populate top-level fields from embedded docs if missing
    doc["airline_name"] = airline.get("name", doc.get("airline", ""))
    doc["airline_code"] = airline.get("code", "")
    doc["airline_logo"] = airline.get("logo_url", "")

    doc["origin_city"] = origin_info.get("city", doc.get("origin", ""))
    doc["origin_code"] = origin_info.get("code", "")
    doc["origin_airport"] = origin_info.get("airport", "")

    doc["destination_city"] = dest_info.get("city", doc.get("destination", ""))
    doc["destination_code"] = dest_info.get("code", "")
    doc["destination_airport"] = dest_info.get("airport", "")

    doc["dep_date"] = schedule.get("departure_date", doc.get("departure_date", ""))
    doc["dep_time"] = schedule.get("departure_time", doc.get("departure_time", ""))
    doc["arr_time"] = schedule.get("arrival_time", doc.get("arrival_time", ""))
    doc["duration"] = schedule.get("duration", "2h 00m")

    doc["price_val"] = pricing.get("base_price", doc.get("price", 0.0))
    doc["price"] = doc["price_val"]

    doc["seats_avail"] = seat_info.get("available_seats", doc.get("seats_available", 0))
    doc["seats_tot"] = seat_info.get("total_seats", doc.get("seats_total", 0))
    doc["flight_class"] = seat_info.get("class", doc.get("class", "Economy"))

    # Photos embedded array
    photos = doc.get("photos", [])
    if not photos and doc.get("photo_url"):
        photos = [{"url": doc.get("photo_url"), "caption": "Flight Photo", "is_primary": True}]
        doc["photos"] = photos

    primary_photo = None
    for p in photos:
        if isinstance(p, dict) and p.get("is_primary"):
            primary_photo = p.get("url")
            break
    if not primary_photo and photos:
        primary_photo = photos[0].get("url") if isinstance(photos[0], dict) else photos[0]
    
    doc["primary_photo"] = primary_photo or "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80"

    return doc


def get_all_flights(status="active"):
    query = {}
    if status:
        query["status"] = status
    docs = list(mongo.db.flights.find(query))
    return [format_flight_doc(d) for d in docs]


def search_flights(origin="", destination="", date="", flight_class=None, max_price=None):
    """
    Demonstrates MongoDB Embedded Document Querying using dot notation.
    Queries embedded fields: route.origin.city, route.destination.city,
    schedule.departure_date, seat_info.available_seats, pricing.base_price.
    """
    query = {"status": "active"}

    # Embedded document queries using dot notation
    conditions = []
    
    if origin:
        conditions.append({
            "$or": [
                {"route.origin.city": {"$regex": origin, "$options": "i"}},
                {"route.origin.code": {"$regex": origin, "$options": "i"}},
                {"route.origin.airport": {"$regex": origin, "$options": "i"}},
                {"origin": {"$regex": origin, "$options": "i"}},
            ]
        })

    if destination:
        conditions.append({
            "$or": [
                {"route.destination.city": {"$regex": destination, "$options": "i"}},
                {"route.destination.code": {"$regex": destination, "$options": "i"}},
                {"route.destination.airport": {"$regex": destination, "$options": "i"}},
                {"destination": {"$regex": destination, "$options": "i"}},
            ]
        })

    if date:
        conditions.append({
            "$or": [
                {"schedule.departure_date": date},
                {"departure_date": date},
            ]
        })

    if flight_class:
        conditions.append({
            "$or": [
                {"seat_info.class": flight_class},
                {"class": flight_class},
            ]
        })

    if max_price:
        try:
            val = float(max_price)
            conditions.append({
                "$or": [
                    {"pricing.base_price": {"$lte": val}},
                    {"price": {"$lte": val}},
                ]
            })
        except ValueError:
            pass

    # Ensure available seats > 0 (checking both embedded and top-level fields)
    conditions.append({
        "$or": [
            {"seat_info.available_seats": {"$gt": 0}},
            {"seats_available": {"$gt": 0}},
        ]
    })

    if conditions:
        query["$and"] = conditions

    docs = list(mongo.db.flights.find(query))
    return [format_flight_doc(d) for d in docs]


def get_flight_by_id(flight_id):
    try:
        doc = mongo.db.flights.find_one({"_id": ObjectId(flight_id)})
        return format_flight_doc(doc)
    except Exception:
        return None


def create_flight(data):
    """
    Inserts a flight document structured with embedded subdocuments.
    """
    # Build embedded document structure
    embedded_doc = {
        "flight_number": data.get("flight_number", "").upper(),
        "airline": {
            "name": data.get("airline", ""),
            "code": data.get("airline_code", data.get("flight_number", "")[:2]),
            "logo_url": data.get("airline_logo", ""),
        },
        "route": {
            "origin": {
                "city": data.get("origin", ""),
                "code": data.get("origin_code", data.get("origin", "")[:3].upper()),
                "airport": data.get("origin_airport", f"{data.get('origin', '')} Airport"),
            },
            "destination": {
                "city": data.get("destination", ""),
                "code": data.get("destination_code", data.get("destination", "")[:3].upper()),
                "airport": data.get("destination_airport", f"{data.get('destination', '')} Airport"),
            },
        },
        "schedule": {
            "departure_date": data.get("departure_date", ""),
            "departure_time": data.get("departure_time", ""),
            "arrival_time": data.get("arrival_time", ""),
            "duration": data.get("duration", "2h 15m"),
        },
        "aircraft": {
            "model": data.get("aircraft_model", "Boeing 737-800"),
            "registration": data.get("aircraft_reg", "VT-SKY"),
            "manufacturer": data.get("aircraft_mfr", "Boeing"),
        },
        "pricing": {
            "base_price": float(data.get("price", 0)),
            "currency": "INR",
            "tax": float(data.get("price", 0)) * 0.12,
            "total_price": float(data.get("price", 0)) * 1.12,
        },
        "seat_info": {
            "class": data.get("class", "Economy"),
            "total_seats": int(data.get("seats_total", 100)),
            "available_seats": int(data.get("seats_total", 100)),
        },
        "photos": data.get("photos", []),
        "amenities": data.get("amenities", ["In-flight Meals", "Reclining Seats", "USB Charging"]),
        "status": data.get("status", "active"),
        "created_at": datetime.utcnow(),

        # Top-level backwards compatibility fields
        "airline": data.get("airline", ""),
        "origin": data.get("origin", ""),
        "destination": data.get("destination", ""),
        "departure_date": data.get("departure_date", ""),
        "departure_time": data.get("departure_time", ""),
        "arrival_time": data.get("arrival_time", ""),
        "seats_total": int(data.get("seats_total", 100)),
        "seats_available": int(data.get("seats_total", 100)),
        "price": float(data.get("price", 0)),
        "class": data.get("class", "Economy"),
    }

    # Add primary photo if provided
    if data.get("photo_url"):
        embedded_doc["photos"].append({
            "url": data.get("photo_url"),
            "caption": "Main Flight Image",
            "is_primary": True,
            "uploaded_at": datetime.utcnow(),
        })

    result = mongo.db.flights.insert_one(embedded_doc)
    return result.inserted_id


def add_photo_to_flight(flight_id, photo_url, caption="Flight Photo", is_primary=False):
    """
    Appends an embedded photo subdocument to the flight's 'photos' array using $push.
    """
    photo_doc = {
        "url": photo_url,
        "caption": caption,
        "is_primary": is_primary,
        "uploaded_at": datetime.utcnow()
    }
    
    if is_primary:
        # Reset primary flag on existing photos
        mongo.db.flights.update_one(
            {"_id": ObjectId(flight_id)},
            {"$set": {"photos.$[].is_primary": False}}
        )

    mongo.db.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {"$push": {"photos": photo_doc}}
    )


def remove_photo_from_flight(flight_id, photo_url):
    """
    Removes an embedded photo document from the 'photos' array using $pull.
    """
    mongo.db.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {"$pull": {"photos": {"url": photo_url}}}
    )


def update_flight(flight_id, data):
    """
    Updates top-level and embedded fields.
    """
    update_doc = {"$set": {}}
    for k, v in data.items():
        update_doc["$set"][k] = v
        
    if "seats_available" in data:
        update_doc["$set"]["seat_info.available_seats"] = data["seats_available"]
    if "price" in data:
        update_doc["$set"]["pricing.base_price"] = data["price"]

    mongo.db.flights.update_one({"_id": ObjectId(flight_id)}, update_doc)


def decrement_seats(flight_id, count):
    """
    Atomically updates nested embedded document field 'seat_info.available_seats'
    and top-level 'seats_available' using $inc.
    """
    mongo.db.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {
            "$inc": {
                "seat_info.available_seats": -count,
                "seats_available": -count,
            }
        },
    )


def increment_seats(flight_id, count):
    """
    Atomically increases available seats in embedded and top-level fields.
    """
    mongo.db.flights.update_one(
        {"_id": ObjectId(flight_id)},
        {
            "$inc": {
                "seat_info.available_seats": count,
                "seats_available": count,
            }
        },
    )


def delete_flight(flight_id):
    mongo.db.flights.update_one(
        {"_id": ObjectId(flight_id)}, {"$set": {"status": "inactive"}}
    )


def get_featured_flights():
    """
    MongoDB Aggregation Pipeline querying embedded documents ($match, $project, $limit)
    """
    pipeline = [
        {"$match": {"status": "active"}},
        {
            "$project": {
                "flight_number": 1,
                "airline": 1,
                "route": 1,
                "schedule": 1,
                "pricing": 1,
                "seat_info": 1,
                "photos": 1,
                "status": 1,
                "origin": 1,
                "destination": 1,
                "departure_date": 1,
                "departure_time": 1,
                "arrival_time": 1,
                "price": 1,
                "seats_available": 1,
                "seats_total": 1,
                "class": 1,
            }
        },
        {"$limit": 6}
    ]
    docs = list(mongo.db.flights.aggregate(pipeline))
    return [format_flight_doc(d) for d in docs]
