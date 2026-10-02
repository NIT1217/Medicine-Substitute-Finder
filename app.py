from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    session
)

from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
from decimal import Decimal
from dotenv import load_dotenv
from functools import wraps
from sqlalchemy import or_, create_engine
from sqlalchemy.pool import NullPool
import mysql.connector
import os
import json
import urllib.request
import urllib.error
import threading
import time

from database import db
from database.models import (
    User,
    Medicine,
    MedicineSearchHistory,
    UserMedication,
    MedicineReminder
)


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH, override=True)


# ============================================================
# MYSQL CONFIGURATION
# ============================================================

MYSQL_HOST = os.getenv("sql_database_host", "localhost")
MYSQL_PORT = int(os.getenv("sql_database_port", "3306"))
MYSQL_USER = os.getenv("sql_database_user", "root")
MYSQL_PASSWORD = os.getenv("sql_database_password", "")
MYSQL_DATABASE = "MediFind"


print()
print("==========================================")
print("MediFind MySQL Configuration")
print("==========================================")
print("Host     :", MYSQL_HOST)
print("Port     :", MYSQL_PORT)
print("User     :", MYSQL_USER)
print("Password :", "********" if MYSQL_PASSWORD else "NOT SET")
print("Database :", MYSQL_DATABASE)
print("==========================================")
print()


# ============================================================
# GEMINI AI CONFIGURATION
# ============================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-2.5-flash"
).strip()

if GEMINI_API_KEY:
    print("Gemini AI : Configured")
    print("Gemini Model :", GEMINI_MODEL)
else:
    print("Gemini AI : API key not configured")

print()


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "FLASK_SECRET_KEY",
    "medifind-development-secret-key"
)


# ============================================================
# MYSQL CONNECTOR CREATOR
# ============================================================

def create_mysql_connection():

    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )


# ============================================================
# SQLALCHEMY CONFIGURATION
# ============================================================

app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+mysqlconnector://"
    "root@localhost:3306/MediFind"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "creator": create_mysql_connection,
    "pool_pre_ping": True
}

db.init_app(app)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def seed_medicines():

    if Medicine.query.count() > 0:
        return

    initial_medicines = [

        {
            "medicine_name": "Dolo 650",
            "composition": "Paracetamol 650mg",
            "manufacturer": "Micro Labs",
            "price": Decimal("30.00"),
            "description": "Paracetamol 650mg medicine."
        },

        {
            "medicine_name": "Paracetamol 650",
            "composition": "Paracetamol 650mg",
            "manufacturer": "Generic Pharma",
            "price": Decimal("18.00"),
            "description": "Paracetamol 650mg generic medicine."
        },

        {
            "medicine_name": "Calpol 650",
            "composition": "Paracetamol 650mg",
            "manufacturer": "GSK",
            "price": Decimal("28.00"),
            "description": "Paracetamol 650mg medicine."
        },

        {
            "medicine_name": "Azithral 500",
            "composition": "Azithromycin 500mg",
            "manufacturer": "Alembic",
            "price": Decimal("105.00"),
            "description": "Azithromycin 500mg medicine."
        },

        {
            "medicine_name": "Azithromycin 500",
            "composition": "Azithromycin 500mg",
            "manufacturer": "Generic Pharma",
            "price": Decimal("72.00"),
            "description": "Azithromycin 500mg generic medicine."
        }

    ]

    for item in initial_medicines:
        db.session.add(Medicine(**item))

    db.session.commit()


try:

    with app.app_context():

        db.create_all()
        seed_medicines()

        print("Database initialization successful.")

except Exception as error:

    print("Database initialization error:", error)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_current_user():

    user_id = session.get("user_id")

    if user_id is None:
        return None

    return db.session.get(User, user_id)


def is_logged_in():

    return "user_id" in session


