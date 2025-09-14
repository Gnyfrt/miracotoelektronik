from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
MAX_IMAGE_DIM = (800, 800)  # max width, height for uploaded images
THUMBNAIL_SIZE = (240, 240)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'logos')

# ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # plain for demo only

class Marka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(100), nullable=False)
    logo_url = db.Column(db.String(255), nullable=True)
    anahtarlar = db.relationship('AnahtarTip', backref='marka', cascade='all,delete')

class AnahtarTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tip = db.Column(db.String(100), nullable=False)
    marka_id = db.Column(db.Integer, db.ForeignKey('marka.id'), nullable=False)
    fiyat = db.Column(db.Float, default=0.0)
    fiyat_hareketleri = db.relationship('FiyatHareketi', backref='anahtar', cascade='all,delete', order_by='FiyatHareketi.tarih.desc()')

class FiyatHareketi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    anahtar_id = db.Column(db.Integer, db.ForeignKey('anahtar_tip.id'), nullable=False)
    eski_fiyat = db.Column(db.Float)
    yeni_fiyat = db.Column(db.Float)
    tarih = db.Column(db.DateTime, default=datetime.utcnow)

# Simple auth helpers (demo)
def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapped


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def resize_image(src_path, dest_path, max_dim=MAX_IMAGE_DIM):
    try:
        with Image.open(src_path) as im:
            im.thumbnail(max_dim, Image.LANCZOS)
            # ensure RGBA for PNG
            if im.mode in ("RGBA", "LA"):
                background = Image.new("RGBA", im.size)
                background.paste(im, (0,0), im)
                background.save(dest_path, optimize=True)
            else:
                im.convert('RGBA').save(dest_path, optimize=True)
        return True
    except Exception as e:
        print('resize_image error:', e)
        return False


def create_thumbnail(src_path, dest_path, size=THUMBNAIL_SIZE):
    try:
        with Image.open(src_path) as im:
            im.thumbnail(size, Image.LANCZOS)
            im.convert('RGBA').save(dest_path, optimize=True)
        return True
    except Exception as e:
        print('create_thumbnail error:', e)
        return False


def create_tables_and_seed():
    """
    Create DB tables and seed minimal demo data.
    Called at import time inside app.app_context() to avoid relying on
    app.before_first_request (which may not exist on some setups).
    """
    with app.app_context():
        db.create_all()
        # create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            db.session.add(User(username='admin', password='12345'))
            db.session.commit()

        # create example brands if empty — top ~30 commonly seen brands in Turkey (automotive/electronics mix)
        if not Marka.query.first():
            brands = [
                'Renault','Fiat','Ford','Volkswagen','Toyota','Hyundai','Opel','Mercedes-Benz','BMW','Audi',
                'Honda','Nissan','Peugeot','Citroën','Skoda','Seat','Dacia','Mitsubishi','Kia','Isuzu',
                'Suzuki','Lexus','Porsche','Subaru','Mini','Jaguar','Land Rover','Volvo','Tesla','Alfa Romeo'
            ]
            for i, name in enumerate(brands, start=1):
                slug = name.lower().replace(' ', '_').replace('ç','c').replace('ğ','g').replace('ü','u').replace('ş','s').replace('ö','o').replace('ı','i')
                logo_path = f"/static/logos/{slug}.svg"  # prefer svg from simple-icons
                db.session.add(Marka(ad=name, logo_url=logo_path))
            db.session.commit()

# Call at import so it runs under flask run as well as when __main__.
create_tables_and_seed()

# Routes
@app.route('/')
@login_required
def dashboard():
    markalar = Marka.query.all()
    return render_template('dashboard.html', markalar=markalar)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        flash('Geçersiz kullanıcı adı veya şifre','danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/markalar', methods=['GET','POST'])
@login_required
def markalar():
    if request.method == 'POST':
        ad = request.form['marka']
        logo_url = request.form.get('logo_url') or '/static/logo.png'
        m = Marka(ad=ad, logo_url=logo_url)
        db.session.add(m)
        db.session.commit()
        return redirect(url_for('markalar'))
    markalar = Marka.query.all()
    return render_template('markalar.html', markalar=markalar)

