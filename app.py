from flask import Flask, render_template, request, redirect, url_for, session, make_response, flash
from models import KategoriIkan, DaftarIkan, User

app = Flask(__name__)
app.secret_key = '$2&2!@my_secret'  

def login_required():
    return 'user_id' in session

def admin_only():
    return session.get("role") == "admin"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    message = ""
    last_username = request.cookies.get('last_username', '')
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.check_login(username, password)
        if user:
            session['user_id'] = user['id_user']
            session['username'] = user['username']
            session['role'] = user['role']
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('last_username', username, max_age=60*60*24*7)
            return resp
        else:
            message = "Invalid username or password"
            flash(message, 'danger')
    return render_template('login.html', message=message, last_username=last_username)

@app.route('/logout')
def logout():
    session.clear()
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('last_username', '', max_age=0)
    return resp

@app.route('/')
def index():
    if not login_required():
        return redirect(url_for('login'))

    q = request.args.get('q', '').strip()
    kategorifilter = request.args.get('kategori', '').strip()
    id_Kategori = int(kategorifilter) if kategorifilter.isdigit() else None

    print("DEBUG: q=", repr(q), "id_kategori=", id_Kategori)
    ikan = DaftarIkan.search(q=q if q else None, id_kategori=id_Kategori)
    print("DEBUG: hasil_count=", len(ikan))
    kategori = KategoriIkan.get_all()
    ikan = DaftarIkan.get_all()
    last_username = request.cookies.get('last_username')
    return render_template(
        'index.html',
        kategori=kategori,
        ikan=ikan,
        username=session.get('username'),
        last_username=last_username,
        q=q,
        selected_kategori=id_Kategori

    )

# Kategori (admin only)
@app.route('/kategori/insert', methods=['GET', 'POST'])
def form_kategori_insert():
    if not login_required():
        return redirect(url_for('login'))
    if not admin_only():
        return "Access denied! (Admin Only)", 403
    if request.method == 'POST':
        nama = request.form.get('nama_kategori')
        habitat = request.form.get('habitat')
        deskripsi = request.form.get('deskripsi')
        KategoriIkan.create(nama, habitat, deskripsi)
        flash('Kategori berhasil ditambahkan', 'success')
        return redirect(url_for('index'))
    return render_template('insert_kategoriikan.html')

@app.route('/kategori/update/<int:id_kategori>', methods=['GET', 'POST'])
def form_kategori_update(id_kategori):
    if not login_required():
        return redirect(url_for('login'))
    if not admin_only():
        return "Access denied! (Admin Only)", 403
    if request.method == 'POST':
        nama = request.form.get('nama_kategori')
        habitat = request.form.get('habitat')
        deskripsi = request.form.get('deskripsi')
        KategoriIkan.update(id_kategori, nama, habitat, deskripsi)
        flash('Kategori diperbarui', 'success')
        return redirect(url_for('index'))
    data = KategoriIkan.get_by_id(id_kategori)
    return render_template('update_kategoriikan.html', data=data)

@app.route('/kategori/delete/<int:id_kategori>')
def kategori_delete(id_kategori):
    if not login_required():
        return redirect(url_for('login'))
    if not admin_only():
        return "Access denied! (Admin Only)", 403
    KategoriIkan.delete(id_kategori)
    flash('Kategori dihapus', 'info')
    return redirect(url_for('index'))

# Ikan: any logged-in user dapat menambah; edit/hapus oleh owner atau admin
@app.route('/ikan/insert', methods=['GET', 'POST'])
def form_ikan_insert():
    if not login_required():
        return redirect(url_for('login'))
    kategori = KategoriIkan.get_all()
    if request.method == 'POST':
        nama = request.form.get('nama_ikan')
        id_ktgr = request.form.get('id_kategori')
        harga = request.form.get('harga') or 0
        stok = request.form.get('stok') or 0
        # simpan user_id sebagai pembuat
        DaftarIkan.create(nama, id_ktgr, harga, stok, session['user_id'])
        flash('Ikan berhasil ditambahkan', 'success')
        return redirect(url_for('index'))
    return render_template('insert_daftarikan.html', kategori=kategori)

@app.route('/ikan/update/<int:id_ikan>', methods=['GET', 'POST'])
def form_ikan_update(id_ikan):
    if not login_required():
        return redirect(url_for('login'))
    data = DaftarIkan.get_by_id(id_ikan)
    if not data:
        return "Not found", 404
    # otorisasi: owner atau admin
    if session.get('role') != 'admin' and data.get('user_id') != session.get('user_id'):
        return "Access denied!", 403
    if request.method == 'POST':
        nama = request.form.get('nama_ikan')
        id_ktgr = request.form.get('id_kategori')
        harga = request.form.get('harga') or 0
        stok = request.form.get('stok') or 0
        DaftarIkan.update(id_ikan, nama, id_ktgr, harga, stok)
        flash('Data ikan diperbarui', 'success')
        return redirect(url_for('index'))
    kategori = KategoriIkan.get_all()
    return render_template('update_daftarikan.html', data=data, kategori=kategori)

@app.route('/ikan/delete/<int:id_ikan>')
def ikan_delete(id_ikan):
    if not login_required():
        return redirect(url_for('login'))
    data = DaftarIkan.get_by_id(id_ikan)
    if not data:
        return "Not found", 404
    if session.get('role') != 'admin' and data.get('user_id') != session.get('user_id'):
        return "Access denied!", 403
    DaftarIkan.delete(id_ikan)
    flash('Ikan dihapus', 'info')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if not login_required():
        return redirect(url_for('login'))
    if not admin_only():
        return "Only admins can add new users", 403
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role') or 'kasir'
        User.create(username, password, role)
        flash('User baru berhasil dibuat', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

# Users list (admin)
@app.route('/users')
def users_list():
    if not login_required():
        return redirect(url_for('login'))
    if not admin_only():
        return "Access denied! (Admin Only)", 403
    users = User.get_all()
    return render_template('users_list.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)