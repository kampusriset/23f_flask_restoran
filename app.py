from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector

app = Flask(__name__)
app.secret_key = 'lerestaurant123'


def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="restaurant_db"
    )


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') != role:
                flash('Akses ditolak!', 'danger')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated
    return decorator


@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu WHERE available = 1 LIMIT 3")
    featured_menu = cursor.fetchall()
    conn.close()
    return render_template('index.html', featured_menu=featured_menu)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (%s,%s,%s,%s)",
                (
                    request.form['username'],
                    generate_password_hash(request.form['password']),
                    request.form.get('email', ''),
                    'customer'
                )
            )
            conn.commit()
            flash('Registrasi berhasil!', 'success')
            return redirect(url_for('login'))
        except mysql.connector.Error:
            flash('Username sudah digunakan', 'danger')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM users WHERE username=%s",
            (request.form['username'],)
        )
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], request.form['password']):
            session.update({
                'user_id': user['id'],
                'username': user['username'],
                'role': user['role']
            })
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            if user['role'] == 'staff':
                return redirect(url_for('staff_dashboard'))
            return redirect(url_for('dashboard'))

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


@app.route('/admin/manage')
@login_required
@role_required('admin')
def admin_manage():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE role=%s", ('staff',))
    staff_list = cursor.fetchall()
    conn.close()
    return render_template('admin/admin_manage.html', staff_list=staff_list)


@app.route('/admin/staff/tambah', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_tambah_staff():
    if request.method == 'POST':
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                (request.form['username'], generate_password_hash(request.form['password']), request.form.get('email', ''), 'staff')
            )
            conn.commit()
            flash('Staff berhasil ditambahkan!', 'success')
            conn.close()
            return redirect(url_for('admin_manage'))
        except mysql.connector.Error:
            flash('Username sudah digunakan', 'danger')
            conn.close()
    
    return render_template('admin/admin_tambah_staff.html')