@app.route('/upload-logo/<int:marka_id>', methods=['POST'])
@login_required
def upload_logo(marka_id):
    m = Marka.query.get_or_404(marka_id)
    if 'logo' not in request.files:
        flash('Logo dosyası bulunamadı','danger')
        return redirect(url_for('markalar'))
    file = request.files['logo']
    if file.filename == '':
        flash('Dosya seçilmedi','danger')
        return redirect(url_for('markalar'))
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        dest_name = f"{marka_id}_{filename}"
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], dest_name)
        # Save original first
        file.save(save_path)
        # If SVG, keep as is; otherwise resize & create thumbnail
        if ext == 'svg':
            m.logo_url = f"/static/logos/{dest_name}"
            db.session.commit()
            flash('SVG logo yüklendi','success')
            return redirect(url_for('markalar'))
        # For raster images, resize and save optimized PNG
        try:
            optimized_name = f"{marka_id}_{os.path.splitext(filename)[0]}.png"
            optimized_path = os.path.join(app.config['UPLOAD_FOLDER'], optimized_name)
            ok = resize_image(save_path, optimized_path)
            if ok:
                thumb_name = f"thumb_{optimized_name}"
                thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_name)
                create_thumbnail(optimized_path, thumb_path)
                # remove original uploaded file to save space
                try:
                    os.remove(save_path)
                except Exception:
                    pass
                m.logo_url = f"/static/logos/{optimized_name}"
                db.session.commit()
                flash('Logo yüklendi ve optimize edildi','success')
            else:
                flash('Görsel işlenirken hata oluştu','danger')
        except Exception as e:
            print('upload error:', e)
            flash('Dosya kaydedilirken hata oluştu','danger')
    else:
        flash('Geçersiz dosya türü','danger')
    return redirect(url_for('markalar'))

@app.route('/marka-sil/<int:marka_id>', methods=['POST'])
@login_required
def marka_sil(marka_id):
    m = Marka.query.get_or_404(marka_id)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for('markalar'))

@app.route('/anahtar-ekle/<int:marka_id>', methods=['POST'])
@login_required
def anahtar_ekle(marka_id):
    tip = request.form['tip']
    a = AnahtarTip(tip=tip, marka_id=marka_id, fiyat=0.0)
    db.session.add(a)
    db.session.commit()
    return redirect(url_for('markalar'))

@app.route('/anahtar-sil/<int:anahtar_id>', methods=['POST'])
@login_required
def anahtar_sil(anahtar_id):
    a = AnahtarTip.query.get_or_404(anahtar_id)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for('markalar'))

@app.route('/fiyatlar')
@login_required
def fiyatlar():
    anahtarlar = AnahtarTip.query.all()
    return render_template('fiyatlar.html', anahtarlar=anahtarlar)

@app.route('/fiyat-guncelle/<int:anahtar_id>', methods=['POST'])
@login_required
def fiyat_guncelle(anahtar_id):
    anahtar = AnahtarTip.query.get_or_404(anahtar_id)
    try:
        yeni_fiyat = float(request.form['yeni_fiyat'])
    except ValueError:
        flash('Geçerli bir fiyat girin','danger')
        return redirect(url_for('fiyatlar'))
    eski = anahtar.fiyat
    anahtar.fiyat = yeni_fiyat
    hareket = FiyatHareketi(anahtar_id=anahtar.id, eski_fiyat=eski, yeni_fiyat=yeni_fiyat)
    db.session.add(hareket)
    db.session.commit()
    flash('Fiyat güncellendi','success')
    return redirect(url_for('fiyatlar'))

@app.route('/fiyat-gecmisi/<int:anahtar_id>')
@login_required
def fiyat_gecmisi(anahtar_id):
    anahtar = AnahtarTip.query.get_or_404(anahtar_id)
    hareketler = anahtar.fiyat_hareketleri[:100]
    # prepare arrays for chart
    tarihler = [h.tarih.strftime('%Y-%m-%d %H:%M:%S') for h in reversed(hareketler)]
    fiyatlar = [h.yeni_fiyat for h in reversed(hareketler)]
    return render_template('fiyat_gecmisi.html', anahtar=anahtar, hareketler=hareketler, tarihler=tarihler, fiyatlar=fiyatlar)

if __name__ == '__main__':
    app.run(debug=True)