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

from datetime import datetime, timedelta

from database import db

from database.models import (
    User,
    Medicine,
    MedicineSearchHistory,
    UserMedication,
    MedicineReminder
)


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from database import db
from dotenv import load_dotenv
from sqlalchemy.engine import URL
import os


# ============================================================
# FLASK APPLICATION
# ============================================================


load_dotenv()

print("DB USER:", repr(os.getenv("sql_database_user")))
print("DB HOST:", repr(os.getenv("sql_database_host")))
print("DB NAME:", repr(os.getenv("sql_database_name")))
print("DB PASSWORD SET:", bool(os.getenv("sql_database_password")))

app = Flask(__name__)

db_url = URL.create(
    "mysql+mysqlconnector",
    username=os.getenv("sql_database_user"),
    password=os.getenv("sql_database_password"),
    host=os.getenv("sql_database_host", "localhost"),
    port=int(os.getenv("sql_database_port", "3306")),
    database="MediFind"
)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# Used for Flask sessions
app.secret_key = "medifind-development-secret-key"


# ============================================================
# TEMPORARY DATA
# ============================================================
#
# IMPORTANT:
# No database is being used at this stage.
#
# These Python lists will temporarily behave like our
# database.
#
# Later:
#
# Python lists
#      ↓
# MySQL tables
#
# ============================================================


# ------------------------------------------------------------
# USERS
# ------------------------------------------------------------

users = []


# ------------------------------------------------------------
# MEDICINES
# ------------------------------------------------------------

medicines = [

    {
        "id": 1,

        "name": "Dolo 650",

        "composition": "Paracetamol 650mg",

        "manufacturer": "Micro Labs",

        "price": 30.00,

        "description":
            "Paracetamol 650mg medicine."
    },

    {
        "id": 2,

        "name": "Paracetamol 650",

        "composition": "Paracetamol 650mg",

        "manufacturer": "Generic Pharma",

        "price": 18.00,

        "description":
            "Paracetamol 650mg generic medicine."
    },

    {
        "id": 3,

        "name": "Calpol 650",

        "composition": "Paracetamol 650mg",

        "manufacturer": "GSK",

        "price": 28.00,

        "description":
            "Paracetamol 650mg medicine."
    },

    {
        "id": 4,

        "name": "Azithral 500",

        "composition": "Azithromycin 500mg",

        "manufacturer": "Alembic",

        "price": 105.00,

        "description":
            "Azithromycin 500mg medicine."
    },

    {
        "id": 5,

        "name": "Azithromycin 500",

        "composition": "Azithromycin 500mg",

        "manufacturer": "Generic Pharma",

        "price": 72.00,

        "description":
            "Azithromycin 500mg generic medicine."
    }

]


# ------------------------------------------------------------
# SEARCH HISTORY
# ------------------------------------------------------------

search_history = []


# ------------------------------------------------------------
# USER MEDICATIONS
# ------------------------------------------------------------

user_medications = []


# ------------------------------------------------------------
# DOSE HISTORY
# ------------------------------------------------------------

dose_history = []


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def get_current_user():
    """
    Return the currently logged-in user.
    """

    user_id = session.get("user_id")

    if user_id is None:

        return None

    for user in users:

        if user["id"] == user_id:

            return user

    return None


def is_logged_in():
    """
    Check whether a user is logged in.
    """

    return "user_id" in session


def find_medicine(medicine_id):
    """
    Find a medicine using its ID.
    """

    for medicine in medicines:

        if medicine["id"] == medicine_id:

            return medicine

    return None


def normalize_text(text):
    """
    Normalize text for basic syntactic comparison.

    Example:

        Paracetamol 650 MG

    becomes:

        paracetamol650mg
    """

    if not text:

        return ""

    text = text.lower()

    text = text.replace(
        " ",
        ""
    )

    text = text.replace(
        "-",
        ""
    )

    text = text.replace(
        "_",
        ""
    )

    return text


