from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3

app = Flask(__name__)
app.secret_key = 'lerestaurant123'

def get_db_connection():
    conn = sqlite3.connect('restaurant.db')
    conn.row_factory = sqlite3.Row
    return conn

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if session.get('role') != role :
                flash('Akses ditolak!', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    conn = get_db_connection()
    featured_menu = conn.execute(
        'SELECT * FROM menu WHERE available = 1 LIMIT 3'
    ).fetchall()
    conn.close()
    return render_template('index.html', featured_menu=featured_menu)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                (username, hashed_password, email, 'customer')
            )
            conn.commit()
            conn.close()

            flash('Registrasi berhasil! Silakan login', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username sudah digunakan', 'danger')

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE username = ?', (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            flash(f'Selamat datang, {username}!', 'success')

            if user['role'] == 'admin' :
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'staff' :
                return redirect(url_for('staff_dashboard'))
            else : 
                return redirect(url_for('dashboard'))
            
        else:
            flash('Username atau password salah', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Anda telah logout', 'info')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
@login_required
@role_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/staff/dashboard')
@login_required
@role_required('staff')
def staff_dashboard():
    return render_template('staff_dashboard.html')

@app.route('/dashboard')
@login_required
@role_required('customer')
def dashboard():
    conn = get_db_connection()
    reservations = conn.execute(
        'SELECT * FROM reservations WHERE user_id = ? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()

    total_reservations = len(reservations)
    pending_reservations = len([r for r in reservations if r['status'] == 'pending'])
    conn.close()

    return render_template('dashboard.html',
                           reservations=reservations,
                           total_reservations=total_reservations,
                           pending_reservations=pending_reservations)

@app.route('/menu')
def menu():
    conn = get_db_connection()
    category = request.args.get('category', '')
    if category:
        menu_items = conn.execute(
            'SELECT * FROM menu WHERE category = ? AND available = 1',
            (category,)
        ).fetchall()
    else:
        menu_items = conn.execute(
            'SELECT * FROM menu WHERE available = 1'
        ).fetchall()

    categories = conn.execute(
        'SELECT DISTINCT category FROM menu'
    ).fetchall()

    conn.close()

    return render_template('menu.html',
                           menu_items=menu_items,
                           categories=categories,
                           current_category=category)

@app.route('/reservation', methods=['GET', 'POST'])
@login_required
@role_required('customer')
def reservation():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        date = request.form['date']
        time = request.form['time']
        guests = request.form['guests']
        message = request.form.get('message', '')

        conn = get_db_connection()
        conn.execute(
            '''INSERT INTO reservations 
               (user_id, name, email, phone, date, time, guests, message) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (session['user_id'], name, email, phone, date, time, guests, message)
        )
        conn.commit()
        conn.close()

        flash('Reservasi berhasil dibuat!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('reservation.html')


if __name__ == '__main__':
    app.run(debug=True)