def login_required_json(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if not is_logged_in():

            return jsonify({
                "success": False,
                "error": "Login required."
            }), 401

        return function(*args, **kwargs)

    return wrapper


def normalize_text(text):

    if not text:
        return ""

    return (
        str(text)
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
    )


def medicine_to_dict(medicine):

    return {
        "id": medicine.id,
        "name": medicine.medicine_name,
        "medicine_name": medicine.medicine_name,
        "composition": medicine.composition,
        "manufacturer": medicine.manufacturer,
        "price": float(medicine.price),
        "description": medicine.description,
        "created_at": (
            medicine.created_at.isoformat()
            if medicine.created_at
            else None
        )
    }


def medication_to_dict(medication):

    medicine = db.session.get(
        Medicine,
        medication.medicine_id
    )

    return {
        "id": medication.id,
        "medicine_id": medication.medicine_id,
        "medicine_name": (
            medicine.medicine_name
            if medicine
            else None
        ),
        "composition": (
            medicine.composition
            if medicine
            else None
        ),
        "manufacturer": (
            medicine.manufacturer
            if medicine
            else None
        ),
        "price": (
            float(medicine.price)
            if medicine and medicine.price is not None
            else None
        ),
        "dosage": medication.dosage,
        "frequency": medication.frequency,
        "start_date": (
            medication.start_date.isoformat()
            if medication.start_date
            else None
        ),
        "end_date": (
            medication.end_date.isoformat()
            if medication.end_date
            else None
        ),
        "created_at": (
            medication.created_at.isoformat()
            if medication.created_at
            else None
        )
    }


def parse_date(value):

    if not value:
        return None

    try:
        return datetime.strptime(
            str(value),
            "%Y-%m-%d"
        ).date()

    except ValueError:
        return None


def parse_time(value):

    if not value:
        return None

    try:
        return datetime.strptime(
            str(value),
            "%H:%M"
        ).time()

    except ValueError:
        return None


def get_request_data():
    """Accept both JSON requests and normal HTML form POSTs."""
    if request.is_json:
        return request.get_json(silent=True) or {}
    return request.form.to_dict()


# ============================================================
# GEMINI AI HELPER
# ============================================================

def ask_gemini(prompt):

    if not GEMINI_API_KEY:

        return {
            "success": False,
            "error": (
                "Gemini API key is not configured. "
                "Add GEMINI_API_KEY to the .env file."
            )
        }

    url = (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/"
        + GEMINI_MODEL
        + ":generateContent?key="
        + GEMINI_API_KEY
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1200
        }
    }

    data = json.dumps(payload).encode("utf-8")

    http_request = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:

        with urllib.request.urlopen(
            http_request,
            timeout=45
        ) as response:

            response_data = json.loads(
                response.read().decode("utf-8")
            )

        candidates = response_data.get(
            "candidates",
            []
        )

        if not candidates:
            return {
                "success": False,
                "error": "Gemini returned no response."
            }

        text = (
            candidates[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )

        if not text:

            return {
                "success": False,
                "error": "Gemini returned an empty response."
            }

        return {
            "success": True,
            "text": text
        }

    except urllib.error.HTTPError as error:

        try:
            error_body = error.read().decode("utf-8")
        except Exception:
            error_body = str(error)

        print("Gemini HTTP error:", error_body)

        return {
            "success": False,
            "error": (
                "Gemini API request failed. "
                + error_body[:500]
            )
        }

    except urllib.error.URLError as error:

        print("Gemini connection error:", error)

        return {
            "success": False,
            "error": (
                "Could not connect to Gemini API."
            )
        }

    except Exception as error:

        print("Gemini error:", error)

        return {
            "success": False,
            "error": "AI service error."
        }


def build_medicine_ai_prompt(medicine):

    return f"""
You are the AI Advisor inside a medicine information application called MediFind.

Medicine information from the application's database:
Medicine name: {medicine.medicine_name}
Composition: {medicine.composition}
Manufacturer: {medicine.manufacturer or "Not available"}
Description: {medicine.description or "Not available"}

Provide general educational information about this medicine.

Return the response using exactly these headings:

1. Uses
2. Common Side Effects
3. Precautions
4. Important Advice

Rules:
- Do not diagnose the user.
- Do not prescribe a dose.
- Do not tell the user to start, stop, or change a medicine.
- Do not claim that the information is a substitute for a doctor.
- Clearly state that dosage and treatment decisions should be confirmed with a doctor or pharmacist.
- Keep the response concise and easy to understand.
- Base the answer on the medicine/composition supplied above.
"""


# ============================================================
# FRONTEND PAGES
# ============================================================

@app.route("/")
def index():

    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    if not email or not password:

        return render_template(
            "login.html",
            error="Email and password are required."
        )

    user = User.query.filter_by(
        email=email
    ).first()

    if (
        user is None
        or not check_password_hash(
            user.password,
            password
        )
    ):

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    session["user_id"] = user.id

    return redirect(
        url_for("dashboard")
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get(
        "name",
        ""
    ).strip()

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )

    if not name:

        return render_template(
            "register.html",
            error="Name is required."
        )

    if not email:

        return render_template(
            "register.html",
            error="Email is required."
        )

    if not password:

        return render_template(
            "register.html",
            error="Password is required."
        )

    if password != confirm_password:

        return render_template(
            "register.html",
            error="Passwords do not match."
        )

    if len(password) < 6:

        return render_template(
            "register.html",
            error="Password must contain at least 6 characters."
        )

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:

        return render_template(
            "register.html",
            error="Email is already registered."
        )

    new_user = User(
        name=name,
        email=email,
        password=generate_password_hash(password)
    )

    try:

        db.session.add(new_user)
        db.session.commit()

        return redirect(
            url_for("login")
        )

    except Exception as error:

        db.session.rollback()

        print("Registration error:", error)

        return render_template(
            "register.html",
            error="Registration failed."
        )


@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


@app.route("/dashboard")
def dashboard():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    user = get_current_user()

    return render_template(
        "dashboard.html",
        user=user
    )


@app.route("/search")
def search():

    query = request.args.get(
        "query",
        ""
    ).strip()

    search_type = request.args.get(
        "search_type",
        "both"
    ).lower()

    if search_type not in [
        "medicine",
        "name",
        "composition",
        "both"
    ]:
        search_type = "both"

    results = []

    if query:

        normalized_query = normalize_text(query)

        medicines = Medicine.query.order_by(
            Medicine.medicine_name.asc()
        ).all()

        for medicine in medicines:

            medicine_name = normalize_text(
                medicine.medicine_name
            )

            composition = normalize_text(
                medicine.composition
            )

            if search_type in ["medicine", "name"]:

                matched = (
                    normalized_query in medicine_name
                )

            elif search_type == "composition":

                matched = (
                    normalized_query in composition
                )

            else:

                matched = (
                    normalized_query in medicine_name
                    or
                    normalized_query in composition
                )

            if matched:

                results.append(
                    medicine_to_dict(medicine)
                )

        if is_logged_in():

            history_entry = MedicineSearchHistory(
                user_id=session["user_id"],
                medicine_name=query
            )

            try:

                db.session.add(history_entry)
                db.session.commit()

            except Exception as error:

                db.session.rollback()
                print(
                    "Search history error:",
                    error
                )

    return render_template(
        "search.html",
        results=results,
        query=query,
        search_type=search_type
    )


@app.route("/medicine/<int:medicine_id>")
def medicine_details(medicine_id):

    medicine_data = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine_data is None:
        return "Medicine not found", 404

    alternatives = Medicine.query.filter(
        Medicine.id != medicine_id,
        Medicine.composition == medicine_data.composition
    ).all()

    side_effects = [
        "Nausea",
        "Stomach discomfort",
        "Headache"
    ]

    precautions = [
        "Follow the prescribed dosage.",
        "Do not exceed the recommended dose.",
        "Consult a doctor or pharmacist if unsure."
    ]

    return render_template(
        "medicine.html",
        medicine={
            "id": medicine_data.id,
            "name": medicine_data.medicine_name,
            "composition": medicine_data.composition,
            "manufacturer": medicine_data.manufacturer,
            "price": float(medicine_data.price),
            "description": medicine_data.description,
            "dosage_form": "Tablet"
        },
        alternatives=[
            {
                "id": item.id,
                "name": item.medicine_name,
                "composition": item.composition,
                "manufacturer": item.manufacturer,
                "price": float(item.price)
            }
            for item in alternatives
        ],
        side_effects=side_effects,
        precautions=precautions
    )


@app.route("/medication/add/<int:medicine_id>", methods=["POST"])
def add_medication_page(medicine_id):

    if not is_logged_in():
        return redirect(url_for("login"))

    medicine_data = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine_data is None:
        return "Medicine not found", 404

    existing_medication = UserMedication.query.filter_by(
        user_id=session["user_id"],
        medicine_id=medicine_id
    ).first()

    if existing_medication is None:

        new_medication = UserMedication(
            user_id=session["user_id"],
            medicine_id=medicine_id
        )

        try:

            db.session.add(new_medication)
            db.session.commit()

        except Exception as error:

            db.session.rollback()
            print("Add medication page error:", error)

            return "Unable to add medicine", 500

    return redirect(
        url_for("medications")
    )


@app.route("/medications")
def medications():
    if not is_logged_in():
        return redirect(url_for("login"))

    medication_rows = UserMedication.query.filter_by(
        user_id=session["user_id"]
    ).order_by(UserMedication.created_at.desc()).all()

    medication_data = []
    for item in medication_rows:
        payload = medication_to_dict(item)
        reminders = MedicineReminder.query.filter_by(
            user_medication_id=item.id
        ).order_by(
            MedicineReminder.reminder_date.asc(),
            MedicineReminder.reminder_time.asc()
        ).all()

        payload["reminders"] = [
            {
                "id": reminder.id,
                "reminder_date": reminder.reminder_date.isoformat() if reminder.reminder_date else None,
                "reminder_time": reminder.reminder_time.strftime("%H:%M") if reminder.reminder_time else None,
                "status": reminder.status or "pending"
            }
            for reminder in reminders
        ]
        medication_data.append(payload)

    available_medicines = Medicine.query.order_by(
        Medicine.medicine_name.asc()
    ).all()

    return render_template(
        "medications.html",
        medications=medication_data,
        available_medicines=available_medicines
    )


@app.route("/medications/edit/<int:medication_id>", methods=["POST"])
@login_required_json
def edit_medication_page(medication_id):

    medication = UserMedication.query.filter_by(
        id=medication_id,
        user_id=session["user_id"]
    ).first()

    if medication is None:
        return "Medication not found", 404

    dosage = request.form.get(
        "dosage",
        ""
    ).strip()

    frequency = request.form.get(
        "frequency",
        ""
    ).strip()

    start_date = parse_date(
        request.form.get("start_date")
    )

    end_date = parse_date(
        request.form.get("end_date")
    )

    if not dosage or not frequency or not start_date:
        return "Required medication fields are missing.", 400

    if end_date and end_date < start_date:
        return "End date cannot be before start date.", 400

    try:

        medication.dosage = dosage
        medication.frequency = frequency
        medication.start_date = start_date
        medication.end_date = end_date

        db.session.commit()

        return redirect(
            url_for("medications")
        )

    except Exception as error:

        db.session.rollback()
        print("Edit medication error:", error)

        return "Could not update medication.", 500


@app.route("/medications/delete/<int:medication_id>", methods=["POST"])
def delete_medication_page(medication_id):
    if not is_logged_in():
        return redirect(url_for("login"))
    medication = UserMedication.query.filter_by(
        id=medication_id, user_id=session["user_id"]
    ).first()
    if medication is None:
        return "Medication not found", 404
    try:
        MedicineReminder.query.filter_by(
            user_medication_id=medication.id
        ).delete(synchronize_session=False)
        db.session.delete(medication)
        db.session.commit()
        return redirect(url_for("medications"))
    except Exception as error:
        db.session.rollback()
        print("Delete medication page error:", error)
        return "Could not remove medication.", 500


@app.route("/reminders/delete/<int:reminder_id>", methods=["POST"])
def delete_reminder_page(reminder_id):
    if not is_logged_in():
        return redirect(url_for("login"))
    reminder = db.session.get(MedicineReminder, reminder_id)
    if reminder is None:
        return "Reminder not found", 404
    medication = db.session.get(UserMedication, reminder.user_medication_id)
    if medication is None or medication.user_id != session["user_id"]:
        return "Reminder not found", 404
    try:
        db.session.delete(reminder)
        db.session.commit()
        return redirect(url_for("medications"))
    except Exception as error:
        db.session.rollback()
        print("Delete reminder page error:", error)
        return "Could not delete reminder.", 500


@app.route("/history")
def history():
    if not is_logged_in():
        return redirect(url_for("login"))

    history_rows = MedicineSearchHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(MedicineSearchHistory.searched_at.desc()).all()
    medicines = Medicine.query.order_by(Medicine.medicine_name.asc()).all()
    history_data = []

    for item in history_rows:
        query_text = item.medicine_name or ""
        normalized_query = normalize_text(query_text)
        matched_medicine = None
        for medicine in medicines:
            medicine_name = normalize_text(medicine.medicine_name)
            composition = normalize_text(medicine.composition)
            if (
                normalized_query == medicine_name
                or normalized_query in medicine_name
                or medicine_name in normalized_query
                or normalized_query in composition
            ):
                matched_medicine = medicine
                break
        history_data.append({
            "id": item.id,
            "search_text": query_text,
            "medicine_name": matched_medicine.medicine_name if matched_medicine else query_text,
            "composition": matched_medicine.composition if matched_medicine else "Not available",
            "medicine_id": matched_medicine.id if matched_medicine else None,
            "searched_at": item.searched_at.isoformat() if item.searched_at else None
        })

    return render_template("history.html", history=history_data)


@app.route("/profile")
def profile():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )

    user = get_current_user()

    return render_template(
        "profile.html",
        user=user
    )