def medicine_to_dict(medicine):
    """
    Convert medicine dictionary into JSON-friendly data.
    """

    return {

        "id":
            medicine["id"],

        "name":
            medicine["name"],

        "composition":
            medicine["composition"],

        "manufacturer":
            medicine["manufacturer"],

        "price":
            medicine["price"],

        "description":
            medicine["description"]

    }


# ============================================================
# FRONTEND PAGES
# ============================================================


# ------------------------------------------------------------
# HOME
# ------------------------------------------------------------

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ------------------------------------------------------------
# LOGIN
# ------------------------------------------------------------

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    # --------------------------------------------------------
    # GET
    # --------------------------------------------------------

    if request.method == "GET":

        return render_template(
            "login.html"
        )


    # --------------------------------------------------------
    # POST
    # --------------------------------------------------------

    email = request.form.get(
        "email",
        ""
    ).strip().lower()

    password = request.form.get(
        "password",
        ""
    )


    # Validation

    if not email or not password:

        return render_template(
            "login.html",
            error="Email and password are required."
        )


    # Find user

    user = None

    for item in users:

        if item["email"] == email:

            user = item

            break


    if user is None:

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    # Check password

    if not check_password_hash(
        user["password"],
        password
    ):

        return render_template(
            "login.html",
            error="Invalid email or password."
        )


    # Create login session

    session["user_id"] = user["id"]


    return redirect(
        url_for("dashboard")
    )


# ------------------------------------------------------------
# REGISTER
# ------------------------------------------------------------

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    # GET

    if request.method == "GET":

        return render_template(
            "register.html"
        )


    # POST

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


    # Validation

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


    # Check duplicate email

    for user in users:

        if user["email"] == email:

            return render_template(
                "register.html",
                error="Email is already registered."
            )


    # Create user

    new_user = {

        "id":
            len(users) + 1,

        "name":
            name,

        "email":
            email,

        "password":
            generate_password_hash(
                password
            ),

        "notifications":
            True,

        "created_at":
            datetime.now().isoformat()

    }


    users.append(
        new_user
    )


    return redirect(
        url_for("login")
    )


# ------------------------------------------------------------
# LOGOUT
# ------------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("index")
    )


# ------------------------------------------------------------
# DASHBOARD
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# SEARCH PAGE
# ------------------------------------------------------------

@app.route("/search")
def search():

    return render_template(
        "search.html"
    )


# ------------------------------------------------------------
# MEDICINE PAGE
# ------------------------------------------------------------

@app.route("/medicine")
def medicine():

    medicine_id = request.args.get(
        "id",
        type=int
    )


    medicine_data = None


    if medicine_id:

        medicine_data = find_medicine(
            medicine_id
        )


        if medicine_data is None:

            return "Medicine not found", 404


    return render_template(
        "medicine.html",
        medicine=medicine_data
    )


# ------------------------------------------------------------
# MEDICINE DETAILS PAGE
# ------------------------------------------------------------

@app.route(
    "/medicine/<int:medicine_id>"
)
def medicine_details(
    medicine_id
):

    medicine_data = find_medicine(
        medicine_id
    )


    if medicine_data is None:

        return "Medicine not found", 404


    return render_template(
        "medicine.html",
        medicine=medicine_data
    )


# ------------------------------------------------------------
# MEDICATIONS PAGE
# ------------------------------------------------------------

@app.route("/medications")
def medications():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    return render_template(
        "medications.html"
    )


# ------------------------------------------------------------
# HISTORY PAGE
# ------------------------------------------------------------

@app.route("/history")
def history():

    if not is_logged_in():

        return redirect(
            url_for("login")
        )


    return render_template(
        "history.html"
    )


# ------------------------------------------------------------
# PROFILE PAGE
# ------------------------------------------------------------

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


