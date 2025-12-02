from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Data stores
posts = []
services = {"Lawn Care": 10, "Snow Removal": 20, "Leaf Cleanup": 15}
submissions = []
busy_days = []  # admin-blocked dates

# Routes
@app.route("/")
def home():
    return render_template("home.html", posts=posts, logged_in=("user" in session))

@app.route("/get-started", methods=["GET", "POST"])
def get_started():
    if request.method == "POST":
        address = request.form["address"]
        phone = request.form["phone"]
        service = request.form["service"]
        day = request.form["day"]
        time = request.form["time"]

        # Check if day is blocked
        if day in busy_days:
            return "Sorry, this day is unavailable. Please choose another."

        cost = services[service]
        submissions.append({
            "user": session.get("user", "Guest"),
            "address": address,
            "phone": phone,
            "service": service,
            "day": day,
            "time": time,
            "cost": cost
        })
        return render_template("submitted.html", cost=cost, logged_in=("user" in session))

    return render_template("get_started.html", services=services, logged_in=("user" in session))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username == "admin" and password == "admin":
            session["user"] = "admin"
            return redirect(url_for("admin"))
        else:
            session["user"] = username
            return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if "user" not in session or session["user"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        # New post
        if "title" in request.form and "content" in request.form:
            title = request.form["title"]
            content = request.form["content"]
            image = None
            if "image" in request.files and request.files["image"].filename != "":
                image_file = request.files["image"]
                image = image_file.filename
                upload_path = os.path.join("static/uploads", image)
                os.makedirs(os.path.dirname(upload_path), exist_ok=True)
                image_file.save(upload_path)
            posts.append({"title": title, "content": content, "image": image})

        # Add new service
        elif "new_service" in request.form and "new_price" in request.form:
            new_service = request.form["new_service"]
            new_price = int(request.form["new_price"])
            services[new_service] = new_price

        # Update price
        elif "update_service" in request.form and "updated_price" in request.form:
            update_service = request.form["update_service"]
            updated_price = int(request.form["updated_price"])
            services[update_service] = updated_price

        # Block busy day
        elif "busy_day" in request.form:
            busy_day = request.form["busy_day"]
            if busy_day not in busy_days:
                busy_days.append(busy_day)

    return render_template("admin.html", posts=posts, services=services,
                           submissions=submissions, busy_days=busy_days)

if __name__ == "__main__":
    app.run(debug=True)
