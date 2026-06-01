from flask import Flask
from src.routes.auth import auth_bp
from src.routes.dashboard import dashboard_bp
from src.shared import db, settings

app = Flask(__name__)
app.secret_key = settings.APP_SECRET
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
app.config["MAX_FORM_MEMORY_SIZE"] = 16 * 1024 * 1024

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(dashboard_bp)


@app.route("/")
def home():
    return "Welcome to the eShop!"


if __name__ == "__main__":
    try:
        db.init_db()
        app.run(debug=True)
    finally:
        db.close_connection()
