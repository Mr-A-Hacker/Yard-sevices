from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- Database Setup ---
DB_NAME = "yard_services.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    # Services table
    c.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price INTEGER NOT NULL
        )
    """)
    # Submissions table
    c.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            address TEXT,
            phone TEXT,
            service TEXT,
            day TEXT,
            time TEXT,
            cost INTEGER,
            note TEXT
        )
    """)
    # Busy days table
    c.execute("""
        CREATE TABLE IF NOT EXISTS busy_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day TEXT UNIQUE
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- Helper Functions ---
def get_services():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, price FROM services")
    rows = c.fetchall()
    conn.close()
    return {name: price for name, price in rows}

def add_service(name, price):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO services (name, price) VALUES (?, ?)", (name, price))
    conn.commit()
    conn.close()

# preload default services
for svc, price in {"Lawn Care": 10, "Snow Removal": 20, "Leaf Cleanup": 15}.items():
    add_service(svc, price)

# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html", logged_in=("user" in session))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, generate_password_hash(password)))
            conn.commit()
            session["user"] = username
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            return "Username already exists. Please choose another."
        finally:
            conn.close()
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()

        if row and check_password_hash(row[0], password):
            session["user"] = username
            if username == "admin":
                return redirect(url_for("admin"))
            return redirect(url_for("home"))
        else:
            return "Invalid credentials. Try again."
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/get-started", methods=["GET", "POST"])
def get_started():
    services = get_services()
    if request.method == "POST":
        address = request.form["address"]
        phone = request.form["phone"]
        service = request.form["service"]
        day = request.form["day"]
        time = request.form["time"]
        note = request.form.get("note", "")

        # check busy day
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT day FROM busy_days WHERE day=?", (day,))
        if c.fetchone():
            conn.close()
            return "Sorry, this day is unavailable. Please choose another."

        cost = services[service]
        c.execute("""INSERT INTO submissions 
                     (user, address, phone, service, day, time, cost, note)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                  (session.get("user", "Guest"), address, phone, service, day, time, cost, note))
        conn.commit()
        conn.close()

        return render_template("submitted.html", cost=cost, logged_in=("user" in session))

    return render_template("get_started.html", services=services, logged_in=("user" in session))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("login"))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == "POST":
        # Add new service
        if "new_service" in request.form and "new_price" in request.form:
            add_service(request.form["new_service"], int(request.form["new_price"]))

        # Update price
        elif "update_service" in request.form and "updated_price" in request.form:
            add_service(request.form["update_service"], int(request.form["updated_price"]))

        # Block busy day
        elif "busy_day" in request.form:
            busy_day = request.form["busy_day"]
            c.execute("INSERT OR IGNORE INTO busy_days (day) VALUES (?)", (busy_day,))
            conn.commit()

        # Delete service
        elif "delete_service" in request.form:
            c.execute("DELETE FROM services WHERE name=?", (request.form["delete_service"],))
            conn.commit()

        # Delete submission
        elif "delete_submission" in request.form:
            c.execute("DELETE FROM submissions WHERE id=?", (request.form["delete_submission"],))
            conn.commit()

    # fetch data
    c.execute("SELECT name, price FROM services")
    services = {name: price for name, price in c.fetchall()}
    c.execute("SELECT * FROM submissions")
    submissions = c.fetchall()
    c.execute("SELECT day FROM busy_days")
    busy_days = [row[0] for row in c.fetchall()]
    conn.close()

    return render_template("admin.html", services=services,
                           submissions=submissions, busy_days=busy_days)

if __name__ == "__main__":
    app.run(debug=True)
