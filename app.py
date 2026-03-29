# Job Application Tracker
# Main Flask application file

# This file:
# 1) Creates the Flask app
# 2) Handles routes (pages)
# 3) Connects to SQLite database
# 4) Handles authentication (login/register)
# 5) Handles CRUD for job applications
# 6) Sends confirmation email on application save

from flask import Flask, render_template, request, redirect, url_for, g, session
from emailReminder import send_application_confirmation
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# Create Flask app
app = Flask(__name__)

# Secret key for session security
app.config["SECRET_KEY"] = "jobtracker_secret_key_group7_2026"



# DATABASE CONFIGURATION


# Base directory of project
BASE_DIR = Path(__file__).resolve().parent

# Path to database file
DB_PATH = BASE_DIR / "job_tracker.db"

# Path to schema file
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_db():
    """
    Creates and returns a database connection.
    We store it in Flask's g object so each request only uses one connection.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)

        # Allows accessing columns by name instead of index
        g.db.row_factory = sqlite3.Row

        # Enable foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")

    return g.db


@app.teardown_appcontext
def close_db(exception):
    # Job Application Tracker
# Main Flask application file

# This file:
# 1) Creates the Flask app
# 2) Handles routes (pages)
# 3) Connects to SQLite database
# 4) Handles authentication (login/register)
# 5) Handles CRUD for job applications
# 6) Sends confirmation email on application save

    from flask import Flask, render_template, request, redirect, url_for, g, session
from emailReminder import send_application_confirmation
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash

# Create Flask app
app = Flask(__name__)

# Secret key for session security
app.config["SECRET_KEY"] = "jobtracker_secret_key_group7_2026"



# DATABASE CONFIGURATION


# Base directory of project
BASE_DIR = Path(__file__).resolve().parent

# Path to database file
DB_PATH = BASE_DIR / "job_tracker.db"

# Path to schema file
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"


def get_db():
    """
    Creates and returns a database connection.
    We store it in Flask's g object so each request only uses one connection.
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)

        # Allows accessing columns by name instead of index
        g.db.row_factory = sqlite3.Row

        # Enable foreign key constraints
        g.db.execute("PRAGMA foreign_keys = ON;")

    return g.db


@app.teardown_appcontext
def close_db(exception):
    """
    Closes the database connection after the request finishes.
    This keeps the app clean and avoids leaving connections open.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Initialises the database using schema.sql.
    This creates all tables if they don’t already exist.
    """
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON;")

    # Read SQL schema file
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    # Execute SQL commands
    db.executescript(schema_sql)

    db.commit()
    db.close()



# HELPER FUNCTIONS



def is_logged_in():
    """
    Checks if a user is logged in by looking at the session.
    Returns True if logged in, otherwise False.
    """
    return "user_id" in session



# ROUTES


@app.route("/")
def home():
    """
    Home page.
    If user is logged in it goes to the dashboard
    If not it shows dashboard design with empty data
    """
    if is_logged_in():
        return redirect(url_for("dashboard"))

    return render_template(
        "dashboard.html",
        applications=[],
        email="Guest",
        stats={
            "upcoming_deadlines": 0,
            "applied": 0,
            "interview": 0,
            "offer": 0
        },
        search_query=""
    )



