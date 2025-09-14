from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

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

@app.before_first_request
def create_tables():
    db.create_all()
    # create default admin user if not exists
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password='12345'))
        db.session.commit()
    # create example data if empty
    if not Marka.query.first():
        m = Marka(ad='Örnek Marka', logo_url='/static/logo.png')
        db.session.add(m)
        db.session.commit()
        a = AnahtarTip(tip='Örnek Anahtar', marka_id=m.id, fiyat=150.0)
        db.session.add(a)
        db.session.add(FiyatHareketi(anahtar_id=a.id, eski_fiyat=0.0, yeni_fiyat=150.0))
        db.session.commit()

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
    hareketler = anahtar.fiyat_hareketleri[:20]
    return render_template('fiyat_gecmisi.html', anahtar=anahtar, hareketler=hareketler)

if __name__ == '__main__':
    app.run(debug=True)