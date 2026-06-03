from flask import Flask, redirect, url_for

from src.auth.oauth import init_oauth
from src.shared.config import settings
from src.shared.db import close_db, init_db


def create_app():
    app = Flask(__name__)

    app.secret_key = settings.APP_SECRET
    app.config["DATABASE_PATH"]        = settings.DATABASE_NAME
    app.config["MAX_CONTENT_LENGTH"]   = 16 * 1024 * 1024
    app.config["MAX_FORM_MEMORY_SIZE"] = 16 * 1024 * 1024

    app.teardown_appcontext(close_db)

    init_oauth(app)

    from src.auth.routes import auth_bp
    from src.dashboard.routes import dashboard_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    @app.route("/")
    def home():
        return redirect(url_for("auth.login"))

    with app.app_context():
        init_db()

    return app


app = create_app()