# AUTHENTICATION


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles user registration.  
    Gets email and password from the form,
    checks if they are valid, then saves the user in the database.
    """
    message = None

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validation
        if not email or not password or not confirm_password:
            message = "Please fill in all fields."
            return render_template("register.html", message=message)

        if password != confirm_password:
            message = "Passwords do not match."
            return render_template("register.html", message=message)

        if len(password) < 10:
            message = "Password must be at least 10 characters long."
            return render_template("register.html", message=message)

        db = get_db()

        # Hash password before storing
        password_hash = generate_password_hash(password)

        try:
            db.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
                """,
                (email, password_hash)
            )
            db.commit()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            message = "This email is already registered."

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login.
    Checks if the email and password match the database,
    then creates a session if successful.
    """
    message = None

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        # Check credentials
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))

        message = "Invalid email or password."

    return render_template("login.html", message=message)


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    """
    Allows user to reset their password.
    User enters their email and a new password,
    and the database is updated.
    P.s This is a very basic implementation without email verification for simplicity and time constraints.
    """
    message = None

    if request.method == "POST":
        email = request.form["email"].strip()
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not email or not new_password or not confirm_password:
            message = "Please fill in all fields."
            return render_template("forgettingpassword.html", message=message)

        if new_password != confirm_password:
            message = "Passwords do not match."
            return render_template("forgettingpassword.html", message=message)

        if len(new_password) < 10:
            message = "Password must be at least 10 characters long."
            return render_template("forgettingpassword.html", message=message)

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if not user:
            message = "No account found with that email."
            return render_template("forgettingpassword.html", message=message)

        new_password_hash = generate_password_hash(new_password)

        db.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = 0
            WHERE email = ?
            """,
            (new_password_hash, email)
        )
        db.commit()

        return redirect(url_for("login"))

    return render_template("forgettingpassword.html", message=message)



# DASHBOARD