# ============================================================
# SEARCH API
# ============================================================

@app.route("/api/search", methods=["GET"])
def api_search():

    query = request.args.get(
        "query",
        ""
    ).strip()

    search_type = request.args.get(
        "search_type",
        "both"
    ).lower()

    if search_type not in [
        "medicine",
        "name",
        "composition",
        "both"
    ]:
        search_type = "both"

    if not query:

        return jsonify({
            "success": True,
            "query": query,
            "search_type": search_type,
            "results": [],
            "cheaper_alternatives": []
        })

    normalized_query = normalize_text(query)

    all_medicines = Medicine.query.all()
    matched_medicines = []

    for medicine in all_medicines:

        medicine_name = normalize_text(
            medicine.medicine_name
        )

        composition = normalize_text(
            medicine.composition
        )

        if search_type in ["medicine", "name"]:

            matched = normalized_query in medicine_name

        elif search_type == "composition":

            matched = normalized_query in composition

        else:

            matched = (
                normalized_query in medicine_name
                or normalized_query in composition
            )

        if matched:
            matched_medicines.append(medicine)

    if is_logged_in():

        history_entry = MedicineSearchHistory(
            user_id=session["user_id"],
            medicine_name=query
        )

        try:

            db.session.add(history_entry)
            db.session.commit()

        except Exception as error:

            db.session.rollback()
            print("Search history error:", error)

    cheaper_alternatives = []

    if matched_medicines:

        selected_medicine = matched_medicines[0]

        selected_composition = normalize_text(
            selected_medicine.composition
        )

        for medicine in all_medicines:

            current_composition = normalize_text(
                medicine.composition
            )

            if (
                current_composition == selected_composition
                and medicine.price < selected_medicine.price
                and medicine.id != selected_medicine.id
            ):

                cheaper_alternatives.append(medicine)

        cheaper_alternatives.sort(
            key=lambda medicine: medicine.price
        )

    return jsonify({

        "success": True,

        "query": query,

        "search_type": search_type,

        "results": [
            medicine_to_dict(medicine)
            for medicine in matched_medicines
        ],

        "cheaper_alternatives": [
            medicine_to_dict(medicine)
            for medicine in cheaper_alternatives
        ]
    })