@app.route('/admin/staff/edit/<int:staff_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def admin_edit_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s AND role = %s', (staff_id, 'staff'))
    staff = cursor.fetchone()
    
    if not staff:
        flash('Staff tidak ditemukan', 'danger')
        conn.close()
        return redirect(url_for('admin_manage'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        try:
            if password:
                hashed_password = generate_password_hash(password)
                cursor.execute(
                    'UPDATE users SET username = %s, email = %s, password = %s WHERE id = %s',
                    (username, email, hashed_password, staff_id)
                )
            else:
                cursor.execute(
                    'UPDATE users SET username = %s, email = %s WHERE id = %s',
                    (username, email, staff_id)
                )
            conn.commit()
            flash('Staff berhasil diperbarui!', 'success')
            conn.close()
            return redirect(url_for('admin_manage'))
        except mysql.connector.Error:
            flash('Username sudah digunakan', 'danger')
    
    conn.close()
    return render_template('admin/admin_edit_staff.html', staff=staff)


@app.route('/admin/staff/delete/<int:staff_id>')
@login_required
@role_required('admin')
def admin_delete_staff(staff_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE id = %s AND role = %s', (staff_id, 'staff'))
    staff = cursor.fetchone()
    
    if not staff:
        flash('Staff tidak ditemukan', 'danger')
        conn.close()
        return redirect(url_for('admin_manage'))
    
    cursor.execute('DELETE FROM users WHERE id = %s', (staff_id,))
    conn.commit()
    conn.close()
    
    flash('Staff berhasil dihapus!', 'success')
    return redirect(url_for('admin_manage'))


@app.route('/admin/menu')
@login_required
@role_required('admin')
def admin_menu():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    category = request.args.get('category', 'All')
    sort = request.args.get('sort', 'date_desc')

    base_query = 'SELECT * FROM menu'
    params = []
    if category and category != 'All':
        base_query += ' WHERE category = %s'
        params.append(category)

    order_map = {
        'date_desc': 'id DESC',
        'date_asc': 'id ASC',
        'name_asc': 'name ASC',
        'name_desc': 'name DESC',
        'price_asc': 'price ASC',
        'price_desc': 'price DESC'
    }
    order_clause = order_map.get(sort, 'id DESC')
    query = f"{base_query} ORDER BY {order_clause}"

    cursor.execute(query, params)
    menu_items = cursor.fetchall()
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
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO menu (name, category, price, description, image_url, available) VALUES (%s, %s, %s, %s, %s, 1)',
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM menu WHERE id = %s', (menu_id,))
    menu_item = cursor.fetchone()
    
    if not menu_item:
        flash('Menu tidak ditemukan', 'danger')
        conn.close()
        return redirect(url_for('admin_menu'))
    
    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        try:
            price = int(request.form['price'])
        except (ValueError, TypeError):
            flash('Harga harus berupa angka', 'danger')
            conn.close()
            return redirect(url_for('admin_edit_menu', menu_id=menu_id))
        description = request.form.get('description', '')
        image_url = request.form.get('image_url', '')
        
        cursor.execute(
            'UPDATE menu SET name = %s, category = %s, price = %s, description = %s, image_url = %s WHERE id = %s',
            (name, category, price, description, image_url, menu_id)
        )
        conn.commit()
        flash('Menu berhasil diperbarui!', 'success')
        conn.close()
        return redirect(url_for('admin_menu'))
    
    conn.close()
    return render_template('admin/admin_edit_menu.html', menu=menu_item)


@app.route('/admin/menu/delete/<int:menu_id>')
@login_required
@role_required('admin')
def admin_delete_menu(menu_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM menu WHERE id = %s', (menu_id,))
    menu_item = cursor.fetchone()
    
    if not menu_item:
        flash('Menu tidak ditemukan', 'danger')
        conn.close()
        return redirect(url_for('admin_menu'))
    
    cursor.execute('DELETE FROM menu WHERE id = %s', (menu_id,))
    conn.commit()
    conn.close()
    
    flash('Menu berhasil dihapus!', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/menu/toggle/<int:menu_id>')
@login_required
@role_required('admin')
def admin_toggle_menu(menu_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM menu WHERE id = %s', (menu_id,))
    menu_item = cursor.fetchone()
    
    if not menu_item:
        flash('Menu tidak ditemukan', 'danger')
        conn.close()
        return redirect(url_for('admin_menu'))
    
    new_status = 1 if menu_item['available'] == 0 else 0
    cursor.execute('UPDATE menu SET available = %s WHERE id = %s', (new_status, menu_id))
    conn.commit()
    conn.close()
    
    flash('Status menu berhasil diubah!', 'success')
    return redirect(url_for('admin_menu'))


@app.route('/admin/report')
@login_required
@role_required('admin')
def admin_report():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT r.*, u.username FROM reservations r
           LEFT JOIN users u ON r.user_id = u.id
           ORDER BY r.created_at DESC'''
    )
    reservations = cursor.fetchall()
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
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM reservations WHERE user_id = %s ORDER BY created_at DESC',
        (session['user_id'],)
    )
    reservations = cursor.fetchall()

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
    cursor = conn.cursor(dictionary=True)
    category = request.args.get('category', '')
    if category:
        cursor.execute(
            'SELECT * FROM menu WHERE category = %s AND available = 1',
            (category,)
        )
        menu_items = cursor.fetchall()
    else:
        cursor.execute(
            'SELECT * FROM menu WHERE available = 1'
        )
        menu_items = cursor.fetchall()

    cursor.execute(
        'SELECT DISTINCT category FROM menu'
    )
    categories = cursor.fetchall()

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
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO reservations 
               (user_id, name, email, phone, date, time, guests, message) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
            (session['user_id'], name, email, phone, date, time, guests, message)
        )
        conn.commit()
        conn.close()

        flash('Reservasi berhasil dibuat!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('reservation.html')


if __name__ == '__main__':
    app.run(debug=True)
