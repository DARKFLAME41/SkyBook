from flask import Flask
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from .config import Config

mongo = PyMongo()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)
    bcrypt.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    # Register blueprints
    from .routes.auth import auth_bp
    from .routes.flights import flights_bp
    from .routes.bookings import bookings_bp
    from .routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(flights_bp)
    app.register_blueprint(bookings_bp)
    app.register_blueprint(admin_bp)

    # Create indexes safely (non-blocking for serverless cold-starts)
    try:
        with app.app_context():
            mongo.db.users.create_index("email", unique=True)
            mongo.db.flights.create_index("flight_number", unique=True)
            mongo.db.bookings.create_index("user_id")
    except Exception as e:
        app.logger.warning(f"Database index creation deferred: {e}")

    return app