# ============================================================
# MEDICINE API
# ============================================================

@app.route("/api/medicine/<int:medicine_id>", methods=["GET"])
def api_medicine(medicine_id):

    medicine_data = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine_data is None:

        return jsonify({
            "success": False,
            "error": "Medicine not found."
        }), 404

    return jsonify({
        "success": True,
        "medicine": medicine_to_dict(medicine_data)
    })


# ============================================================
# SUBSTITUTE API
# ============================================================

@app.route(
    "/api/medicine/<int:medicine_id>/substitutes",
    methods=["GET"]
)
def medicine_substitutes(medicine_id):

    medicine = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine is None:

        return jsonify({
            "success": False,
            "error": "Medicine not found."
        }), 404

    normalized_composition = normalize_text(
        medicine.composition
    )

    substitutes = []

    medicines = Medicine.query.all()

    for item in medicines:

        if item.id == medicine.id:
            continue

        if normalize_text(item.composition) == normalized_composition:
            substitutes.append(item)

    substitutes.sort(
        key=lambda item: item.price
    )

    return jsonify({

        "success": True,

        "medicine": medicine_to_dict(medicine),

        "substitutes": [
            medicine_to_dict(item)
            for item in substitutes
        ]
    })


# ============================================================
# AI ADVISOR / SAFETY INFORMATION
# ============================================================

@app.route(
    "/api/medicine/<int:medicine_id>/safety",
    methods=["GET"]
)
def medicine_safety(medicine_id):

    medicine = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine is None:

        return jsonify({
            "success": False,
            "error": "Medicine not found."
        }), 404

    prompt = build_medicine_ai_prompt(
        medicine
    )

    ai_result = ask_gemini(prompt)

    if not ai_result["success"]:

        return jsonify({

            "success": False,

            "medicine": medicine.medicine_name,

            "composition": medicine.composition,

            "llm_connected": False,

            "error": ai_result["error"]
        }), 503

    return jsonify({

        "success": True,

        "medicine": medicine.medicine_name,

        "composition": medicine.composition,

        "llm_connected": True,

        "model": GEMINI_MODEL,

        "advisor": ai_result["text"],

        "disclaimer": (
            "This AI-generated information is for general "
            "educational purposes only. Confirm medication "
            "decisions with a qualified doctor or pharmacist."
        )
    })


@app.route(
    "/api/ai/advisor",
    methods=["POST"]
)
@login_required_json
def ai_advisor():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "error": "JSON data is required."
        }), 400

    medicine_id = data.get(
        "medicine_id"
    )

    question = str(
        data.get(
            "question",
            ""
        )
    ).strip()

    if medicine_id is None:

        return jsonify({
            "success": False,
            "error": "medicine_id is required."
        }), 400

    try:

        medicine_id = int(medicine_id)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "error": "Invalid medicine_id."
        }), 400

    medicine = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine is None:

        return jsonify({
            "success": False,
            "error": "Medicine not found."
        }), 404

    if question:

        user_question = question

    else:

        user_question = (
            "Explain the uses, common side effects, "
            "precautions, and important advice for this medicine."
        )

    prompt = f"""
You are the MediFind AI Advisor.

Medicine:
Name: {medicine.medicine_name}
Composition: {medicine.composition}
Manufacturer: {medicine.manufacturer or "Not available"}
Description: {medicine.description or "Not available"}

User question:
{user_question}

Answer clearly for a general user.

Important safety rules:
- Give general educational information only.
- Do not diagnose.
- Do not prescribe or change a dose.
- Do not tell the user to start or stop a medicine.
- Mention when professional medical advice is appropriate.
- If the question requires information that cannot safely be determined from the supplied medicine information, say so.
"""

    ai_result = ask_gemini(prompt)

    if not ai_result["success"]:

        return jsonify({
            "success": False,
            "medicine": medicine.medicine_name,
            "llm_connected": False,
            "error": ai_result["error"]
        }), 503

    return jsonify({

        "success": True,

        "medicine": medicine_to_dict(medicine),

        "llm_connected": True,

        "model": GEMINI_MODEL,

        "answer": ai_result["text"],

        "disclaimer": (
            "AI Advisor provides general educational "
            "information and does not replace a doctor "
            "or pharmacist."
        )
    })


# ============================================================
# MEDICATION API
# ============================================================

