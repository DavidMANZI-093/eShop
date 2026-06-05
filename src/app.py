from datetime import date, timedelta

from flask import Flask, render_template, session

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
    app.config["SESSION_PERMANENT"]          = True
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

    app.teardown_appcontext(close_db)

    init_oauth(app)

    from src.auth.routes     import auth_bp
    from src.buyer.routes    import buyer_bp
    from src.admin.routes    import admin_bp
    from src.dashboard.routes import dashboard_bp
    from src.seller.routes   import seller_bp

    app.register_blueprint(auth_bp,       url_prefix="/auth")
    app.register_blueprint(dashboard_bp,  url_prefix="/dashboard")
    app.register_blueprint(seller_bp,     url_prefix="/seller")
    app.register_blueprint(buyer_bp,      url_prefix="/buyer")
    app.register_blueprint(admin_bp,      url_prefix="/admin")

    @app.route("/")
    def landing():
        from src.shared.db import get_db

        db        = get_db()
        logged_in = "user" in session
        role      = session.get("role", "")

        # Live stats
        stats = {
            "products": db.execute(
                "SELECT COUNT(*) FROM products WHERE status='active'"
            ).fetchone()[0],
            "sellers": db.execute(
                "SELECT COUNT(*) FROM users WHERE role='seller'"
            ).fetchone()[0],
            "buyers": db.execute(
                "SELECT COUNT(*) FROM users WHERE role='buyer'"
            ).fetchone()[0],
        }

        # Featured products (newest first, up to 8)
        featured = [
            dict(r)
            for r in db.execute(
                """
                SELECT id, title, price, category, imageData
                FROM   products
                WHERE  status = 'active'
                ORDER  BY createdAt DESC
                LIMIT  8
                """
            ).fetchall()
        ]

        return render_template(
            "landing.html",
            logged_in       = logged_in,
            role            = role,
            stats           = stats,
            featured        = featured,
            placeholder_img = settings.DEFAULT_PRODUCT_IMAGE,
            year            = date.today().year,
        )

    # ── Template filter: format dates regardless of type (str vs datetime) ──
    @app.template_filter("date")
    def _date_filter(value, fmt="%b %d, %Y"):
        if value is None:
            return "—"
        if hasattr(value, "strftime"):
            return value.strftime(fmt)
        # Fallback: value is a string — take the date part
        s = str(value)
        return s[:10] if len(s) >= 10 else s

    # Inject cart_count into every template so the sidebar badge always works.
    @app.context_processor
    def inject_globals():
        cart_count = session_cart_count() if session.get("role") == "buyer" else 0
        return {"cart_count": cart_count}

    with app.app_context():
        init_db()

    return app


app = create_app()
