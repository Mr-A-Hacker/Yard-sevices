from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "supersecretkey"  # change this in production

# --- In-memory storage (replace with database later) ---
users = {}
services = {"Lawn Care": 50, "Snow Removal": 75, "Leaf Cleanup": 40}
posts = []
submissions = []

# --- Routes ---
@app.route("/")
def home():
    return render_template("home.html",
                           logged_in="user" in session,
                           posts=posts)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            return "Passwords do not match!"
        if username in users:
            return "User already exists!"
        users[username] = {"email": email, "password": password}
        session["user"] = username
        return redirect(url_for("home"))
    return render_template("signup.html", logged_in="user" in session)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            session["user"] = username
            return redirect(url_for("home"))
        return "Invalid credentials!"
    return render_template("login.html", logged_in="user" in session)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/get-started", methods=["GET", "POST"])
def get_started():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        address = request.form["address"]
        phone = request.form["phone"]
        service = request.form["service"]
        cost = services[service]

        submissions.append({
            "user": session["user"],
            "address": address,
            "phone": phone,
            "service": service,
            "cost": cost,
            "time": "Now"  # placeholder
        })
        return render_template("submitted.html",
                               cost=cost,
                               logged_in=True)

    return render_template("get_started.html",
                           services=services,
                           logged_in=True)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("home"))

    if request.method == "POST":
        # Handle new post
        if "title" in request.form:
            posts.append({
                "title": request.form["title"],
                "content": request.form["content"],
                "image": None  # skip image upload for now
            })
        # Handle new service
        elif "new_service" in request.form:
            services[request.form["new_service"]] = int(request.form["new_price"])
        # Handle price update
        elif "update_service" in request.form:
            services[request.form["update_service"]] = int(request.form["updated_price"])

    return render_template("admin.html",
                           services=services,
                           posts=posts,
                           submissions=submissions,
                           logged_in=True)

# --- Run ---
if __name__ == "__main__":
    app.run(debug=True)