@app.route("/api/medications", methods=["GET"])
@login_required_json
def get_medications():

    medications = UserMedication.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        UserMedication.created_at.desc()
    ).all()

    return jsonify({

        "success": True,

        "medications": [
            medication_to_dict(item)
            for item in medications
        ]
    })


@app.route("/api/medications", methods=["POST"])
@login_required_json
def add_medication():

    data = get_request_data()

    if not data:
        if request.is_json:
            return jsonify({
                "success": False,
                "error": "JSON data is required."
            }), 400
        return "Form data is required.", 400

    medicine_id = data.get("medicine_id")

    if medicine_id is None:

        return jsonify({
            "success": False,
            "error": "medicine_id is required."
        }), 400

    try:

        medicine_id = int(medicine_id)

    except (TypeError, ValueError):

        return jsonify({
            "success": False,
            "error": "Invalid medicine_id."
        }), 400

    medicine = db.session.get(
        Medicine,
        medicine_id
    )

    if medicine is None:

        return jsonify({
            "success": False,
            "error": "Medicine not found."
        }), 404

    dosage = data.get("dosage")
    frequency = data.get("frequency")

    if frequency is None:
        frequency = data.get("frequency_hours")

    start_date = parse_date(
        data.get("start_date")
    )

    end_date = parse_date(
        data.get("end_date")
    )

    if data.get("start_date") and start_date is None:

        return jsonify({
            "success": False,
            "error": "Invalid start_date. Use YYYY-MM-DD."
        }), 400

    if data.get("end_date") and end_date is None:

        return jsonify({
            "success": False,
            "error": "Invalid end_date. Use YYYY-MM-DD."
        }), 400

    if (
        start_date
        and end_date
        and end_date < start_date
    ):

        return jsonify({
            "success": False,
            "error": "end_date cannot be before start_date."
        }), 400

    new_medication = UserMedication(

        user_id=session["user_id"],

        medicine_id=medicine.id,

        dosage=(
            str(dosage)
            if dosage is not None
            else None
        ),

        frequency=(
            str(frequency)
            if frequency is not None
            else None
        ),

        start_date=start_date,

        end_date=end_date
    )

    try:

        db.session.add(new_medication)
        db.session.commit()

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Medication added successfully.",
                "medication": medication_to_dict(new_medication)
            }), 201

        return redirect(url_for("medications"))

    except Exception as error:

        db.session.rollback()

        print("Add medication error:", error)

        return jsonify({
            "success": False,
            "error": "Could not add medication."
        }), 500


@app.route(
    "/api/medications/<int:medication_id>",
    methods=["PUT"]
)
@login_required_json
def update_medication(medication_id):

    medication = UserMedication.query.filter_by(
        id=medication_id,
        user_id=session["user_id"]
    ).first()

    if medication is None:

        return jsonify({
            "success": False,
            "error": "Medication not found."
        }), 404

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "error": "JSON data is required."
        }), 400

    if "dosage" in data:
        medication.dosage = str(
            data["dosage"]
        )

    if "frequency" in data:
        medication.frequency = str(
            data["frequency"]
        )

    if "start_date" in data:

        start_date = parse_date(
            data["start_date"]
        )

        if data["start_date"] and start_date is None:

            return jsonify({
                "success": False,
                "error":
                    "Invalid start_date. Use YYYY-MM-DD."
            }), 400

        medication.start_date = start_date

    if "end_date" in data:

        end_date = parse_date(
            data["end_date"]
        )

        if data["end_date"] and end_date is None:

            return jsonify({
                "success": False,
                "error":
                    "Invalid end_date. Use YYYY-MM-DD."
            }), 400

        medication.end_date = end_date

    if (
        medication.start_date
        and medication.end_date
        and medication.end_date < medication.start_date
    ):

        return jsonify({
            "success": False,
            "error":
                "end_date cannot be before start_date."
        }), 400

    try:

        db.session.commit()

        return jsonify({
            "success": True,
            "message":
                "Medication updated successfully.",
            "medication":
                medication_to_dict(medication)
        })

    except Exception as error:

        db.session.rollback()

        print("Update medication error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not update medication."
        }), 500


# ============================================================
# UPCOMING MEDICATION
# ============================================================

@app.route(
    "/api/medications/upcoming",
    methods=["GET"]
)
@login_required_json
def upcoming_medication():

    medications = UserMedication.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        UserMedication.start_date.asc()
    ).all()

    if not medications:

        return jsonify({
            "success": True,
            "medication": None
        })

    current_date = date.today()
    active_medications = []

    for medication in medications:

        if (
            medication.end_date
            and medication.end_date < current_date
        ):
            continue

        active_medications.append(medication)

    if not active_medications:

        return jsonify({
            "success": True,
            "medication": None
        })

    return jsonify({

        "success": True,

        "medication":
            medication_to_dict(
                active_medications[0]
            )
    })


# ============================================================
# DELETE MEDICATION
# ============================================================

@app.route(
    "/api/medications/<int:medication_id>",
    methods=["DELETE"]
)
@login_required_json
def delete_medication(medication_id):

    medication = UserMedication.query.filter_by(
        id=medication_id,
        user_id=session["user_id"]
    ).first()

    if medication is None:

        return jsonify({
            "success": False,
            "error": "Medication not found."
        }), 404

    try:

        MedicineReminder.query.filter_by(
            user_medication_id=medication.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(medication)
        db.session.commit()

        return jsonify({
            "success": True,
            "message":
                "Medication stopped successfully."
        })

    except Exception as error:

        db.session.rollback()

        print("Delete medication error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not stop medication."
        }), 500


# ============================================================
# REMINDERS
# ============================================================

