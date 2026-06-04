from datetime import timedelta

from flask import Flask, redirect, session, url_for

from src.auth.oauth import init_oauth
from src.shared.cart import session_cart_count
from src.shared.config import settings
from src.shared.db import close_db, init_db


def create_app():
    app = Flask(__name__)

    app.secret_key = settings.APP_SECRET
    app.config["DATABASE_PATH"]        = settings.DATABASE_NAME
    app.config["MAX_CONTENT_LENGTH"]   = 16 * 1024 * 1024
    app.config["MAX_FORM_MEMORY_SIZE"] = 16 * 1024 * 1024

    # Keep session cookie alive across browser restarts (30 days).
    # The session cart relies on this to survive without a DB write on every
    # browser close.
    app.config["SESSION_PERMANENT"]        = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

    app.teardown_appcontext(close_db)

    init_oauth(app)

    from src.auth.routes import auth_bp
    from src.buyer.routes import buyer_bp
    from src.dashboard.routes import dashboard_bp
    from src.seller.routes import seller_bp

    app.register_blueprint(auth_bp,      url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")
    app.register_blueprint(seller_bp,    url_prefix="/seller")
    app.register_blueprint(buyer_bp,     url_prefix="/buyer")

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    # Inject cart_count into every template so the sidebar badge always works.
    @app.context_processor
    def inject_globals():
        cart_count = session_cart_count() if session.get("role") == "buyer" else 0
        return {"cart_count": cart_count}

    with app.app_context():
        init_db()

    return app


app = create_app()
