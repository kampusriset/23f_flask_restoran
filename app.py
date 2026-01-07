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
    return render_template('admin/admin_dashboard.html')


@app.route('/admin/manage', methods=['GET'])
@login_required
@role_required('admin')
def admin_manage():
    conn = get_db_connection()
    staff_list = conn.execute(
        'SELECT * FROM users WHERE role = ?', ('staff',)
    ).fetchall()
    conn.close()
    
    return render_template('admin/admin_manage.html', staff_list=staff_list)


@app.route('/admin/staff/tambah', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_tambah_staff():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form.get('email', '')
        
        hashed_password = generate_password_hash(password)
        
        conn = get_db_connection()
        try:
            conn.execute(
                'INSERT INTO users (username, password, email, role) VALUES (?, ?, ?, ?)',
                (username, hashed_password, email, 'staff')
            )
            conn.commit()
            conn.close()
            flash('Staff berhasil ditambahkan!', 'success')
            return redirect(url_for('admin_manage'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username sudah digunakan', 'danger')
    
    return render_template('admin/admin_tambah_staff.html')


@app.route('/admin/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_staff(staff_id):
    conn = get_db_connection()
    staff = conn.execute('SELECT * FROM users WHERE id = ? AND role = ?', (staff_id, 'staff')).fetchone()
    
    if not staff:
        flash('Staff tidak ditemukan', 'danger')
        return redirect(url_for('admin_manage'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        try:
            if password:
                hashed_password = generate_password_hash(password)
                conn.execute(
                    'UPDATE users SET username = ?, email = ?, password = ? WHERE id = ?',
                    (username, email, hashed_password, staff_id)
                )
            else:
                conn.execute(
                    'UPDATE users SET username = ?, email = ? WHERE id = ?',
                    (username, email, staff_id)
                )
            conn.commit()
            flash('Staff berhasil diperbarui!', 'success')
            return redirect(url_for('admin_manage'))
        except sqlite3.IntegrityError:
            flash('Username sudah digunakan', 'danger')
    
    conn.close()
    return render_template('admin/admin_edit_staff.html', staff=staff)


@app.route('/admin/staff/delete/<int:staff_id>')
@login_required
@role_required('admin')
def admin_delete_staff(staff_id):
    conn = get_db_connection()
    staff = conn.execute('SELECT * FROM users WHERE id = ? AND role = ?', (staff_id, 'staff')).fetchone()
    
    if not staff:
        flash('Staff tidak ditemukan', 'danger')
        return redirect(url_for('admin_manage'))
    
    conn.execute('DELETE FROM users WHERE id = ?', (staff_id,))
    conn.commit()
    conn.close()
    
    flash('Staff berhasil dihapus!', 'success')
    return redirect(url_for('admin_manage'))


@app.route('/admin/menu')
@login_required
@role_required('admin')
def admin_menu():
    conn = get_db_connection()
    # filtering and sorting via query params
    category = request.args.get('category', 'All')
    sort = request.args.get('sort', 'date_desc')

    base_query = 'SELECT * FROM menu'
    params = []
    if category and category != 'All':
        base_query += ' WHERE category = ?'
        params.append(category)

    # map sort keys to safe ORDER BY clauses
    order_map = {
        'date_desc': 'id DESC',
        'date_asc': 'id ASC',
        'name_asc': 'name COLLATE NOCASE ASC',
        'name_desc': 'name COLLATE NOCASE DESC',
        'price_asc': 'price ASC',
        'price_desc': 'price DESC'
    }
    order_clause = order_map.get(sort, 'id DESC')
    query = f"{base_query} ORDER BY {order_clause}"

    menu_items = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('admin/admin_menu.html', menu_items=menu_items, current_category=category, current_sort=sort)


@app.route('/admin/menu/tambah', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_tambah_menu():
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        try:
            price = int(request.form['price'])
        except (ValueError, TypeError):
            flash('Harga harus berupa angka', 'danger')
            return redirect(url_for('admin_tambah_menu'))
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', '')
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO menu (name, category, price, description, image_url, available) VALUES (?, ?, ?, ?, ?, 1)',
            (name, category, price, description, image_url)
        )
        conn.commit()
        conn.close()
        
        flash('Menu berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_menu'))
    
    return render_template('admin/admin_tambah_menu.html')


@app.route('/admin/menu/edit/<int:menu_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_menu(menu_id):
    conn = get_db_connection()
    menu_item = conn.execute('SELECT * FROM menu WHERE id = ?', (menu_id,)).fetchone()
    
    if not menu_item:
        flash('Menu tidak ditemukan', 'danger')
        return redirect(url_for('admin_menu'))
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        try:
            price = int(request.form['price'])
        except (ValueError, TypeError):
            flash('Harga harus berupa angka', 'danger')
            return redirect(url_for('admin_edit_menu', menu_id=menu_id))
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', '')
        
        conn.execute(
            'UPDATE menu SET name = ?, category = ?, price = ?, description = ?, image_url = ? WHERE id = ?',
            (name, category, price, description, image_url, menu_id)
        )
        conn.commit()
        flash('Menu berhasil diperbarui!', 'success')
        return redirect(url_for('admin_menu'))
    
    conn.close()
    return render_template('admin/admin_edit_menu.html', menu=menu_item)


@app.route('/admin/menu/delete/<int:menu_id>')
@login_required
@role_required('admin')
def admin_delete_menu(menu_id):
    conn = get_db_connection()
    menu_item = conn.execute('SELECT * FROM menu WHERE id = ?', (menu_id,)).fetchone()
    
    if not menu_item:
        flash('Menu tidak ditemukan', 'danger')
        return redirect(url_for('admin_menu'))
    
    conn.execute('DELETE FROM menu WHERE id = ?', (menu_id,))
    conn.commit()
    conn.close()
    
    flash('Menu berhasil dihapus!', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/toggle/<int:menu_id>')
@login_required
@role_required('admin')
def admin_toggle_menu(menu_id):
    conn = get_db_connection()
    menu_item = conn.execute('SELECT * FROM menu WHERE id = ?', (menu_id,)).fetchone()
    
    if not menu_item:
        flash('Menu tidak ditemukan', 'danger')
        return redirect(url_for('admin_menu'))
    
    new_status = 1 if menu_item['available'] == 0 else 0
    conn.execute('UPDATE menu SET available = ? WHERE id = ?', (new_status, menu_id))
    conn.commit()
    conn.close()
    
    flash('Status menu berhasil diubah!', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/report')
@login_required
@role_required('admin')
def admin_report():
    conn = get_db_connection()
    reservations = conn.execute(
        '''SELECT r.*, u.username FROM reservations r
           LEFT JOIN users u ON r.user_id = u.id
           ORDER BY r.created_at DESC'''
    ).fetchall()
    conn.close()
    return render_template('admin/admin_report.html', reservations=reservations)

@app.route('/staff/dashboard')
@login_required
@role_required('staff')
def staff_dashboard():
    return render_template('staff/staff_dashboard.html')

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