@app.route(
    "/api/search",
    methods=["GET"]
)
def api_search():

    query = request.args.get(
        "query",
        ""
    ).strip()


    search_type = request.args.get(
        "search_type",
        "both"
    ).lower()


    # --------------------------------------------------------
    # Empty search
    # --------------------------------------------------------

    if not query:

        return jsonify({

            "success":
                True,

            "query":
                query,

            "results":
                [],

            "cheaper_alternatives":
                []

        })


    normalized_query = normalize_text(
        query
    )


    matched_medicines = []


    # --------------------------------------------------------
    # SEARCH BY NAME
    # --------------------------------------------------------

    if search_type == "name":

        for medicine_item in medicines:

            medicine_name = normalize_text(
                medicine_item["name"]
            )


            if normalized_query in medicine_name:

                matched_medicines.append(
                    medicine_item
                )


    # --------------------------------------------------------
    # SEARCH BY COMPOSITION
    # --------------------------------------------------------

    elif search_type == "composition":

        for medicine_item in medicines:

            composition = normalize_text(
                medicine_item["composition"]
            )


            if normalized_query in composition:

                matched_medicines.append(
                    medicine_item
                )


    # --------------------------------------------------------
    # SEARCH BY BOTH
    # --------------------------------------------------------

    else:

        for medicine_item in medicines:

            medicine_name = normalize_text(
                medicine_item["name"]
            )

            composition = normalize_text(
                medicine_item["composition"]
            )


            if (
                normalized_query in medicine_name
                or
                normalized_query in composition
            ):

                matched_medicines.append(
                    medicine_item
                )


    # --------------------------------------------------------
    # SAVE SEARCH HISTORY
    # --------------------------------------------------------

    if is_logged_in():

        user = get_current_user()


        search_history.append({

            "id":
                len(search_history) + 1,

            "user_id":
                user["id"],

            "search_text":
                query,

            "search_type":
                search_type,

            "searched_at":
                datetime.now().isoformat(),

            "medicine_id":
                (
                    matched_medicines[0]["id"]
                    if matched_medicines
                    else None
                )

        })


    # --------------------------------------------------------
    # FIND CHEAPER ALTERNATIVES
    # --------------------------------------------------------

    cheaper_alternatives = []


    if matched_medicines:

        selected_medicine = matched_medicines[0]


        selected_composition = normalize_text(
            selected_medicine["composition"]
        )


        for medicine_item in medicines:

            current_composition = normalize_text(
                medicine_item["composition"]
            )


            if (

                current_composition
                ==
                selected_composition

                and

                medicine_item["price"]
                <
                selected_medicine["price"]

                and

                medicine_item["id"]
                !=
                selected_medicine["id"]

            ):

                cheaper_alternatives.append(
                    medicine_item
                )


        # Cheapest first

        cheaper_alternatives.sort(
            key=lambda x: x["price"]
        )


    return jsonify({

        "success":
            True,

        "query":
            query,

        "search_type":
            search_type,

        "results": [

            medicine_to_dict(
                medicine_item
            )

            for medicine_item
            in matched_medicines

        ],

        "cheaper_alternatives": [

            medicine_to_dict(
                medicine_item
            )

            for medicine_item
            in cheaper_alternatives

        ]

    })


# ============================================================
# MEDICINE API
# ============================================================


@app.route(
    "/api/medicine/<int:medicine_id>",
    methods=["GET"]
)
def api_medicine(
    medicine_id
):

    medicine_data = find_medicine(
        medicine_id
    )


    if medicine_data is None:

        return jsonify({

            "success":
                False,

            "error":
                "Medicine not found."

        }), 404


    return jsonify({

        "success":
            True,

        "medicine":
            medicine_to_dict(
                medicine_data
            )

    })


# ============================================================
# SAFETY INFORMATION API
# ============================================================
#
# LLM IS NOT CONNECTED YET.
#
# This endpoint exists so that your frontend can already
# communicate with the backend.
#
# Later:
#
# JavaScript
#     ↓
# Flask
#     ↓
# LLM
#     ↓
# Side effects + precautions
#
# ============================================================


@app.route(
    "/api/medicine/<int:medicine_id>/safety",
    methods=["GET"]
)
def medicine_safety(
    medicine_id
):

    medicine_data = find_medicine(
        medicine_id
    )


    if medicine_data is None:

        return jsonify({

            "success":
                False,

            "error":
                "Medicine not found."

        }), 404


    return jsonify({

        "success":
            True,

        "medicine":
            medicine_data["name"],

        "composition":
            medicine_data["composition"],

        "llm_connected":
            False,

        "message":
            "Safety information will be generated after LLM integration."

    })