@app.route(
    "/api/reminders",
    methods=["GET"]
)
@login_required_json
def get_reminders():

    user_medications = UserMedication.query.filter_by(
        user_id=session["user_id"]
    ).all()

    medication_ids = [
        medication.id
        for medication in user_medications
    ]

    if not medication_ids:

        return jsonify({
            "success": True,
            "reminders": []
        })

    reminders = MedicineReminder.query.filter(
        MedicineReminder.user_medication_id.in_(
            medication_ids
        )
    ).order_by(
        MedicineReminder.reminder_date.asc(),
        MedicineReminder.reminder_time.asc()
    ).all()

    result = []

    for reminder in reminders:

        medication = db.session.get(
            UserMedication,
            reminder.user_medication_id
        )

        medicine = (
            db.session.get(
                Medicine,
                medication.medicine_id
            )
            if medication
            else None
        )

        result.append({

            "id": reminder.id,

            "user_medication_id":
                reminder.user_medication_id,

            "medicine_name": (
                medicine.medicine_name
                if medicine
                else None
            ),

            "reminder_date": (
                reminder.reminder_date.isoformat()
                if reminder.reminder_date
                else None
            ),

            "reminder_time": (
                reminder.reminder_time.strftime("%H:%M")
                if reminder.reminder_time
                else None
            ),

            "status": reminder.status
        })

    return jsonify({
        "success": True,
        "reminders": result
    })


@app.route(
    "/api/reminders",
    methods=["POST"]
)
@login_required_json
def add_reminder():

    data = get_request_data()

    if not data:
        if request.is_json:
            return jsonify({
                "success": False,
                "error": "JSON data is required."
            }), 400
        return "Form data is required.", 400

    medication_id = data.get(
        "user_medication_id"
    )

    reminder_date = parse_date(
        data.get("reminder_date")
    )

    reminder_time = parse_time(
        data.get("reminder_time")
    )

    if medication_id is None:

        return jsonify({
            "success": False,
            "error":
                "user_medication_id is required."
        }), 400

    if reminder_date is None:

        return jsonify({
            "success": False,
            "error":
                "Valid reminder_date is required."
        }), 400

    if reminder_time is None:

        return jsonify({
            "success": False,
            "error":
                "Valid reminder_time is required. Use HH:MM."
        }), 400

    medication = UserMedication.query.filter_by(
        id=medication_id,
        user_id=session["user_id"]
    ).first()

    if medication is None:

        return jsonify({
            "success": False,
            "error":
                "Medication not found."
        }), 404

    reminder = MedicineReminder(

        user_medication_id=medication.id,

        reminder_date=reminder_date,

        reminder_time=reminder_time,

        status="pending"
    )

    try:

        db.session.add(reminder)
        db.session.commit()

        if request.is_json:
            return jsonify({
                "success": True,
                "message": "Reminder added successfully.",
                "reminder": {
                    "id": reminder.id,
                    "user_medication_id": reminder.user_medication_id,
                    "reminder_date": reminder.reminder_date.isoformat(),
                    "reminder_time": reminder.reminder_time.strftime("%H:%M"),
                    "status": reminder.status
                }
            }), 201

        return redirect(url_for("medications"))

    except Exception as error:

        db.session.rollback()

        print("Add reminder error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not add reminder."
        }), 500


@app.route(
    "/api/reminders/<int:reminder_id>",
    methods=["DELETE"]
)
@login_required_json
def delete_reminder(reminder_id):

    reminder = db.session.get(
        MedicineReminder,
        reminder_id
    )

    if reminder is None:

        return jsonify({
            "success": False,
            "error": "Reminder not found."
        }), 404

    medication = db.session.get(
        UserMedication,
        reminder.user_medication_id
    )

    if (
        medication is None
        or medication.user_id != session["user_id"]
    ):

        return jsonify({
            "success": False,
            "error": "Reminder not found."
        }), 404

    try:

        db.session.delete(reminder)
        db.session.commit()

        return jsonify({
            "success": True,
            "message":
                "Reminder deleted successfully."
        })

    except Exception as error:

        db.session.rollback()

        print("Delete reminder error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not delete reminder."
        }), 500


# ============================================================
# HISTORY API
# ============================================================

@app.route(
    "/api/history",
    methods=["GET"]
)
@login_required_json
def get_history():

    history = MedicineSearchHistory.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        MedicineSearchHistory.searched_at.desc()
    ).all()

    result = []

    for item in history:

        result.append({

            "id": item.id,

            "search_text":
                item.medicine_name,

            "medicine_name":
                item.medicine_name,

            "searched_at": (
                item.searched_at.isoformat()
                if item.searched_at
                else None
            )
        })

    return jsonify({
        "success": True,
        "history": result
    })


# ============================================================
# PROFILE API
# ============================================================

@app.route(
    "/api/profile",
    methods=["GET"]
)
@login_required_json
def get_profile():

    user = get_current_user()

    return jsonify({

        "success": True,

        "user": {

            "id": user.id,

            "name": user.name,

            "email": user.email
        }
    })


@app.route(
    "/api/profile",
    methods=["POST"]
)
@login_required_json
def update_profile():

    data = request.get_json(
        silent=True
    )

    if not data:

        return jsonify({
            "success": False,
            "error":
                "JSON data is required."
        }), 400

    user = get_current_user()

    if "name" in data:

        name = str(
            data["name"]
        ).strip()

        if not name:

            return jsonify({
                "success": False,
                "error":
                    "Name cannot be empty."
            }), 400

        user.name = name

    if "email" in data:

        email = str(
            data["email"]
        ).strip().lower()

        if not email:

            return jsonify({
                "success": False,
                "error":
                    "Email cannot be empty."
            }), 400

        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_user:

            return jsonify({
                "success": False,
                "error":
                    "Email is already registered."
            }), 409

        user.email = email

    try:

        db.session.commit()

        return jsonify({

            "success": True,

            "message":
                "Profile updated successfully.",

            "user": {

                "id": user.id,

                "name": user.name,

                "email": user.email
            }
        })

    except Exception as error:

        db.session.rollback()

        print("Profile update error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not update profile."
        }), 500


# ============================================================
# CHANGE PASSWORD
# ============================================================

