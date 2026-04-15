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
from emailReminder import send_application_confirmation, send_application_update, send_application_deleted, send_email
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash, check_password_hash
import string 

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

# Validates the password, system checks each letter and compares with the requirements to see if it's met
def validate_password(password):
    if len(password) < 10:
        return "Password must be at least 10 characters long."
    
    if not any(char.isupper() for char in password):
        return "Password must contain at least one uppercase letter."
    
    if not any(char.islower() for char in password):
        return "Password must contain at least one lowercase letter."
    
    if not any(char.isdigit() for char in password):
        return "Password must contain at least one number."
    
    if not any(char in string.punctuation for char in password):
        return "Password must contain at least one symbol."
    
    return None

#Function used to send the deadline reminders
def send_deadline_reminders():
    db = get_db()

    today = datetime.now().date()
    threshold = today + timedelta(days=3)

    apps = db.execute("""
        SELECT id, company, role, deadline, reminder_sent
        FROM applications
        WHERE user_id = ?
        
    """, (session["user_id"],)).fetchall()

    for app in apps:
        if app["deadline"] and app["reminder_sent"] == 0:
            try:
                deadline_date = datetime.strptime(app["deadline"], "%Y-%m-%d").date()

                if today <= deadline_date <= threshold:

                    subject = "Upcoming Job Application Deadline"

                    body = f"""
Reminder!

Your application for {app["role"]} at {app["company"]} is due on {app["deadline"]}.

Make sure to complete it before the deadline.

- Job Tracker
"""

                    send_email(session["email"], subject, body)

                    

                    db.execute("""
                        UPDATE applications
                        SET reminder_sent = 1
                        WHERE id = ?
                    """, (app["id"],))

            except ValueError:
                continue

    db.commit()
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

        validation_error = validate_password(password)
        if validation_error:
            return render_template("register.html", message=validation_error)
        
        db = get_db()
        password_hash = generate_password_hash(password)

        try:
            db.execute(
                "INSERT INTO users (email, password_hash) VALUES (?, ?)",
                (email, password_hash)
            )
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            message = "This email is already registered."

    return render_template("register.html", message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    message = None
    if request.method == "POST":
        email = request.form["email"].strip()
        password = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["email"] = user["email"]
            return redirect(url_for("dashboard"))
        message = "Invalid email or password."

    return render_template("login.html", message=message)


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
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

        validation_error = validate_password(new_password)
        if validation_error:
            return render_template("forgettingpassword.html", message=validation_error)
        
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if not user:
            message = "No account found with that email."
            return render_template("forgettingpassword.html", message=message)

        new_password_hash = generate_password_hash(new_password)
        db.execute(
            "UPDATE users SET password_hash = ?, must_change_password = 0 WHERE email = ?",
            (new_password_hash, email)
        )
        db.commit()
        return redirect(url_for("login"))

    return render_template("forgettingpassword.html", message=message)


# DASHBOARD

from datetime import datetime, timedelta

@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))
    
    send_deadline_reminders()

    message = request.args.get("message", None) # <-- get the success message

    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "").strip()
    sort_option = request.args.get("sort", "deadline_asc")
    
    #pagination
    page = int(request.args.get("page", 1))
    per_page = 5
    offset = (page - 1) * per_page

    db = get_db()
    
    # Base query
    query = "SELECT * FROM applications WHERE user_id = ?"
    params = [session["user_id"]]
    
    #Apply search filter
    if search_query:
        query += " AND (company LIKE ? OR role LIKE ?)"
        params.extend([f"%{search_query}%", f"%{search_query}%"])
    
    #Apply status filter
    if status_filter:
        query += " AND status = ?"
        params.append(status_filter)
    
    #Apply sorting
    if sort_option == "company_asc":
        query += " ORDER BY company COLLATE NOCASE ASC" # A-Z
    elif sort_option == "company_desc":
        query += " ORDER BY company COLLATE NOCASE DESC" # Z-A
    else:
        query += " ORDER BY deadline ASC" # default: soonest deadline first
    
    #Add pagination to query
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    applications = db.execute(query, params).fetchall()

    # Total Count for pagination
    total_apps = db.execute(
        "SELECT COUNT(*) FROM applications WHERE user_id = ?",
        (session["user_id"],)
    ).fetchone()[0]
    
    total_pages = (total_apps + per_page - 1) // per_page

    #Stats of applications calculation
    all_apps = db.execute(
        "SELECT status, deadline FROM applications WHERE user_id = ?",
        (session["user_id"],)
    ).fetchall()
    
    # Calculate stats dynamically (supports custom statuses)
    stats = {}
    for app in all_apps:
        status = app["status"]
        stats[status] = stats.get(status, 0) + 1
    
    # Add the upcoming deadlines count separately
    stats["upcoming_deadlines"] = sum(1 for app in all_apps if app["deadline"])

    
    #Upcoming deadline warnings
    warning_threshold = datetime.now() + timedelta(days=3)
    upcoming_warnings = []
    for app in applications:
        if app["deadline"]:
            try:
                deadline_date = datetime.strptime(app["deadline"], "%Y-%m-%d")
                if deadline_date <= warning_threshold:
                    upcoming_warnings.append({
                        "company": app["company"],
                        "role": app["role"],
                        "deadline": app["deadline"]
                    })
            except ValueError:
                continue #Skip invalid dates

    return render_template(
        "dashboard.html",
        applications=applications,
        email=session["email"],
        stats=stats,
        search_query=search_query,
        status_filter = status_filter,
        upcoming_warnings = upcoming_warnings,
        sort_option = sort_option,
        message=message,
        page=page,
        total_pages=total_pages
    )


