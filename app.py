import os
import re
import math
import sqlite3
from datetime import datetime, date
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for

from ai_service import generate_health_remarks

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DB_PATH = BASE_DIR / "healthpredict.db"

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                email TEXT NOT NULL,
                glucose REAL NOT NULL,
                haemoglobin REAL NOT NULL,
                cholesterol REAL NOT NULL,
                remarks TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)



def validate_patient(form):
    errors = []

    name = form.get("full_name", "").strip()
    dob_text = form.get("dob", "").strip()
    email = form.get("email", "").strip()

    numeric = {}

    # Validate full name
    if not name:
        errors.append("Full name is required.")

    # Validate email
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors.append(
            "Enter a valid email address (for example, name@example.com)."
        )

    # Validate date of birth
    dob = None

    try:
        dob = datetime.strptime(dob_text, "%d.%m.%Y").date()

        if dob > date.today():
            errors.append("Date of birth cannot be in the future.")

    except ValueError:
        errors.append(
            "Date of birth must be a real date in DD.MM.YYYY format."
        )

    # Validate blood test values
    limits = {
        "glucose": ("Glucose", 20, 600),
        "haemoglobin": ("Haemoglobin", 3, 25),
        "cholesterol": ("Cholesterol", 50, 600),
    }

    for field, (label, minimum, maximum) in limits.items():
        raw = form.get(field, "").strip()

        try:
            value = float(raw)

            if not math.isfinite(value):
                raise ValueError

            if not minimum <= value <= maximum:
                errors.append(
                    f"{label} must be between {minimum} and {maximum}."
                )
            else:
                numeric[field] = value

        except ValueError:
            errors.append(
                f"{label} must be a valid numeric value."
            )

    if errors:
        return None, errors

    clean = {
        "full_name": name,
        "dob": dob.strftime("%d.%m.%Y"),
        "email": email,
        **numeric,
    }

    return clean, []



def save_patient(data, patient_id=None):
    # Only the necessary blood-test values are sent to the AI service.
    remarks = generate_health_remarks(
        data["glucose"], data["haemoglobin"], data["cholesterol"]
    )
    with get_db() as conn:
        if patient_id is None:
            conn.execute("""
                INSERT INTO patients
                (full_name, dob, email, glucose, haemoglobin, cholesterol, remarks)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data["full_name"], data["dob"], data["email"],
                  data["glucose"], data["haemoglobin"], data["cholesterol"], remarks))
        else:
            conn.execute("""
                UPDATE patients
                SET full_name=?, dob=?, email=?, glucose=?, haemoglobin=?,
                    cholesterol=?, remarks=?
                WHERE id=?
            """, (data["full_name"], data["dob"], data["email"],
                  data["glucose"], data["haemoglobin"], data["cholesterol"],
                  remarks, patient_id))


@app.route("/")
def index():
    with get_db() as conn:
        patients = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    return render_template("index.html", patients=patients, total=total,
                           api_configured=bool(os.getenv("GEMINI_API_KEY")))

@app.route("/add", methods=["GET", "POST"])
def add_patient():
    if request.method == "POST":
        data, errors = validate_patient(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("patient_form.html", patient=request.form, page_title="Add patient")
        save_patient(data)
        flash("Patient record added.", "success")
        return redirect(url_for("index"))
    return render_template("patient_form.html", patient={}, page_title="Add patient")


@app.route("/edit/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    with get_db() as conn:
        patient = conn.execute("SELECT * FROM patients WHERE id=?", (patient_id,)).fetchone()
    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        data, errors = validate_patient(request.form)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("patient_form.html", patient=request.form,
                                   page_title="Edit patient", patient_id=patient_id)
        save_patient(data, patient_id)
        flash("Patient record updated.", "success")
        return redirect(url_for("index"))

    return render_template("patient_form.html", patient=patient,
                           page_title="Edit patient", patient_id=patient_id)


@app.post("/delete/<int:patient_id>")
def delete_patient(patient_id):
    with get_db() as conn:
        conn.execute("DELETE FROM patients WHERE id=?", (patient_id,))
    flash("Patient record deleted.", "success")
    return redirect(url_for("index"))


@app.post("/retry-ai/<int:patient_id>")
def retry_ai(patient_id):
    # Find the patient
    with get_db() as conn:
        patient = conn.execute(
            "SELECT * FROM patients WHERE id = ?",
            (patient_id,)
        ).fetchone()

    if patient is None:
        flash("Patient record not found.", "error")
        return redirect(url_for("index"))

    # Generate new AI remarks
    remarks = generate_health_remarks(
        patient["glucose"],
        patient["haemoglobin"],
        patient["cholesterol"]
    )

    # Check whether Gemini failed
    if (
        remarks.startswith("AI service")
        or remarks.startswith("AI remarks pending")
    ):
        flash("Gemini is temporarily unavailable. Please try again later.", "error")
        return redirect(url_for("index"))

    # Save successful remarks
    with get_db() as conn:
        conn.execute(
            "UPDATE patients SET remarks = ? WHERE id = ?",
            (remarks, patient_id)
        )

    flash("AI remarks generated and saved successfully.", "success")
    return redirect(url_for("index"))

@app.get("/health")
def health():
    return {"status": "ok", "application": "HealthPredict"}


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