@app.route(
    "/change-password",
    methods=["POST"]
)
@login_required_json
def change_password():

    data = request.get_json(
        silent=True
    )

    if data:

        current_password = data.get(
            "current_password"
        )

        new_password = data.get(
            "new_password"
        )

        confirm_password = data.get(
            "confirm_password"
        )

    else:

        current_password = request.form.get(
            "current_password"
        )

        new_password = request.form.get(
            "new_password"
        )

        confirm_password = request.form.get(
            "confirm_password"
        )

    if not current_password:

        return jsonify({
            "success": False,
            "error":
                "Current password is required."
        }), 400

    if not new_password:

        return jsonify({
            "success": False,
            "error":
                "New password is required."
        }), 400

    if new_password != confirm_password:

        return jsonify({
            "success": False,
            "error":
                "New password and confirm password do not match."
        }), 400

    if len(new_password) < 6:

        return jsonify({
            "success": False,
            "error":
                "Password must contain at least 6 characters."
        }), 400

    user = get_current_user()

    if not check_password_hash(
        user.password,
        current_password
    ):

        return jsonify({
            "success": False,
            "error":
                "Current password is incorrect."
        }), 400

    user.password = generate_password_hash(
        new_password
    )

    try:

        db.session.commit()

        return jsonify({
            "success": True,
            "message":
                "Password changed successfully."
        })

    except Exception as error:

        db.session.rollback()

        print("Password update error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not change password."
        }), 500


# ============================================================
# NOTIFICATION SETTINGS
# ============================================================

@app.route(
    "/api/profile/notifications",
    methods=["GET", "POST"]
)
@login_required_json
def notification_settings():

    if request.method == "GET":

        return jsonify({

            "success": True,

            "notifications":
                session.get(
                    "notifications",
                    True
                )
        })

    data = request.get_json(
        silent=True
    )

    if (
        not data
        or "enabled" not in data
    ):

        return jsonify({
            "success": False,
            "error":
                "enabled is required."
        }), 400

    session["notifications"] = bool(
        data["enabled"]
    )

    return jsonify({

        "success": True,

        "message":
            "Notification settings updated.",

        "notifications":
            session["notifications"]
    })


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.route(
    "/api/notifications",
    methods=["GET"]
)
@login_required_json
def notifications():

    if not session.get(
        "notifications",
        True
    ):

        return jsonify({
            "success": True,
            "notifications": []
        })

    now = datetime.now()

    user_medications = UserMedication.query.filter_by(
        user_id=session["user_id"]
    ).all()

    notifications_list = []

    for medication in user_medications:

        if (
            medication.end_date
            and medication.end_date < now.date()
        ):
            continue

        medicine = db.session.get(
            Medicine,
            medication.medicine_id
        )

        if medicine is None:
            continue

        reminders = MedicineReminder.query.filter(
            MedicineReminder.user_medication_id == medication.id,
            MedicineReminder.status.in_(["pending", "due"])
        ).filter(
            MedicineReminder.reminder_date == now.date()
        ).all()

        for reminder in reminders:

            reminder_datetime = datetime.combine(
                reminder.reminder_date,
                reminder.reminder_time
            )

            if reminder_datetime <= now:

                notifications_list.append({

                    "reminder_id":
                        reminder.id,

                    "medication_id":
                        medication.id,

                    "medicine_name":
                        medicine.medicine_name,

                    "reminder_date":
                        reminder.reminder_date.isoformat(),

                    "reminder_time":
                        reminder.reminder_time.strftime("%H:%M"),

                    "message":
                        (
                            "Your scheduled dose of "
                            + medicine.medicine_name
                            + " is due."
                        )
                })

    return jsonify({

        "success": True,

        "notifications":
            notifications_list
    })


# ============================================================
# COMPLETE REMINDER
# ============================================================

@app.route(
    "/api/reminders/<int:reminder_id>/complete",
    methods=["POST"]
)
@login_required_json
def complete_reminder(reminder_id):

    reminder = db.session.get(
        MedicineReminder,
        reminder_id
    )

    if reminder is None:

        return jsonify({
            "success": False,
            "error":
                "Reminder not found."
        }), 404

    medication = db.session.get(
        UserMedication,
        reminder.user_medication_id
    )

    if (
        medication is None
        or medication.user_id != session["user_id"]
    ):

        return jsonify({
            "success": False,
            "error":
                "Reminder not found."
        }), 404

    reminder.status = "completed"

    try:

        db.session.commit()

        return jsonify({
            "success": True,
            "message":
                "Reminder completed."
        })

    except Exception as error:

        db.session.rollback()

        print("Complete reminder error:", error)

        return jsonify({
            "success": False,
            "error":
                "Could not update reminder."
        }), 500


# ============================================================
# DOSE HISTORY
# ============================================================

@app.route(
    "/api/dose-history",
    methods=["GET"]
)
@login_required_json
def get_dose_history():

    return jsonify({

        "success": True,

        "dose_history": []
    })


# ============================================================
# AI HEALTH CHECK
# ============================================================

@app.route(
    "/api/ai/health",
    methods=["GET"]
)
def ai_health():

    if not GEMINI_API_KEY:

        return jsonify({

            "success": True,

            "llm_connected": False,

            "model": GEMINI_MODEL,

            "message":
                "Gemini API key is not configured."
        })

    test_result = ask_gemini(
        "Reply with exactly the word: CONNECTED"
    )

    return jsonify({

        "success": True,

        "llm_connected":
            test_result["success"],

        "model":
            GEMINI_MODEL,

        "message": (
            "Gemini AI is connected."
            if test_result["success"]
            else test_result["error"]
        )
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    try:

        db.session.execute(
            db.text("SELECT 1")
        )

        database_connected = True

    except Exception as error:

        print("Health check error:", error)

        database_connected = False

    return jsonify({

        "success": True,

        "application":
            "MediFind",

        "backend":
            "Flask",

        "database":
            database_connected,

        "llm":
            bool(GEMINI_API_KEY),

        "llm_model":
            GEMINI_MODEL,

        "price_trend":
            False,

        "savings_leaderboard":
            False,

        "status":
            "Backend is running."
    })


# ============================================================
# TEST DATABASE
# ============================================================

@app.route("/test-db")
def test_db():

    try:

        users = User.query.all()
        medicines = Medicine.query.all()

        return jsonify({

            "success": True,

            "database":
                "Connected",

            "users_count":
                len(users),

            "medicines_count":
                len(medicines)
        })

    except Exception as error:

        return jsonify({

            "success": False,

            "database":
                "Connection failed",

            "error":
                str(error)
        }), 500


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success": False,

        "error":
            "Page or endpoint not found."
    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success": False,

        "error":
            "Internal server error."
    }), 500