@app.route("/dashboard")
def dashboard():
    """
    Main dashboard page.
    Shows all applications, allows searching,
    and calculates stats like applied, interview, and offers.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    search_query = request.args.get("search", "").strip()
    db = get_db()

    # Search filter
    if search_query:
        applications = db.execute(
            """
            SELECT *
            FROM applications
            WHERE user_id = ?
              AND (company LIKE ? OR role LIKE ?)
            ORDER BY created_at DESC
            """,
            (
                session["user_id"],
                f"%{search_query}%",
                f"%{search_query}%"
            )
        ).fetchall()
    else:
        applications = db.execute(
            """
            SELECT *
            FROM applications
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

    # Stats calculation
    all_apps = db.execute(
        """
        SELECT status, deadline
        FROM applications
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    stats = {
        "upcoming_deadlines": sum(1 for app in all_apps if app["deadline"]),
        "applied": sum(1 for app in all_apps if app["status"] == "Applied"),
        "interview": sum(1 for app in all_apps if app["status"] == "Interview"),
        "offer": sum(1 for app in all_apps if app["status"] == "Offer"),
    }

    return render_template(
        "dashboard.html",
        applications=applications,
        email=session["email"],
        stats=stats,
        search_query=search_query
    )



# APPLICATION CRUD


@app.route("/add", methods=["GET", "POST"])
def add_application():
    """
    Adds a new job application.
    Takes form data, saves it to the database,
    and sends a confirmation email.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    message = None

    if request.method == "POST":
        company = request.form["company"].strip()
        role = request.form["role"].strip()
        deadline = request.form["deadline"]
        date_applied = request.form.get("date_applied", "").strip()
        interview_date = request.form.get("interview_date", "").strip()
        status = request.form["status"]
        notes = request.form.get("notes", "").strip()
        job_url = request.form.get("job_url", "").strip()
        cover_letter = request.form.get("cover_letter", "").strip()

        if not company or not role or not deadline or not status:
            message = "Please fill in all required fields."
            return render_template("newjobpage.html", message=message)

        db = get_db()

        try:
            db.execute(
                """
                INSERT INTO applications
                (user_id, company, role, deadline, date_applied, interview_date, status, notes, job_url, cover_letter)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    company,
                    role,
                    deadline,
                    date_applied,
                    interview_date,
                    status,
                    notes,
                    job_url,
                    cover_letter
                )
            )
            db.commit()

            # Send confirmation email
            send_application_confirmation(
                session["email"],
                company,
                role,
                deadline,
                interview_date
            )

            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError:
            message = "You have already added this role for this company."

    return render_template("newjobpage.html", message=message)


@app.route("/edit/<int:app_id>", methods=["GET", "POST"])
def edit_application(app_id):
    """
    Edits an existing job application.
    Updates the selected application with new data from the form.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()

    application = db.execute(
        """
        SELECT *
        FROM applications
        WHERE id = ? AND user_id = ?
        """,
        (app_id, session["user_id"])
    ).fetchone()

    if not application:
        return "Application not found."

    message = None

    if request.method == "POST":
        company = request.form["company"].strip()
        role = request.form["role"].strip()
        deadline = request.form["deadline"]
        date_applied = request.form.get("date_applied", "").strip()
        interview_date = request.form.get("interview_date", "").strip()
        status = request.form["status"]
        notes = request.form.get("notes", "").strip()
        job_url = request.form.get("job_url", "").strip()
        cover_letter = request.form.get("cover_letter", "").strip()

        if not company or not role or not deadline or not status:
            message = "Please fill in all required fields."
            return render_template("editaplic.html", application=application, message=message)

        try:
            db.execute(
                """
                UPDATE applications
                SET company = ?, role = ?, deadline = ?, date_applied = ?, interview_date = ?, status = ?, notes = ?, job_url = ?, cover_letter = ?, updated_at = datetime('now')
                WHERE id = ? AND user_id = ?
                """,
                (
                    company,
                    role,
                    deadline,
                    date_applied,
                    interview_date,
                    status,
                    notes,
                    job_url,
                    cover_letter,
                    app_id,
                    session["user_id"]
                )
            )
            db.commit()
            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError:
            message = "That company and role already exists in your tracker."

    return render_template("editaplic.html", application=application, message=message)


@app.route("/delete/<int:app_id>", methods=["POST"])
def delete_application(app_id):
    """
    Deletes a job application.
    Removes the selected application from the database.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()

    db.execute(
        """
        DELETE FROM applications
        WHERE id = ? AND user_id = ?
        """,
        (app_id, session["user_id"])
    )

    db.commit()

    return redirect(url_for("dashboard"))



# SESSION MANAGEMENT


@app.route("/logout")
def logout():
    """
    Logs out the user.
    Clears the session data.
    """
    session.clear()
    return redirect(url_for("home"))



# RUN APPLICATION


if __name__ == "__main__":
    # Initialise database on startup
    init_db()

    # Run development server
    app.run(debug=True)
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """
    Initialises the database using schema.sql.
    This creates all tables if they don’t already exist.
    """
    db = sqlite3.connect(DB_PATH)
    db.execute("PRAGMA foreign_keys = ON;")

    # Read SQL schema file
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")

    # Execute SQL commands
    db.executescript(schema_sql)

    db.commit()
    db.close()



# HELPER FUNCTIONS



def is_logged_in():
    """
    Checks if a user is logged in by looking at the session.
    Returns True if logged in, otherwise False.
    """
    return "user_id" in session



# ROUTES


@app.route("/")
def home():
    """
    Home page.
    If user is logged in it goes to the dashboard
    If not it shows dashboard design with empty data
    """
    if is_logged_in():
        return redirect(url_for("dashboard"))

    return render_template(
        "dashboard.html",
        applications=[],
        email="Guest",
        stats={
            "upcoming_deadlines": 0,
            "applied": 0,
            "interview": 0,
            "offer": 0
        },
        search_query=""
    )



# AUTHENTICATION


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles user registration.  
    Gets email and password from the form,
    checks if they are valid, then saves the user in the database.
    """
    message = None

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Validation
        if not email or not password or not confirm_password:
            message = "Please fill in all fields."
            return render_template("register.html", message=message)

        if password != confirm_password:
            message = "Passwords do not match."
            return render_template("register.html", message=message)

        if len(password) < 10:
            message = "Password must be at least 10 characters long."
            return render_template("register.html", message=message)

        db = get_db()

        # Hash password before storing
        password_hash = generate_password_hash(password)

        try:
            db.execute(
                """
                INSERT INTO users (email, password_hash)
                VALUES (?, ?)
                """,
                (email, password_hash)
            )
            db.commit()

            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            message = "This email is already registered."

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles user login.
    Checks if the email and password match the database,
    then creates a session if successful.
    """
    message = None

    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        # Check credentials
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))

        message = "Invalid email or password."

    return render_template("login.html", message=message)


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    """
    Allows user to reset their password.
    User enters their email and a new password,
    and the database is updated.
    P.s This is a very basic implementation without email verification for simplicity and time constraints.
    """
    message = None

    if request.method == "POST":
        email = request.form["email"].strip()
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if not email or not new_password or not confirm_password:
            message = "Please fill in all fields."
            return render_template("forgettingpassword.html", message=message)

        if new_password != confirm_password:
            message = "Passwords do not match."
            return render_template("forgettingpassword.html", message=message)

        if len(new_password) < 10:
            message = "Password must be at least 10 characters long."
            return render_template("forgettingpassword.html", message=message)

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if not user:
            message = "No account found with that email."
            return render_template("forgettingpassword.html", message=message)

        new_password_hash = generate_password_hash(new_password)

        db.execute(
            """
            UPDATE users
            SET password_hash = ?, must_change_password = 0
            WHERE email = ?
            """,
            (new_password_hash, email)
        )
        db.commit()

        return redirect(url_for("login"))

    return render_template("forgettingpassword.html", message=message)



# DASHBOARD


@app.route("/dashboard")
def dashboard():
    """
    Main dashboard page.
    Shows all applications, allows searching,
    and calculates stats like applied, interview, and offers.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    search_query = request.args.get("search", "").strip()
    db = get_db()

    # Search filter
    if search_query:
        applications = db.execute(
            """
            SELECT *
            FROM applications
            WHERE user_id = ?
              AND (company LIKE ? OR role LIKE ?)
            ORDER BY created_at DESC
            """,
            (
                session["user_id"],
                f"%{search_query}%",
                f"%{search_query}%"
            )
        ).fetchall()
    else:
        applications = db.execute(
            """
            SELECT *
            FROM applications
            WHERE user_id = ?
            ORDER BY created_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

    # Stats calculation
    all_apps = db.execute(
        """
        SELECT status, deadline
        FROM applications
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchall()

    stats = {
        "upcoming_deadlines": sum(1 for app in all_apps if app["deadline"]),
        "applied": sum(1 for app in all_apps if app["status"] == "Applied"),
        "interview": sum(1 for app in all_apps if app["status"] == "Interview"),
        "offer": sum(1 for app in all_apps if app["status"] == "Offer"),
    }

    return render_template(
        "dashboard.html",
        applications=applications,
        email=session["email"],
        stats=stats,
        search_query=search_query
    )



# APPLICATION CRUD


@app.route("/add", methods=["GET", "POST"])
def add_application():
    """
    Adds a new job application.
    Takes form data, saves it to the database,
    and sends a confirmation email.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    message = None

    if request.method == "POST":
        company = request.form["company"].strip()
        role = request.form["role"].strip()
        deadline = request.form["deadline"]
        date_applied = request.form.get("date_applied", "").strip()
        interview_date = request.form.get("interview_date", "").strip()
        status = request.form["status"]
        notes = request.form.get("notes", "").strip()
        job_url = request.form.get("job_url", "").strip()
        cover_letter = request.form.get("cover_letter", "").strip()

        if not company or not role or not deadline or not status:
            message = "Please fill in all required fields."
            return render_template("newjobpage.html", message=message)

        db = get_db()

        try:
            db.execute(
                """
                INSERT INTO applications
                (user_id, company, role, deadline, date_applied, interview_date, status, notes, job_url, cover_letter)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session["user_id"],
                    company,
                    role,
                    deadline,
                    date_applied,
                    interview_date,
                    status,
                    notes,
                    job_url,
                    cover_letter
                )
            )
            db.commit()

            # Send confirmation email
            send_application_confirmation(
                session["email"],
                company,
                role,
                deadline,
                interview_date
            )

            return redirect(url_for("dashboard"))

        except sqlite3.IntegrityError:
            message = "You have already added this role for this company."

    return render_template("newjobpage.html", message=message)


@app.route("/delete/<int:app_id>", methods=["POST"])
def delete_application(app_id):
    """
    Deletes a job application.
    Removes the selected application from the database.
    """
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()

    db.execute(
        """
        DELETE FROM applications
        WHERE id = ? AND user_id = ?
        """,
        (app_id, session["user_id"])
    )

    db.commit()

    return redirect(url_for("dashboard"))



# SESSION MANAGEMENT


@app.route("/logout")
def logout():
    """
    Logs out the user.
    Clears the session data.
    """
    session.clear()
    return redirect(url_for("home"))



# RUN APPLICATION


if __name__ == "__main__":
    # Initialise database on startup
    init_db()

    # Run development server
    app.run(debug=True)