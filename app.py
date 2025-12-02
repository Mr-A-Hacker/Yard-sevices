from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Database file
DB_FILE = "database.db"

# Initialize database
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Posts table
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT, content TEXT, image TEXT)''')
    # Services table
    c.execute('''CREATE TABLE IF NOT EXISTS services
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT UNIQUE, price INTEGER)''')
    # Submissions table
    c.execute('''CREATE TABLE IF NOT EXISTS submissions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user TEXT, address TEXT, phone TEXT,
                  service TEXT, cost INTEGER, time TEXT)''')
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE, password TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_services():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT name, price FROM services")
    services = dict(c.fetchall())
    conn.close()
    return services

# Routes
@app.route('/')
def home():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT title, content, image FROM posts")
    posts = [{"title": row[0], "content": row[1], "image": row[2]} for row in c.fetchall()]
    conn.close()
    return render_template('home.html', logged_in='user' in session, posts=posts)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists!"
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if row and check_password_hash(row[0], password):
            session['user'] = username
            return redirect(url_for('home'))
        else:
            return "Invalid credentials!"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != 'admin':
        return redirect(url_for('home'))

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if request.method == 'POST':
        # Handle new post
        if 'title' in request.form:
            title = request.form['title']
            content = request.form['content']
            image = request.files['image']
            filename = None
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            c.execute("INSERT INTO posts (title, content, image) VALUES (?, ?, ?)", (title, content, filename))

        # Handle new service
        if 'new_service' in request.form:
            name = request.form['new_service']
            price = int(request.form['new_price'])
            c.execute("INSERT OR REPLACE INTO services (name, price) VALUES (?, ?)", (name, price))

        # Handle price update
        if 'update_service' in request.form:
            name = request.form['update_service']
            new_price = int(request.form['updated_price'])
            c.execute("UPDATE services SET price=? WHERE name=?", (new_price, name))

        conn.commit()

    # Fetch posts, services, submissions
    c.execute("SELECT title, content, image FROM posts")
    posts = [{"title": row[0], "content": row[1], "image": row[2]} for row in c.fetchall()]
    c.execute("SELECT name, price FROM services")
    services = dict(c.fetchall())
    c.execute("SELECT user, address, phone, service, cost, time FROM submissions")
    submissions = [{"user": row[0], "address": row[1], "phone": row[2],
                    "service": row[3], "cost": row[4], "time": row[5]} for row in c.fetchall()]
    conn.close()

    return render_template('admin.html', posts=posts, services=services, submissions=submissions)

@app.route('/get-started', methods=['GET', 'POST'])
def get_started():
    if 'user' not in session:
        return redirect(url_for('login'))

    services = get_services()

    if request.method == 'POST':
        address = request.form['address']
        phone = request.form['phone']
        service = request.form['service']
        cost = services.get(service, 0)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("INSERT INTO submissions (user, address, phone, service, cost, time) VALUES (?, ?, ?, ?, ?, ?)",
                  (session['user'], address, phone, service, cost, timestamp))
        conn.commit()
        conn.close()

        return render_template('submitted.html', cost=cost)

    return render_template('get_started.html', services=services)

# Run locally
if __name__ == '__main__':
    app.run(debug=True)
