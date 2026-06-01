# routes/auth.py
import bcrypt
from flask import Blueprint, redirect, render_template, request, session, url_for

from ..shared import db

auth_bp = Blueprint("auth", __name__, template_folder="templates")


@auth_bp.route("/signup", methods=["POST", "GET"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        user_name = request.form.get("user_name", "").strip()
        user_email = request.form.get("user_email", "").strip()
        password = request.form.get("password", "")
        image_data = request.form.get("profile_base64", "")
        role = request.form.get("user_role", "")

        if not all([full_name, user_name, user_email, password, role]):
            return render_template("auth/signup.html")

        password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        try:
            db.cur.execute(
                """
                    INSERT INTO users (fullName, userName, email, imageData, passwordHash, role)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                (full_name, user_name, user_email, image_data, password_hash, role),
            )
            db.conn.commit()
        except db.conn.IntegrityError:
            return render_template("auth/signup.html")

        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html")


@auth_bp.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        user_name = request.form.get("user_name", "").strip()
        password = request.form.get("password", "")

        if not user_name or not password:
            return render_template("auth/login.html")

        db.cur.execute(
            "SELECT userName, passwordHash, role FROM users WHERE userName = ?",
            (user_name,),
        )
        user = db.cur.fetchone()

        if not user or not bcrypt.checkpw(
            password.encode("utf-8"), user[1].encode("utf-8")
        ):
            return render_template("auth/login.html")

        session["user"] = user[0]
        session["role"] = user[2]

        return redirect(url_for(f"dashboard.{user[2]}"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
