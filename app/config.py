import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-flight-booking-app-2026")
    MONGO_URI = os.environ.get(
        "MONGO_URI",
        "mongodb+srv://ofharig_db_user:Hari_2006@flight.vprdvok.mongodb.net/flight_booking?retryWrites=true&w=majority&appName=Flight"
    )
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload limit