# ============================================================
# MEDICATION API
# ============================================================


@app.route(
    "/api/medications",
    methods=["GET"]
)
def get_medications():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    result = []


    for medication in user_medications:

        if medication["user_id"] != user["id"]:

            continue


        medicine_data = find_medicine(
            medication["medicine_id"]
        )


        if medicine_data is None:

            continue


        result.append({

            "id":
                medication["id"],

            "medicine_id":
                medicine_data["id"],

            "medicine_name":
                medicine_data["name"],

            "composition":
                medicine_data["composition"],

            "frequency_hours":
                medication["frequency_hours"],

            "start_date":
                medication["start_date"],

            "next_dose":
                medication["next_dose"],

            "active":
                medication["active"]

        })


    return jsonify({

        "success":
            True,

        "medications":
            result

    })


# ============================================================
# ADD MEDICATION
# ============================================================


@app.route(
    "/api/medications",
    methods=["POST"]
)
def add_medication():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success":
                False,

            "error":
                "JSON data is required."

        }), 400


    medicine_id = data.get(
        "medicine_id"
    )


    if medicine_id is None:

        return jsonify({

            "success":
                False,

            "error":
                "medicine_id is required."

        }), 400


    medicine_data = find_medicine(
        int(medicine_id)
    )


    if medicine_data is None:

        return jsonify({

            "success":
                False,

            "error":
                "Medicine not found."

        }), 404


    # --------------------------------------------------------
    # Frequency
    # --------------------------------------------------------

    frequency_hours = data.get(
        "frequency_hours"
    )


    # Allow simple frontend values

    if frequency_hours is None:

        frequency = data.get(
            "frequency",
            "24"
        )


        frequency_map = {

            "once_daily":
                24,

            "twice_daily":
                12,

            "three_times_daily":
                8,

            "four_times_daily":
                6

        }


        frequency_hours = frequency_map.get(
            str(frequency),
            None
        )


    try:

        frequency_hours = int(
            frequency_hours
        )

    except (
        TypeError,
        ValueError
    ):

        return jsonify({

            "success":
                False,

            "error":
                "Invalid frequency."

        }), 400


    if frequency_hours <= 0:

        return jsonify({

            "success":
                False,

            "error":
                "Frequency must be greater than zero."

        }), 400


    # --------------------------------------------------------
    # Start time
    # --------------------------------------------------------

    now = datetime.now()


    # --------------------------------------------------------
    # Calculate next dose
    # --------------------------------------------------------

    next_dose = (
        now
        +
        timedelta(
            hours=frequency_hours
        )
    )


    # --------------------------------------------------------
    # Create medication
    # --------------------------------------------------------

    new_medication = {

        "id":
            len(user_medications) + 1,

        "user_id":
            get_current_user()["id"],

        "medicine_id":
            medicine_data["id"],

        "frequency_hours":
            frequency_hours,

        "start_date":
            now.isoformat(),

        "next_dose":
            next_dose.isoformat(),

        "active":
            True

    }


    user_medications.append(
        new_medication
    )


    return jsonify({

        "success":
            True,

        "message":
            "Medication added successfully.",

        "medication": {

            "id":
                new_medication["id"],

            "medicine_id":
                medicine_data["id"],

            "medicine_name":
                medicine_data["name"],

            "composition":
                medicine_data["composition"],

            "frequency_hours":
                frequency_hours,

            "start_date":
                now.isoformat(),

            "next_dose":
                next_dose.isoformat()

        }

    }), 201


# ============================================================
# UPCOMING MEDICATION
# ============================================================


