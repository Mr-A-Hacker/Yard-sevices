from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key'

# Upload settings
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Data stores
admin_posts = []
service_prices = {
    'Lawn mowing': 10,
    'Snow removal': 15,
    'Raking': 10
}
submissions = []  # store service requests

# Helpers
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    return render_template('home.html', logged_in='user' in session, posts=admin_posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['user'] = request.form['username']
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != 'admin':
        return redirect(url_for('home'))

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
            admin_posts.append({'title': title, 'content': content, 'image': filename})

        # Handle new service
        if 'new_service' in request.form:
            name = request.form['new_service']
            price = int(request.form['new_price'])
            service_prices[name] = price

        # Handle price update
        if 'update_service' in request.form:
            name = request.form['update_service']
            new_price = int(request.form['updated_price'])
            if name in service_prices:
                service_prices[name] = new_price

    return render_template('admin.html',
                           posts=admin_posts,
                           services=service_prices,
                           submissions=submissions)

@app.route('/get-started', methods=['GET', 'POST'])
def get_started():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        address = request.form['address']
        phone = request.form['phone']
        service = request.form['service']
        cost = service_prices.get(service, 0)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save submission
        submissions.append({
            'user': session['user'],
            'address': address,
            'phone': phone,
            'service': service,
            'cost': cost,
            'time': timestamp
        })

        return render_template('submitted.html', cost=cost)

    return render_template('get_started.html', services=service_prices)

# Run locally
if __name__ == '__main__':
    app.run(debug=True)
