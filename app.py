from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import mysql.connector
from datetime import datetime, timedelta
from collections import defaultdict
from io import BytesIO
import os

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


def update_expired_reservations():
    """Update status reservasi yang sudah lewat tanggal menjadi 'completed'"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Update reservasi yang tanggal dan waktunya sudah lewat dan statusnya masih pending/approved
        cursor.execute(
            """UPDATE reservations 
               SET status = 'completed' 
               WHERE (status = 'pending' OR status = 'approved') 
               AND CONCAT(date, ' ', time) < NOW()"""
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating expired reservations: {e}")



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
    # Update expired reservations
    update_expired_reservations()
    
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
    # Update expired reservations
    update_expired_reservations()
    
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


@app.route('/api/chart-data')
@login_required
@role_required('customer')
def chart_data():
    """API untuk menampilkan data grafik reservasi user"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Query untuk mendapatkan reservasi user dalam 30 hari terakhir
    cursor.execute(
        '''SELECT DATE(date) as reservation_date, COUNT(*) as count 
           FROM reservations 
           WHERE user_id = %s AND date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
           GROUP BY DATE(date)
           ORDER BY DATE(date) ASC''',
        (session['user_id'],)
    )
    data = cursor.fetchall()
    conn.close()
    
    # Format data untuk Chart.js
    labels = []
    counts = []
    
    # Jika tidak ada data, buat range 30 hari terakhir dengan nilai 0
    if not data:
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            labels.append(date)
            counts.append(0)
    else:
        # Buat dictionary untuk data yang ada
        data_dict = {item['reservation_date'].strftime('%Y-%m-%d'): item['count'] for item in data}
        
        # Fill dalam 30 hari dengan data yang ada atau 0
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            labels.append(date)
            counts.append(data_dict.get(date, 0))
    
    return jsonify({
        'labels': labels,
        'data': counts,
        'title': 'Reservasi Anda - 30 Hari Terakhir'
    })


@app.route('/api/chart-data-admin')
@login_required
@role_required('admin')
def chart_data_admin():
    """API untuk menampilkan data grafik reservasi keseluruhan"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Query untuk mendapatkan semua reservasi dalam 30 hari terakhir
    cursor.execute(
        '''SELECT DATE(date) as reservation_date, COUNT(*) as count 
           FROM reservations 
           WHERE date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
           GROUP BY DATE(date)
           ORDER BY DATE(date) ASC'''
    )
    data = cursor.fetchall()
    
    # Query untuk status reservasi
    cursor.execute(
        '''SELECT status, COUNT(*) as count 
           FROM reservations 
           GROUP BY status'''
    )
    status_data = cursor.fetchall()
    conn.close()
    
    # Format data untuk Chart.js - Grafik garis
    labels = []
    counts = []
    
    if not data:
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            labels.append(date)
            counts.append(0)
    else:
        data_dict = {item['reservation_date'].strftime('%Y-%m-%d'): item['count'] for item in data}
        for i in range(30, -1, -1):
            date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            labels.append(date)
            counts.append(data_dict.get(date, 0))
    
    # Format data untuk pie chart - Status
    status_labels = []
    status_counts = []
    for item in status_data:
        status_labels.append(item['status'].capitalize() if item['status'] else 'Unknown')
        status_counts.append(item['count'])
    
    return jsonify({
        'line_chart': {
            'labels': labels,
            'data': counts,
            'title': 'Total Reservasi - 30 Hari Terakhir'
        },
        'status_chart': {
            'labels': status_labels,
            'data': status_counts,
            'title': 'Status Reservasi'
        }
    })


@app.route('/print/reservations')
@login_required
@role_required('customer')
def print_reservations():
    """Print riwayat reservasi user"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM reservations WHERE user_id = %s ORDER BY created_at DESC',
        (session['user_id'],)
    )
    reservations = cursor.fetchall()
    conn.close()
    
    return render_template('print_reservations.html', 
                         reservations=reservations,
                         username=session['username'],
                         now=datetime.now())


@app.route('/admin/report/print')
@login_required
@role_required('admin')
def print_admin_report():
    """Print laporan lengkap admin"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT r.*, u.username FROM reservations r
           LEFT JOIN users u ON r.user_id = u.id
           ORDER BY r.created_at DESC'''
    )
    reservations = cursor.fetchall()
    conn.close()
    
    return render_template('print_admin_report.html', 
                         reservations=reservations,
                         now=datetime.now())


@app.route('/print/menu')
@login_required
@role_required('admin')
def print_menu():
    """Print daftar menu"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu ORDER BY category ASC, name ASC")
    menu_items = cursor.fetchall()
    conn.close()
    
    return render_template('print_menu.html', 
                         menu_items=menu_items,
                         now=datetime.now())


