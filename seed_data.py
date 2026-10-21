from app import create_app, mongo, bcrypt
from datetime import datetime

app = create_app()

def make_flight(
    flight_number, airline_name, airline_code,
    origin_city, origin_code, origin_airport,
    dest_city, dest_code, dest_airport,
    dep_date, dep_time, arr_time, duration,
    aircraft_model, aircraft_reg, manufacturer,
    base_price, tax,
    seat_class, total_seats,
    photos, amenities,
):
    total_price = base_price + tax
    return {
        "flight_number": flight_number,
        "airline": {
            "name": airline_name,
            "code": airline_code,
            "logo_url": photos[0]["url"] if photos else "",
        },
        "route": {
            "origin": {
                "city": origin_city,
                "code": origin_code,
                "airport": origin_airport,
            },
            "destination": {
                "city": dest_city,
                "code": dest_code,
                "airport": dest_airport,
            },
        },
        "schedule": {
            "departure_date": dep_date,
            "departure_time": dep_time,
            "arrival_time": arr_time,
            "duration": duration,
        },
        "aircraft": {
            "model": aircraft_model,
            "registration": aircraft_reg,
            "manufacturer": manufacturer,
        },
        "pricing": {
            "base_price": base_price,
            "currency": "INR",
            "tax": tax,
            "total_price": total_price,
        },
        "seat_info": {
            "class": seat_class,
            "total_seats": total_seats,
            "available_seats": total_seats,
        },
        "photos": photos,
        "amenities": amenities,
        "status": "active",
        # backward-compat flat fields
        "origin": origin_city,
        "destination": dest_city,
        "departure_date": dep_date,
        "departure_time": dep_time,
        "arrival_time": arr_time,
        "seats_total": total_seats,
        "seats_available": total_seats,
        "price": base_price,
        "class": seat_class,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Photo sets per airline
# ─────────────────────────────────────────────────────────────────────────────
PHOTOS = {
    "AI": [
        {"url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80", "caption": "Air India Boeing 787 Dreamliner", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1512100356356-de1b84283e18?auto=format&fit=crop&w=1200&q=80", "caption": "Spacious Economy Cabin", "is_primary": False},
        {"url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1200&q=80", "caption": "In-flight Meal Service", "is_primary": False},
    ],
    "6E": [
        {"url": "https://images.unsplash.com/photo-1556388158-158ea5ccacbd?auto=format&fit=crop&w=1200&q=80", "caption": "IndiGo A320neo Ready for Takeoff", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1508672019048-805479767746?auto=format&fit=crop&w=1200&q=80", "caption": "Clean Airbus Cabin", "is_primary": False},
    ],
    "UK": [
        {"url": "https://images.unsplash.com/photo-1569154941061-e231b4725ef1?auto=format&fit=crop&w=1200&q=80", "caption": "Vistara Luxury Aircraft", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1570710891158-d73111f18546?auto=format&fit=crop&w=1200&q=80", "caption": "Vistara Business Class Suite", "is_primary": False},
        {"url": "https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?auto=format&fit=crop&w=1200&q=80", "caption": "Gourmet Fine Dining", "is_primary": False},
    ],
    "SG": [
        {"url": "https://images.unsplash.com/photo-1524592094714-0f0654e20314?auto=format&fit=crop&w=1200&q=80", "caption": "SpiceJet Boeing 737", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1517649763962-0c623266010b?auto=format&fit=crop&w=1200&q=80", "caption": "SpiceMax Legroom Seats", "is_primary": False},
    ],
    "QP": [
        {"url": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?auto=format&fit=crop&w=1200&q=80", "caption": "Akasa Air Brand New Jet", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80", "caption": "Eco-Friendly Engine", "is_primary": False},
    ],
    "IX": [
        {"url": "https://images.unsplash.com/photo-1464037866556-6812c9d1c72e?auto=format&fit=crop&w=1200&q=80", "caption": "Air India Express Flight", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1494783367193-149034c05e8f?auto=format&fit=crop&w=1200&q=80", "caption": "Express Economy Cabin", "is_primary": False},
    ],
    "GO": [
        {"url": "https://images.unsplash.com/photo-1474302770737-173ee21bab63?auto=format&fit=crop&w=1200&q=80", "caption": "Go First Aircraft", "is_primary": True},
        {"url": "https://images.unsplash.com/photo-1485738422979-f5c462d49f74?auto=format&fit=crop&w=1200&q=80", "caption": "Comfortable Economy Seats", "is_primary": False},
    ],
}

AMENITIES = {
    "economy_budget": ["Express Check-in", "USB Charging", "Reclining Seats"],
    "economy_mid": ["Hot Meals Included", "USB Charging", "Reclining Seats", "In-flight Entertainment"],
    "economy_premium": ["Wi-Fi Onboard", "Hot Meals Included", "Extra Legroom", "USB Power Ports", "In-flight Screen"],
    "business": ["Lie-flat Seats", "Multi-course Meals", "Lounge Access", "High-speed Wi-Fi", "Noise-cancelling Headsets", "Amenity Kit"],
}

# ─────────────────────────────────────────────────────────────────────────────
# All major Indian airport data
# ─────────────────────────────────────────────────────────────────────────────
AIRPORTS = {
    "Mumbai":     ("BOM", "Chhatrapati Shivaji Maharaj International Airport"),
    "Delhi":      ("DEL", "Indira Gandhi International Airport"),
    "Bangalore":  ("BLR", "Kempegowda International Airport"),
    "Chennai":    ("MAA", "Chennai International Airport"),
    "Kolkata":    ("CCU", "Netaji Subhash Chandra Bose International Airport"),
    "Hyderabad":  ("HYD", "Rajiv Gandhi International Airport"),
    "Pune":       ("PNQ", "Pune Airport"),
    "Ahmedabad":  ("AMD", "Sardar Vallabhbhai Patel International Airport"),
    "Goa":        ("GOI", "Goa International Airport"),
    "Jaipur":     ("JAI", "Jaipur International Airport"),
    "Kochi":      ("COK", "Cochin International Airport"),
    "Lucknow":    ("LKO", "Chaudhary Charan Singh International Airport"),
    "Chandigarh": ("IXC", "Chandigarh Airport"),
    "Nagpur":     ("NAG", "Dr. Babasaheb Ambedkar International Airport"),
    "Bhubaneswar":("BBI", "Biju Patnaik International Airport"),
    "Varanasi":   ("VNS", "Lal Bahadur Shastri Airport"),
    "Amritsar":   ("ATQ", "Sri Guru Ram Dass Jee International Airport"),
    "Srinagar":   ("SXR", "Sheikh ul-Alam International Airport"),
    "Coimbatore": ("CJB", "Coimbatore International Airport"),
    "Visakhapatnam": ("VTZ", "Visakhapatnam Airport"),
}

# ─────────────────────────────────────────────────────────────────────────────
# Build flights list
# ─────────────────────────────────────────────────────────────────────────────
FLIGHTS = [

    # ── MUMBAI routes ──────────────────────────────────────────────────
    make_flight("AI-101", "Air India", "AI",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-10", "06:00", "08:15", "2h 15m",
        "Boeing 787-8 Dreamliner", "VT-ANP", "Boeing",
        3499, 420, "Economy", 180, PHOTOS["AI"], AMENITIES["economy_premium"]),

    make_flight("6E-201", "IndiGo", "6E",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-10", "09:00", "11:20", "2h 20m",
        "Airbus A320neo", "VT-IZA", "Airbus",
        2899, 350, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),

    make_flight("UK-501", "Vistara", "UK",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-11", "07:30", "09:45", "2h 15m",
        "Airbus A321neo", "VT-TVB", "Airbus",
        5499, 660, "Business", 160, PHOTOS["UK"], AMENITIES["business"]),

    make_flight("SG-401", "SpiceJet", "SG",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-11", "14:00", "16:15", "2h 15m",
        "Boeing 737 MAX 8", "VT-MAX", "Boeing",
        2499, 300, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    make_flight("AI-201", "Air India", "AI",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-12", "07:00", "08:45", "1h 45m",
        "Airbus A320", "VT-PPD", "Airbus",
        3199, 380, "Economy", 168, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("6E-301", "IndiGo", "6E",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-13", "06:30", "08:40", "2h 10m",
        "Airbus A320neo", "VT-IZB", "Airbus",
        2799, 340, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),

    make_flight("UK-601", "Vistara", "UK",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "2026-11-12", "07:45", "10:30", "2h 45m",
        "Airbus A321neo", "VT-TVA", "Airbus",
        5499, 650, "Business", 160, PHOTOS["UK"], AMENITIES["business"]),

    make_flight("QP-101", "Akasa Air", "QP",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Goa", "GOI", AIRPORTS["Goa"][1],
        "2026-11-14", "08:00", "09:10", "1h 10m",
        "Boeing 737 MAX 200", "VT-YAA", "Boeing",
        1899, 230, "Economy", 170, PHOTOS["QP"], AMENITIES["economy_budget"]),

    make_flight("SG-501", "SpiceJet", "SG",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Ahmedabad", "AMD", AIRPORTS["Ahmedabad"][1],
        "2026-11-15", "10:00", "11:05", "1h 05m",
        "Boeing 737-800", "VT-SGX", "Boeing",
        1499, 180, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    make_flight("AI-301", "Air India", "AI",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-15", "11:30", "13:10", "1h 40m",
        "Boeing 737-800", "VT-ANR", "Boeing",
        2699, 325, "Economy", 162, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("6E-901", "IndiGo", "6E",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Jaipur", "JAI", AIRPORTS["Jaipur"][1],
        "2026-11-16", "07:15", "09:00", "1h 45m",
        "Airbus A320", "VT-IZC", "Airbus",
        2199, 265, "Economy", 180, PHOTOS["6E"], AMENITIES["economy_budget"]),

    make_flight("UK-701", "Vistara", "UK",
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "Lucknow", "LKO", AIRPORTS["Lucknow"][1],
        "2026-11-17", "08:00", "10:15", "2h 15m",
        "Airbus A320neo", "VT-TVC", "Airbus",
        4299, 515, "Economy", 168, PHOTOS["UK"], AMENITIES["economy_premium"]),

    # ── DELHI routes ───────────────────────────────────────────────────
    make_flight("6E-202", "IndiGo", "6E",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-10", "09:30", "12:00", "2h 30m",
        "Airbus A320neo", "VT-IZI", "Airbus",
        4199, 500, "Economy", 200, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-401", "Air India", "AI",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-11", "06:15", "08:45", "2h 30m",
        "Boeing 787-8", "VT-ANQ", "Boeing",
        4499, 540, "Economy", 180, PHOTOS["AI"], AMENITIES["economy_premium"]),

    make_flight("UK-801", "Vistara", "UK",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-12", "10:00", "12:35", "2h 35m",
        "Airbus A321neo", "VT-TVD", "Airbus",
        6499, 780, "Business", 156, PHOTOS["UK"], AMENITIES["business"]),

    make_flight("SG-601", "SpiceJet", "SG",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-10", "07:00", "09:15", "2h 15m",
        "Boeing 737 MAX 8", "VT-SGY", "Boeing",
        2599, 312, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    make_flight("6E-601", "IndiGo", "6E",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-13", "11:00", "13:45", "2h 45m",
        "Airbus A320neo", "VT-IZD", "Airbus",
        3999, 480, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-501", "Air India", "AI",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "2026-11-14", "08:30", "10:50", "2h 20m",
        "Airbus A320", "VT-ANA", "Airbus",
        3299, 396, "Economy", 168, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("QP-201", "Akasa Air", "QP",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-15", "09:00", "11:15", "2h 15m",
        "Boeing 737 MAX 200", "VT-YAB", "Boeing",
        2899, 348, "Economy", 170, PHOTOS["QP"], AMENITIES["economy_budget"]),

    make_flight("6E-701", "IndiGo", "6E",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Goa", "GOI", AIRPORTS["Goa"][1],
        "2026-11-16", "06:45", "09:00", "2h 15m",
        "Airbus A320", "VT-IZE", "Airbus",
        3499, 420, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-601", "Air India", "AI",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Amritsar", "ATQ", AIRPORTS["Amritsar"][1],
        "2026-11-17", "07:30", "08:30", "1h 00m",
        "ATR 72-600", "VT-ATR", "ATR",
        1999, 240, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_budget"]),

    make_flight("UK-901", "Vistara", "UK",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Srinagar", "SXR", AIRPORTS["Srinagar"][1],
        "2026-11-18", "08:00", "09:15", "1h 15m",
        "Airbus A320", "VT-TVE", "Airbus",
        3799, 456, "Economy", 168, PHOTOS["UK"], AMENITIES["economy_premium"]),

    make_flight("6E-801", "IndiGo", "6E",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Jaipur", "JAI", AIRPORTS["Jaipur"][1],
        "2026-11-19", "09:30", "10:30", "1h 00m",
        "Airbus A320", "VT-IZF", "Airbus",
        1299, 156, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),

    make_flight("SG-701", "SpiceJet", "SG",
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "Chandigarh", "IXC", AIRPORTS["Chandigarh"][1],
        "2026-11-20", "07:00", "07:55", "0h 55m",
        "Bombardier Q400", "VT-SQA", "Bombardier",
        1199, 145, "Economy", 78, PHOTOS["SG"], AMENITIES["economy_budget"]),

    # ── BANGALORE routes ───────────────────────────────────────────────
    make_flight("SG-303", "SpiceJet", "SG",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-11", "13:00", "14:10", "1h 10m",
        "Boeing 737 MAX 8", "VT-MAX", "Boeing",
        2199, 265, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    make_flight("6E-402", "IndiGo", "6E",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-12", "10:30", "11:35", "1h 05m",
        "Airbus A320neo", "VT-IZG", "Airbus",
        1899, 228, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),

    make_flight("AI-701", "Air India", "AI",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-13", "08:00", "09:45", "1h 45m",
        "Boeing 737-800", "VT-ANS", "Boeing",
        3099, 372, "Economy", 162, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("UK-1001", "Vistara", "UK",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-14", "06:30", "09:10", "2h 40m",
        "Airbus A321neo", "VT-TVF", "Airbus",
        6199, 744, "Business", 156, PHOTOS["UK"], AMENITIES["business"]),

    make_flight("6E-1001", "IndiGo", "6E",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "2026-11-15", "09:00", "11:40", "2h 40m",
        "Airbus A320neo", "VT-IZH", "Airbus",
        3799, 456, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("QP-301", "Akasa Air", "QP",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Goa", "GOI", AIRPORTS["Goa"][1],
        "2026-11-16", "07:00", "08:05", "1h 05m",
        "Boeing 737 MAX 200", "VT-YAC", "Boeing",
        1799, 216, "Economy", 170, PHOTOS["QP"], AMENITIES["economy_budget"]),

    make_flight("AI-801", "Air India", "AI",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Kochi", "COK", AIRPORTS["Kochi"][1],
        "2026-11-17", "10:00", "11:10", "1h 10m",
        "ATR 72-600", "VT-ATB", "ATR",
        2299, 276, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_budget"]),

    make_flight("6E-1101", "IndiGo", "6E",
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "Coimbatore", "CJB", AIRPORTS["Coimbatore"][1],
        "2026-11-18", "08:30", "09:30", "1h 00m",
        "Airbus A320", "VT-IZJ", "Airbus",
        1599, 192, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),

    # ── CHENNAI routes ─────────────────────────────────────────────────
    make_flight("6E-502", "IndiGo", "6E",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-10", "07:30", "09:40", "2h 10m",
        "Airbus A320neo", "VT-IZK", "Airbus",
        2999, 360, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-901", "Air India", "AI",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-11", "06:00", "08:45", "2h 45m",
        "Boeing 787-8", "VT-ANT", "Boeing",
        4599, 552, "Economy", 180, PHOTOS["AI"], AMENITIES["economy_premium"]),

    make_flight("UK-1101", "Vistara", "UK",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-12", "11:30", "12:40", "1h 10m",
        "Airbus A320", "VT-TVG", "Airbus",
        2799, 336, "Economy", 168, PHOTOS["UK"], AMENITIES["economy_mid"]),

    make_flight("SG-801", "SpiceJet", "SG",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-13", "09:00", "10:15", "1h 15m",
        "Boeing 737-800", "VT-SGZ", "Boeing",
        1999, 240, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    make_flight("6E-1201", "IndiGo", "6E",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "2026-11-14", "10:00", "12:30", "2h 30m",
        "Airbus A320neo", "VT-IZL", "Airbus",
        3499, 420, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-1001", "Air India", "AI",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Kochi", "COK", AIRPORTS["Kochi"][1],
        "2026-11-15", "08:00", "09:00", "1h 00m",
        "ATR 72-600", "VT-ATC", "ATR",
        1799, 216, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_budget"]),

    make_flight("QP-401", "Akasa Air", "QP",
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "Coimbatore", "CJB", AIRPORTS["Coimbatore"][1],
        "2026-11-16", "07:30", "08:35", "1h 05m",
        "Boeing 737 MAX 200", "VT-YAD", "Boeing",
        1499, 180, "Economy", 170, PHOTOS["QP"], AMENITIES["economy_budget"]),

    # ── HYDERABAD routes ───────────────────────────────────────────────
    make_flight("QP-808", "Akasa Air", "QP",
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-12", "15:00", "17:00", "2h 00m",
        "Boeing 737 MAX 200", "VT-YAE", "Boeing",
        2799, 336, "Economy", 170, PHOTOS["QP"], AMENITIES["economy_budget"]),

    make_flight("6E-1301", "IndiGo", "6E",
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-13", "07:00", "09:15", "2h 15m",
        "Airbus A320neo", "VT-IZM", "Airbus",
        3299, 396, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-1101", "Air India", "AI",
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-14", "10:30", "11:35", "1h 05m",
        "Boeing 737-800", "VT-ANU", "Boeing",
        2199, 264, "Economy", 162, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("UK-1201", "Vistara", "UK",
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "2026-11-15", "08:00", "10:30", "2h 30m",
        "Airbus A321neo", "VT-TVH", "Airbus",
        5299, 636, "Business", 156, PHOTOS["UK"], AMENITIES["business"]),

    make_flight("SG-901", "SpiceJet", "SG",
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-16", "13:30", "14:45", "1h 15m",
        "Boeing 737 MAX 8", "VT-SGV", "Boeing",
        1999, 240, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    # ── KOLKATA routes ─────────────────────────────────────────────────
    make_flight("AI-1201", "Air India", "AI",
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-10", "06:30", "09:00", "2h 30m",
        "Boeing 787-8", "VT-ANV", "Boeing",
        3799, 456, "Economy", 180, PHOTOS["AI"], AMENITIES["economy_premium"]),

    make_flight("6E-1401", "IndiGo", "6E",
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-11", "07:45", "10:30", "2h 45m",
        "Airbus A320neo", "VT-IZN", "Airbus",
        3599, 432, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("UK-1301", "Vistara", "UK",
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-13", "09:00", "11:40", "2h 40m",
        "Airbus A321neo", "VT-TVI", "Airbus",
        5799, 696, "Business", 156, PHOTOS["UK"], AMENITIES["business"]),

    make_flight("QP-501", "Akasa Air", "QP",
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-14", "10:00", "12:30", "2h 30m",
        "Boeing 737 MAX 200", "VT-YAF", "Boeing",
        3299, 396, "Economy", 170, PHOTOS["QP"], AMENITIES["economy_mid"]),

    make_flight("SG-1001", "SpiceJet", "SG",
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-15", "07:00", "09:30", "2h 30m",
        "Boeing 737-800", "VT-SGW", "Boeing",
        2899, 348, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    make_flight("AI-1301", "Air India", "AI",
        "Kolkata", "CCU", AIRPORTS["Kolkata"][1],
        "Bhubaneswar", "BBI", AIRPORTS["Bhubaneswar"][1],
        "2026-11-16", "09:00", "10:00", "1h 00m",
        "ATR 72-600", "VT-ATD", "ATR",
        1699, 204, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_budget"]),

    # ── GOA routes ─────────────────────────────────────────────────────
    make_flight("6E-1501", "IndiGo", "6E",
        "Goa", "GOI", AIRPORTS["Goa"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-17", "10:00", "11:10", "1h 10m",
        "Airbus A320neo", "VT-IZO", "Airbus",
        1999, 240, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),

    make_flight("AI-1401", "Air India", "AI",
        "Goa", "GOI", AIRPORTS["Goa"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-18", "09:30", "12:00", "2h 30m",
        "Boeing 737-800", "VT-ANW", "Boeing",
        3499, 420, "Economy", 162, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("UK-1401", "Vistara", "UK",
        "Goa", "GOI", AIRPORTS["Goa"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-19", "11:00", "12:05", "1h 05m",
        "Airbus A320", "VT-TVJ", "Airbus",
        2999, 360, "Economy", 168, PHOTOS["UK"], AMENITIES["economy_premium"]),

    # ── KOCHI routes ────────────────────────────────────────────────────
    make_flight("6E-1601", "IndiGo", "6E",
        "Kochi", "COK", AIRPORTS["Kochi"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-20", "08:00", "10:00", "2h 00m",
        "Airbus A320neo", "VT-IZP", "Airbus",
        2699, 324, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-1501", "Air India", "AI",
        "Kochi", "COK", AIRPORTS["Kochi"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-20", "06:30", "09:30", "3h 00m",
        "Boeing 787-8", "VT-ANX", "Boeing",
        4799, 576, "Economy", 180, PHOTOS["AI"], AMENITIES["economy_premium"]),

    make_flight("SG-1101", "SpiceJet", "SG",
        "Kochi", "COK", AIRPORTS["Kochi"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-21", "11:00", "12:00", "1h 00m",
        "Boeing 737-800", "VT-SGU", "Boeing",
        1799, 216, "Economy", 150, PHOTOS["SG"], AMENITIES["economy_budget"]),

    # ── PUNE routes ─────────────────────────────────────────────────────
    make_flight("6E-1701", "IndiGo", "6E",
        "Pune", "PNQ", AIRPORTS["Pune"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-18", "06:00", "08:15", "2h 15m",
        "Airbus A320neo", "VT-IZQ", "Airbus",
        2999, 360, "Economy", 180, PHOTOS["6E"], AMENITIES["economy_mid"]),

    make_flight("AI-1601", "Air India", "AI",
        "Pune", "PNQ", AIRPORTS["Pune"][1],
        "Bangalore", "BLR", AIRPORTS["Bangalore"][1],
        "2026-11-19", "07:30", "09:10", "1h 40m",
        "ATR 72-600", "VT-ATE", "ATR",
        2299, 276, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("UK-1501", "Vistara", "UK",
        "Pune", "PNQ", AIRPORTS["Pune"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-20", "09:00", "10:30", "1h 30m",
        "Airbus A320", "VT-TVK", "Airbus",
        3299, 396, "Economy", 168, PHOTOS["UK"], AMENITIES["economy_premium"]),

    # ── VARANASI routes ─────────────────────────────────────────────────
    make_flight("AI-1701", "Air India", "AI",
        "Varanasi", "VNS", AIRPORTS["Varanasi"][1],
        "Delhi", "DEL", AIRPORTS["Delhi"][1],
        "2026-11-20", "06:00", "07:30", "1h 30m",
        "ATR 72-600", "VT-ATF", "ATR",
        2199, 264, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_mid"]),

    make_flight("6E-1801", "IndiGo", "6E",
        "Varanasi", "VNS", AIRPORTS["Varanasi"][1],
        "Mumbai", "BOM", AIRPORTS["Mumbai"][1],
        "2026-11-21", "07:30", "10:00", "2h 30m",
        "Airbus A320", "VT-IZR", "Airbus",
        3299, 396, "Economy", 168, PHOTOS["6E"], AMENITIES["economy_mid"]),

    # ── VISAKHAPATNAM routes ────────────────────────────────────────────
    make_flight("AI-1801", "Air India", "AI",
        "Visakhapatnam", "VTZ", AIRPORTS["Visakhapatnam"][1],
        "Hyderabad", "HYD", AIRPORTS["Hyderabad"][1],
        "2026-11-21", "08:00", "09:15", "1h 15m",
        "ATR 72-600", "VT-ATG", "ATR",
        1899, 228, "Economy", 70, PHOTOS["AI"], AMENITIES["economy_budget"]),

    make_flight("6E-1901", "IndiGo", "6E",
        "Visakhapatnam", "VTZ", AIRPORTS["Visakhapatnam"][1],
        "Chennai", "MAA", AIRPORTS["Chennai"][1],
        "2026-11-22", "10:00", "11:30", "1h 30m",
        "Airbus A320neo", "VT-IZS", "Airbus",
        2199, 264, "Economy", 186, PHOTOS["6E"], AMENITIES["economy_budget"]),
]


def seed():
    with app.app_context():
        print("Connecting to MongoDB Atlas...")

        # Clear existing flights and admin
        mongo.db.flights.delete_many({})
        mongo.db.users.delete_many({"role": "admin"})

        # Insert all flights
        mongo.db.flights.insert_many(FLIGHTS)
        print(f"[OK] Inserted {len(FLIGHTS)} flights across all major Indian routes.")

        # Create admin
        existing = mongo.db.users.find_one({"email": "admin@flights.com"})
        if not existing:
            hashed = bcrypt.generate_password_hash("admin123").decode("utf-8")
            mongo.db.users.insert_one({
                "name": "Admin",
                "email": "admin@flights.com",
                "password": hashed,
                "role": "admin",
                "created_at": datetime.utcnow(),
            })
            print("[OK] Admin user created: admin@flights.com / admin123")
        else:
            print("[INFO] Admin user already exists.")

        print(f"\n[SUCCESS] Database seeded with {len(FLIGHTS)} flights!")
        print("\nAvailable Routes:")
        cities = set()
        for f in FLIGHTS:
            cities.add(f["origin"])
            cities.add(f["destination"])
        for c in sorted(cities):
            print(f"  - {c}")


if __name__ == "__main__":
    seed()
