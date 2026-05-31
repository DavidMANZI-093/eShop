# routes/auth.py
from flask import Blueprint, render_template, request

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        print("POST request acquired")
    return render_template("auth/signup.html")