# ============================================================
# MYSQL REMINDER EVENT
# ============================================================

def ensure_reminder_mysql_event():
    """Create the MySQL Event that marks reminders as due."""
    connection = None
    cursor = None
    try:
        table_name = MedicineReminder.__table__.name
        connection = create_mysql_connection()
        cursor = connection.cursor()
        try:
            cursor.execute("SET GLOBAL event_scheduler = ON")
        except Exception as scheduler_error:
            print("MySQL event scheduler warning:", scheduler_error)
        event_sql = f"""
        CREATE EVENT IF NOT EXISTS medifind_reminder_event
        ON SCHEDULE EVERY 5 SECOND
        DO
          UPDATE `{table_name}`
          SET status = 'due'
          WHERE status = 'pending'
            AND TIMESTAMP(reminder_date, reminder_time) <= NOW();
        """
        cursor.execute(event_sql)
        connection.commit()
        print("MySQL reminder event is ready.")
    except Exception as error:
        print("MySQL reminder event setup warning:", repr(error))
    finally:
        try:
            if cursor: cursor.close()
        except Exception: pass
        try:
            if connection: connection.close()
        except Exception: pass


# ============================================================
# REMINDER ALARM WITHOUT EDITING medications.html
# ============================================================

REMINDER_ALARM_SCRIPT = r"""
<script>
(function () {
    if (window.__medifindReminderAlarmLoaded) return;
    window.__medifindReminderAlarmLoaded = true;
    let audioContext = null;
    let alarmTimer = null;
    let currentReminderId = null;
    const storageKey = "medifind_triggered_reminders";

    function getTriggered() {
        try { return JSON.parse(localStorage.getItem(storageKey) || "[]"); }
        catch (e) { return []; }
    }
    function remember(id) {
        const ids = getTriggered();
        if (!ids.includes(id)) {
            ids.push(id);
            localStorage.setItem(storageKey, JSON.stringify(ids));
        }
    }
    function popup() {
        let element = document.getElementById("medifind-alarm-popup");
        if (element) return element;
        element = document.createElement("div");
        element.id = "medifind-alarm-popup";
        element.style.cssText = "position:fixed;top:25px;right:25px;width:340px;z-index:99999;background:#fff;border-radius:16px;padding:24px;box-shadow:0 12px 40px rgba(0,0,0,.25);border:3px solid #dc3545;font-family:Arial,sans-serif;";
        element.innerHTML = "<div style='font-size:26px;margin-bottom:10px'>⏰ Medicine Reminder</div><div id='medifind-alarm-text' style='font-size:17px;line-height:1.5;margin-bottom:18px'></div><button id='medifind-stop-alarm' style='width:100%;padding:12px;border:0;border-radius:9px;background:#dc3545;color:white;font-size:16px;font-weight:700;cursor:pointer'>Stop Alarm</button>";
        document.body.appendChild(element);
        document.getElementById("medifind-stop-alarm").onclick = stopAlarm;
        return element;
    }
    function beep() {
        try {
            audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
            if (audioContext.state === "suspended") audioContext.resume();
            const oscillator = audioContext.createOscillator();
            const gain = audioContext.createGain();
            oscillator.type = "sine";
            oscillator.frequency.value = 880;
            gain.gain.value = 0.25;
            oscillator.connect(gain);
            gain.connect(audioContext.destination);
            oscillator.start();
            oscillator.stop(audioContext.currentTime + 0.45);
        } catch (e) { console.warn("MediFind alarm audio error", e); }
    }
    function startAlarm(notification) {
        if (currentReminderId === notification.reminder_id) return;
        stopAlarm();
        currentReminderId = notification.reminder_id;
        remember(currentReminderId);
        const element = popup();
        document.getElementById("medifind-alarm-text").textContent = notification.message || "It is time to take your medicine.";
        element.style.display = "block";
        beep();
        alarmTimer = setInterval(beep, 1200);
        if ("Notification" in window && Notification.permission === "granted") {
            new Notification("MediFind Medicine Reminder", {body: notification.message || "It is time to take your medicine."});
        }
    }
    function stopAlarm() {
        if (alarmTimer) { clearInterval(alarmTimer); alarmTimer = null; }
        currentReminderId = null;
        const element = document.getElementById("medifind-alarm-popup");
        if (element) element.style.display = "none";
    }
    document.addEventListener("click", function () {
        try {
            audioContext = audioContext || new (window.AudioContext || window.webkitAudioContext)();
            if (audioContext.state === "suspended") audioContext.resume();
        } catch (e) {}
        if ("Notification" in window && Notification.permission === "default") {
            Notification.requestPermission().catch(function () {});
        }
    }, {once:true});
    async function checkReminders() {
        try {
            const response = await fetch("/api/notifications", {cache:"no-store"});
            if (!response.ok) return;
            const data = await response.json();
            if (!data.success || !Array.isArray(data.notifications)) return;
            const triggered = getTriggered();
            for (const notification of data.notifications) {
                if (!triggered.includes(notification.reminder_id)) {
                    startAlarm(notification);
                    break;
                }
            }
        } catch (e) { console.warn("MediFind reminder polling error", e); }
    }
    popup().style.display = "none";
    checkReminders();
    setInterval(checkReminders, 5000);
})();
</script>
"""

@app.after_request
def inject_reminder_alarm(response):
    """Inject alarm JavaScript into /medications without editing medications.html."""
    try:
        if (request.path == "/medications" and response.content_type and response.content_type.startswith("text/html")):
            html = response.get_data(as_text=True)
            if "__medifindReminderAlarmLoaded" not in html:
                response.set_data(html.replace("</body>", REMINDER_ALARM_SCRIPT + "</body>"))
    except Exception as error:
        print("Reminder alarm injection warning:", repr(error))
    return response


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        ensure_reminder_mysql_event()


    app.run(host="0.0.0.0", port=5000, debug=True)