# PDF Download Routes
@app.route('/pdf/reservations')
@login_required
@role_required('customer')
def pdf_reservations():
    """Download PDF riwayat reservasi user"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM reservations WHERE user_id = %s ORDER BY created_at DESC',
        (session['user_id'],)
    )
    reservations = cursor.fetchall()
    conn.close()
    
    # Generate PDF using fpdf2
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Le Restaurant", ln=True, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, "Riwayat Reservasi", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 10, f"Nama: {session['username']}")
    pdf.ln()
    pdf.cell(50, 10, f"Tanggal Cetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(212, 165, 116)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(35, 7, "Tanggal", border=1, fill=True)
    pdf.cell(20, 7, "Waktu", border=1, fill=True)
    pdf.cell(40, 7, "Nama", border=1, fill=True)
    pdf.cell(30, 7, "Email", border=1, fill=True)
    pdf.cell(15, 7, "Tamu", border=1, fill=True)
    pdf.cell(25, 7, "Status", border=1, fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 9)
    for res in reservations:
        pdf.cell(35, 7, str(res['date']), border=1)
        pdf.cell(20, 7, str(res['time']), border=1)
        pdf.cell(40, 7, res['name'][:15], border=1)
        pdf.cell(30, 7, res['email'][:12], border=1)
        pdf.cell(15, 7, str(res['guests']), border=1)
        pdf.cell(25, 7, res['status'].upper()[:8], border=1)
        pdf.ln()
    
    pdf_output = pdf.output()
    
    return send_file(
        BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Riwayat_Reservasi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )


@app.route('/pdf/admin/report')
@login_required
@role_required('admin')
def pdf_admin_report():
    """Download PDF laporan admin"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        '''SELECT r.*, u.username FROM reservations r
           LEFT JOIN users u ON r.user_id = u.id
           ORDER BY r.created_at DESC'''
    )
    reservations = cursor.fetchall()
    conn.close()
    
    # Generate PDF using fpdf2
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Le Restaurant", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Laporan Reservasi Lengkap", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 10, f"Tanggal Cetak: {datetime.now().strftime('%d/%m/%Y')}")
    pdf.ln()
    pdf.cell(50, 10, f"Waktu Cetak: {datetime.now().strftime('%H:%M:%S')}")
    pdf.ln()
    pdf.cell(50, 10, f"Total Reservasi: {len(reservations)}")
    pdf.ln(5)
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(212, 165, 116)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(8, 7, "ID", border=1, fill=True)
    pdf.cell(20, 7, "User", border=1, fill=True)
    pdf.cell(25, 7, "Nama", border=1, fill=True)
    pdf.cell(25, 7, "Email", border=1, fill=True)
    pdf.cell(18, 7, "Tanggal", border=1, fill=True)
    pdf.cell(15, 7, "Waktu", border=1, fill=True)
    pdf.cell(12, 7, "Tamu", border=1, fill=True)
    pdf.cell(18, 7, "Status", border=1, fill=True)
    pdf.ln()
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 8)
    for res in reservations:
        pdf.cell(8, 6, str(res['id']), border=1)
        pdf.cell(20, 6, (res['username'] or 'Guest')[:10], border=1)
        pdf.cell(25, 6, res['name'][:12], border=1)
        pdf.cell(25, 6, res['email'][:12], border=1)
        pdf.cell(18, 6, str(res['date']), border=1)
        pdf.cell(15, 6, str(res['time']), border=1)
        pdf.cell(12, 6, str(res['guests']), border=1)
        pdf.cell(18, 6, res['status'][:8], border=1)
        pdf.ln()
    
    pdf_output = pdf.output()
    
    return send_file(
        BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Laporan_Reservasi_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )


@app.route('/pdf/menu')
@login_required
@role_required('admin')
def pdf_menu():
    """Download PDF daftar menu"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM menu ORDER BY category ASC, name ASC")
    menu_items = cursor.fetchall()
    conn.close()
    
    # Generate PDF using fpdf2
    from fpdf import FPDF
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Le Restaurant", ln=True, align="C")
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Daftar Menu Lengkap", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(50, 10, f"Tanggal Cetak: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    pdf.ln()
    pdf.cell(50, 10, f"Total Menu: {len(menu_items)} item")
    pdf.ln(5)
    
    current_category = ""
    for item in menu_items:
        if current_category != item['category']:
            current_category = item['category']
            pdf.set_font("Arial", "B", 11)
            pdf.set_fill_color(212, 165, 116)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(0, 8, current_category, fill=True, ln=True)
            pdf.set_text_color(0, 0, 0)
        
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, item['name'], ln=True)
        
        pdf.set_font("Arial", "", 9)
        pdf.cell(20, 6, f"Harga: Rp {item['price']:,}", ln=True)
        if item['description']:
            pdf.multi_cell(0, 5, f"Deskripsi: {item['description'][:80]}")
        
        status = "Tersedia" if item['available'] == 1 else "Tidak Tersedia"
        pdf.cell(0, 5, f"Status: {status}", ln=True)
        pdf.ln(2)
    
    pdf_output = pdf.output()
    
    return send_file(
        BytesIO(pdf_output),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'Daftar_Menu_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    )


if __name__ == '__main__':
    app.run(debug=True)
