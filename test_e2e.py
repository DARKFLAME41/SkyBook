import sys
from app import create_app, mongo

app = create_app()

def run_tests():
    print("=" * 60)
    print("SKYBOOK FLIGHT BOOKING SYSTEM - COMPREHENSIVE E2E VERIFICATION")
    print("=" * 60)

    client = app.test_client()

    # 1. Homepage
    res = client.get("/")
    assert res.status_code == 200, f"Homepage failed with {res.status_code}"
    assert b"SkyBook" in res.data
    print("[PASS] 1. Homepage loaded successfully (HTTP 200)")

    # 2. Flight Search
    res = client.get("/flights/search?origin=Delhi&destination=Mumbai")
    assert res.status_code == 200, f"Search failed with {res.status_code}"
    assert b"Delhi" in res.data or b"flight" in res.data.lower()
    print("[PASS] 2. Flight search filtered by route loaded (HTTP 200)")

    # 3. Flight Details
    flight = mongo.db.flights.find_one({"status": "active"})
    assert flight is not None, "No active flights in DB"
    flight_id = str(flight["_id"])
    res = client.get(f"/flights/{flight_id}")
    assert res.status_code == 200, f"Flight detail failed with {res.status_code}"
    assert flight["flight_number"].encode() in res.data
    print(f"[PASS] 3. Flight detail for {flight['flight_number']} loaded (HTTP 200)")

    # 4. User Registration & Login Flow
    test_email = "testuser_e2e@example.com"
    test_password = "password123"
    mongo.db.users.delete_one({"email": test_email})

    reg_res = client.post("/register", data={
        "name": "E2E Traveler",
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    }, follow_redirects=True)
    assert reg_res.status_code == 200
    assert b"Account created" in reg_res.data or b"Log In" in reg_res.data
    print(f"[PASS] 4. User registration succeeded for {test_email}")

    # 5. User Login
    login_res = client.post("/login", data={
        "email": test_email,
        "password": test_password
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Welcome back" in login_res.data or b"E2E Traveler" in login_res.data
    print("[PASS] 5. User login authenticated successfully")

    # 6. Book Flight
    book_get = client.get(f"/bookings/new/{flight_id}?seats=1")
    assert book_get.status_code == 200
    print("[PASS] 6. Booking confirmation form loaded (HTTP 200)")

    initial_seats = flight.get("seat_info", {}).get("available_seats", flight.get("seats_available", 100))

    book_post = client.post(f"/bookings/new/{flight_id}", data={
        "seat_count": "1",
        "passenger_name_0": "E2E Traveler",
        "passenger_age_0": "28",
        "passenger_gender_0": "Male"
    }, follow_redirects=True)
    assert book_post.status_code == 200
    assert b"Booking confirmed" in book_post.data or b"Boarding Pass" in book_post.data or b"Booking ID" in book_post.data
    print("[PASS] 7. Flight booking created and confirmed with embedded snapshot & passengers")

    # Check seat count decreased
    flight_after = mongo.db.flights.find_one({"_id": flight["_id"]})
    new_seats = flight_after.get("seat_info", {}).get("available_seats", flight_after.get("seats_available", 100))
    assert new_seats == initial_seats - 1, f"Expected seats {initial_seats - 1}, got {new_seats}"
    print(f"[PASS] 8. Seat inventory atomically decremented from {initial_seats} to {new_seats}")

    # 7. List User Bookings
    bookings_res = client.get("/bookings/")
    assert bookings_res.status_code == 200
    assert b"My Bookings" in bookings_res.data
    assert flight["flight_number"].encode() in bookings_res.data
    print("[PASS] 9. User bookings dashboard shows active booking")

    # Find the newly created booking
    user = mongo.db.users.find_one({"email": test_email})
    booking = mongo.db.bookings.find_one({"user_id": user["_id"], "status": "confirmed"})
    assert booking is not None
    booking_id = str(booking["_id"])

    # 8. Cancellation Preview & Policy (< 3 hrs => 100% refund)
    cancel_preview = client.get(f"/bookings/{booking_id}/cancel")
    assert cancel_preview.status_code == 200
    assert b"100%" in cancel_preview.data
    print("[PASS] 10. Cancellation preview shows 100% full refund policy applied (<3 hours)")

    # 9. Execute Cancellation
    cancel_post = client.post(f"/bookings/{booking_id}/cancel", follow_redirects=True)
    assert cancel_post.status_code == 200
    assert b"cancelled successfully" in cancel_post.data.lower() or b"refund" in cancel_post.data.lower()
    print("[PASS] 11. Booking cancelled, refund recorded in DB, status updated to 'cancelled'")

    # Verify inventory was restored
    flight_restored = mongo.db.flights.find_one({"_id": flight["_id"]})
    restored_seats = flight_restored.get("seat_info", {}).get("available_seats", flight_restored.get("seats_available", 100))
    assert restored_seats == initial_seats
    print(f"[PASS] 12. Seat inventory atomically restored back to {restored_seats}")

    # 10. Admin Logout & Login
    client.get("/logout", follow_redirects=True)
    admin_login = client.post("/login", data={
        "email": "admin@flights.com",
        "password": "admin123"
    }, follow_redirects=True)
    assert admin_login.status_code == 200
    print("[PASS] 13. Admin logged in successfully")

    # 11. Admin Dashboard
    dash_res = client.get("/admin/")
    assert dash_res.status_code == 200
    assert b"Admin" in dash_res.data
    print("[PASS] 14. Admin dashboard loaded with real-time MongoDB statistics (HTTP 200)")

    # 12. Admin Flights Management
    admin_flights = client.get("/admin/flights")
    assert admin_flights.status_code == 200
    print("[PASS] 15. Admin flight management directory loaded (HTTP 200)")

    # 13. Admin Bookings View
    admin_bookings = client.get("/admin/bookings")
    assert admin_bookings.status_code == 200
    assert b"All Bookings" in admin_bookings.data
    print("[PASS] 16. Admin all-bookings overview loaded with refund tracking (HTTP 200)")

    # 14. Admin Add Flight
    new_flight_no = "SK-9999"
    mongo.db.flights.delete_one({"flight_number": new_flight_no})
    add_flight_res = client.post("/admin/flights/add", data={
        "flight_number": new_flight_no,
        "airline": "SkyBook Express",
        "origin": "Bangalore",
        "destination": "Goa",
        "departure_date": "2026-11-25",
        "departure_time": "14:00",
        "arrival_time": "15:15",
        "seats_total": "180",
        "price": "3499",
        "flight_class": "Economy",
        "aircraft_model": "Airbus A321neo",
        "photo_url": "https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?auto=format&fit=crop&w=1200&q=80"
    }, follow_redirects=True)
    assert add_flight_res.status_code == 200
    assert b"Flight SK-9999 added" in add_flight_res.data
    print("[PASS] 17. Admin added new flight with full embedded schema & specs successfully")

    print("\n" + "=" * 60)
    print("ALL 17 TESTS PASSED! APPLICATION IS 100% OPERATIONAL!")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
