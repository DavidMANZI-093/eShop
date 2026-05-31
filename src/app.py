from flask import Flask
from src.routes.auth import auth_bp
from src.shared import db

app = Flask(__name__)

app.register_blueprint(auth_bp, url_prefix="/auth")


@app.route("/")
def home():
    return "Welcome to the eShop!"


if __name__ == "__main__":
    try:
        db.init_db()
        app.run(debug=True)
    finally:
        db.close_connection()