# APPLICATION CRUD

@app.route("/add", methods=["GET", "POST"])
def add_application():
    if not is_logged_in():
        return redirect(url_for("login"))

    message = None
    if request.method == "POST":
        company = request.form["company"].strip()
        role = request.form["role"].strip()
        deadline = request.form["deadline"]
        date_applied = request.form.get("date_applied", "").strip()
        interview_date = request.form.get("interview_date", "").strip()
        notes = request.form.get("notes", "").strip()
        job_url = request.form.get("job_url", "").strip()
        cover_letter = request.form.get("cover_letter", "").strip()
        
        #Takes in either a predefined status or a custom status
        status_dropdown = request.form.get("status", "").strip()
        custom_status = request.form.get("custom_status", "").strip()
        status = custom_status or status_dropdown

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
                (session["user_id"], company, role, deadline, date_applied, interview_date, status, notes, job_url, cover_letter)
            )
            db.commit()
            send_application_confirmation(session["email"], company, role, deadline, interview_date)

            # Add success message
            return redirect(url_for("dashboard", message="Application successfully added."))
        except sqlite3.IntegrityError:
            message = "You have already added this role for this company."

    return render_template("newjobpage.html", message=message)


@app.route("/edit/<int:app_id>", methods=["GET", "POST"])
def edit_application(app_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()
    application = db.execute(
        "SELECT * FROM applications WHERE id = ? AND user_id = ?",
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
        notes = request.form.get("notes", "").strip()
        job_url = request.form.get("job_url", "").strip()
        cover_letter = request.form.get("cover_letter", "").strip()
        
        #Takes in either a predefined or custom status
        status_dropdown = request.form.get("status", "").strip()
        custom_status = request.form.get("custom_status", "").strip()
        status = status_dropdown or custom_status

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
                (company, role, deadline, date_applied, interview_date, status, notes, job_url, cover_letter, app_id, session["user_id"])
            )
            db.commit()

            # SEND UPDATE EMAIL
            send_application_update(session["email"], company, role)
            return redirect(url_for("dashboard", message="Application successfully updated."))
        except sqlite3.IntegrityError:
            message = "That company and role already exists in your tracker."

    return render_template("editaplic.html", application=application, message=message)


@app.route("/delete/<int:app_id>", methods=["POST"])
def delete_application(app_id):
    if not is_logged_in():
        return redirect(url_for("login"))

    db = get_db()
    
    # Get application info BEFORE deleting
    application = db.execute(
        "SELECT company, role FROM applications WHERE id = ? AND user_id = ?",
        (app_id, session["user_id"])
    ).fetchone()

    # Delete the application
    db.execute(
        "DELETE FROM applications WHERE id = ? AND user_id = ?", 
        (app_id, session["user_id"])
        )
    db.commit()

    # Send email if application existed
    if application:
        company = application["company"]
        role = application["role"]
        from emailReminder import send_application_deleted
        send_application_deleted(session["email"], company, role)
    # Redirect to dashboard with success message
    return redirect(url_for("dashboard", message="Application successfully deleted."))

# SESSION MANAGEMENT

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# RUN APPLICATION

if __name__ == "__main__":
    # Initialise database on startup
    init_db()

    # Run development server
    app.run(debug=True)