@app.route(
    "/api/medications/upcoming",
    methods=["GET"]
)
def upcoming_medication():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    user_meds = []


    for medication in user_medications:

        if (
            medication["user_id"]
            ==
            user["id"]

            and

            medication["active"]
        ):

            user_meds.append(
                medication
            )


    if not user_meds:

        return jsonify({

            "success":
                True,

            "medication":
                None

        })


    # Sort by next dose

    user_meds.sort(
        key=lambda x: x["next_dose"]
    )


    medication = user_meds[0]


    medicine_data = find_medicine(
        medication["medicine_id"]
    )


    return jsonify({

        "success":
            True,

        "medication": {

            "id":
                medication["id"],

            "medicine_id":
                medicine_data["id"],

            "medicine_name":
                medicine_data["name"],

            "composition":
                medicine_data["composition"],

            "next_dose":
                medication["next_dose"],

            "frequency_hours":
                medication["frequency_hours"]

        }

    })


# ============================================================
# MARK MEDICATION AS TAKEN
# ============================================================


@app.route(
    "/api/medications/<int:medication_id>/taken",
    methods=["POST"]
)
def mark_dose_taken(
    medication_id
):

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    medication = None


    for item in user_medications:

        if (

            item["id"]
            ==
            medication_id

            and

            item["user_id"]
            ==
            user["id"]

            and

            item["active"]

        ):

            medication = item

            break


    if medication is None:

        return jsonify({

            "success":
                False,

            "error":
                "Medication not found."

        }), 404


    now = datetime.now()


    # --------------------------------------------------------
    # Store dose history
    # --------------------------------------------------------

    dose_history.append({

        "id":
            len(dose_history) + 1,

        "user_id":
            user["id"],

        "medication_id":
            medication["id"],

        "taken_at":
            now.isoformat()

    })


    # --------------------------------------------------------
    # Calculate next dose
    # --------------------------------------------------------

    next_dose = (

        now

        +

        timedelta(
            hours=medication[
                "frequency_hours"
            ]
        )

    )


    medication["next_dose"] = (
        next_dose.isoformat()
    )


    return jsonify({

        "success":
            True,

        "message":
            "Dose marked as taken.",

        "next_dose":
            next_dose.isoformat()

    })


# ============================================================
# DELETE / STOP MEDICATION
# ============================================================


@app.route(
    "/api/medications/<int:medication_id>",
    methods=["DELETE"]
)
def delete_medication(
    medication_id
):

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    for medication in user_medications:

        if (

            medication["id"]
            ==
            medication_id

            and

            medication["user_id"]
            ==
            user["id"]

        ):

            medication["active"] = False


            return jsonify({

                "success":
                    True,

                "message":
                    "Medication stopped successfully."

            })


    return jsonify({

        "success":
            False,

        "error":
            "Medication not found."

    }), 404


# ============================================================
# SEARCH HISTORY API
# ============================================================


@app.route(
    "/api/history",
    methods=["GET"]
)
def get_history():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    user_history = []


    for history_item in search_history:

        if history_item["user_id"] != user["id"]:

            continue


        medicine_data = None


        if history_item["medicine_id"]:

            medicine_data = find_medicine(
                history_item["medicine_id"]
            )


        user_history.append({

            "id":
                history_item["id"],

            "search_text":
                history_item["search_text"],

            "search_type":
                history_item["search_type"],

            "medicine_id":
                history_item["medicine_id"],

            "medicine_name":
                (
                    medicine_data["name"]
                    if medicine_data
                    else None
                ),

            "composition":
                (
                    medicine_data["composition"]
                    if medicine_data
                    else None
                ),

            "searched_at":
                history_item["searched_at"]

        })


    # Latest search first

    user_history.reverse()


    return jsonify({

        "success":
            True,

        "history":
            user_history

    })


# ============================================================
# PROFILE API
# ============================================================


@app.route(
    "/api/profile",
    methods=["GET"]
)
def get_profile():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    return jsonify({

        "success":
            True,

        "user": {

            "id":
                user["id"],

            "name":
                user["name"],

            "email":
                user["email"],

            "notifications":
                user["notifications"]

        }

    })


# ============================================================
# UPDATE PROFILE
# ============================================================


