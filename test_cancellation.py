from app import create_app, mongo
from app.models.booking import create_booking, cancel_booking, calculate_cancellation_refund
from app.models.flight import get_all_flights
from datetime import datetime, timedelta

app = create_app()
with app.app_context():
    user = mongo.db.users.find_one()
    flights = get_all_flights()
    if user and flights:
        flight = flights[0]

        # Case 1: Cancelled within 3 hours
        b1_id = create_booking(user['_id'], str(flight['_id']), [{'name': 'Pax 1'}], 1, 6000.0)
        b1 = mongo.db.bookings.find_one({'_id': b1_id})
        res1 = calculate_cancellation_refund(b1)
        print("--- CASE 1: Booked < 3 Hours Ago ---")
        print("Refund preview:", res1)
        cancel_booking(b1_id)
        b1_db = mongo.db.bookings.find_one({'_id': b1_id})
        print("DB Status:", b1_db['status'], "| Refund Amount:", b1_db['refund_amount'], "| Pct:", b1_db['refund_percentage'], "%")

        # Case 2: Cancelled after 3 hours (e.g., 6 hours ago)
        b2_id = create_booking(user['_id'], str(flight['_id']), [{'name': 'Pax 2'}], 2, 12000.0)
        mongo.db.bookings.update_one({'_id': b2_id}, {'$set': {'booked_at': datetime.utcnow() - timedelta(hours=6)}})
        b2 = mongo.db.bookings.find_one({'_id': b2_id})
        res2 = calculate_cancellation_refund(b2)
        print("\n--- CASE 2: Booked > 3 Hours Ago (6h ago) ---")
        print("Refund preview:", res2)
        cancel_booking(b2_id)
        b2_db = mongo.db.bookings.find_one({'_id': b2_id})
        print("DB Status:", b2_db['status'], "| Refund Amount:", b2_db['refund_amount'], "| Pct:", b2_db['refund_percentage'], "%")