@app.route(
    "/api/profile",
    methods=["POST"]
)
def update_profile():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    data = request.get_json(
        silent=True
    )


    if not data:

        return jsonify({

            "success":
                False,

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

                "success":
                    False,

                "error":
                    "Name cannot be empty."

            }), 400


        user["name"] = name


    return jsonify({

        "success":
            True,

        "message":
            "Profile updated successfully.",

        "user": {

            "id":
                user["id"],

            "name":
                user["name"],

            "email":
                user["email"]

        }

    })


# ============================================================
# NOTIFICATION SETTINGS
# ============================================================


@app.route(
    "/api/profile/notifications",
    methods=["POST"]
)
def update_notifications():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    data = request.get_json(
        silent=True
    )


    if not data or "enabled" not in data:

        return jsonify({

            "success":
                False,

            "error":
                "enabled is required."

        }), 400


    user = get_current_user()


    user["notifications"] = bool(
        data["enabled"]
    )


    return jsonify({

        "success":
            True,

        "message":
            "Notification settings updated.",

        "notifications":
            user["notifications"]

    })
    
    
    
    
    


# ============================================================
# NOTIFICATIONS
# ============================================================




@app.route(
    "/api/notifications",
    methods=["GET"]
)
def notifications():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    if not user["notifications"]:

        return jsonify({

            "success":
                True,

            "notifications":
                []

        })


    now = datetime.now()


    notifications_list = []


    for medication in user_medications:

        if (

            medication["user_id"]
            !=
            user["id"]

            or

            not medication["active"]

        ):

            continue


        next_dose = datetime.fromisoformat(
            medication["next_dose"]
        )


        if next_dose <= now:

            medicine_data = find_medicine(
                medication["medicine_id"]
            )


            if medicine_data:

                notifications_list.append({

                    "medication_id":
                        medication["id"],

                    "medicine_name":
                        medicine_data["name"],

                    "next_dose":
                        medication["next_dose"],

                    "message":
                        (
                            "Your scheduled dose of "
                            +
                            medicine_data["name"]
                            +
                            " is due."
                        )

                })


    return jsonify({

        "success":
            True,

        "notifications":
            notifications_list

    })
    
@app.route("/change-password", methods=["POST"])
def change_password():

    # For now, database is not connected.
    # So we will only demonstrate the functionality.

    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not current_password:
        return "Current password is required", 400

    if not new_password:
        return "New password is required", 400

    if new_password != confirm_password:
        return "New password and confirm password do not match", 400

    if len(new_password) < 6:
        return "Password must contain at least 6 characters", 400

    return "Password changed successfully"


# ============================================================
# DOSE HISTORY
# ============================================================


@app.route(
    "/api/dose-history",
    methods=["GET"]
)
def get_dose_history():

    if not is_logged_in():

        return jsonify({

            "success":
                False,

            "error":
                "Login required."

        }), 401


    user = get_current_user()


    result = []


    for dose in dose_history:

        if dose["user_id"] != user["id"]:

            continue


        medication = None


        for item in user_medications:

            if item["id"] == dose["medication_id"]:

                medication = item

                break


        if medication is None:

            continue


        medicine_data = find_medicine(
            medication["medicine_id"]
        )


        if medicine_data is None:

            continue


        result.append({

            "id":
                dose["id"],

            "medication_id":
                dose["medication_id"],

            "medicine_name":
                medicine_data["name"],

            "taken_at":
                dose["taken_at"]

        })


    result.reverse()


    return jsonify({

        "success":
            True,

        "dose_history":
            result

    })


# ============================================================
# HEALTH CHECK
# ============================================================


@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({

        "success":
            True,

        "application":
            "MediFind",

        "backend":
            "Flask",

        "database":
            False,

        "llm":
            False,

        "status":
            "Backend is running."

    })


# ============================================================
# ERROR HANDLERS
# ============================================================


@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "success":
            False,

        "error":
            "Page or endpoint not found."

    }), 404


@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "success":
            False,

        "error":
            "Internal server error."

    }), 500


# ============================================================
# RUN APPLICATION
# ============================================================


@app.route("/test-db")
def test_db():
    try:
        users = User.query.all()

        return jsonify({
            "success": True,
            "database": "Connected",
            "users_count": len(users)
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "database": "Connection failed",
            "error": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=True)