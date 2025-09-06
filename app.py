from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///veritabani.db'
db = SQLAlchemy(app)

class Marka(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ad = db.Column(db.String(50), nullable=False)
    anahtarlar = db.relationship('AnahtarTip', backref='marka', cascade="all, delete-orphan")

class AnahtarTip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tip = db.Column(db.String(50), nullable=False)
    marka_id = db.Column(db.Integer, db.ForeignKey('marka.id'), nullable=False)

class Stok(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    marka_id = db.Column(db.Integer, db.ForeignKey('marka.id'), nullable=False)
    anahtar_id = db.Column(db.Integer, db.ForeignKey('anahtar_tip.id'), nullable=False)
    miktar = db.Column(db.Integer, default=0)
    treshold = db.Column(db.Integer, default=5)
    marka = db.relationship('Marka')
    anahtar = db.relationship('AnahtarTip')

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def ana_sayfa():
    stoklar = Stok.query.all()
    uyarilar = []
    for s in stoklar:
        if s.miktar <= s.treshold:
            uyarilar.append(f"{s.marka.ad} - {s.anahtar.tip}: Stok Azaldı! ({s.miktar} adet)")
    return render_template('index.html', uyarilar=uyarilar)

@app.route('/stok', methods=['GET', 'POST'])
def stok():
    if request.method == 'POST':
        marka_id = int(request.form['marka_id'])
        anahtar_id = int(request.form['anahtar_id'])
        miktar = int(request.form['miktar'])
        treshold = int(request.form['treshold'])
        stok_kalemi = Stok.query.filter_by(marka_id=marka_id, anahtar_id=anahtar_id).first()
        if stok_kalemi:
            stok_kalemi.miktar += miktar
            stok_kalemi.treshold = treshold
        else:
            stok_kalemi = Stok(marka_id=marka_id, anahtar_id=anahtar_id, miktar=miktar, treshold=treshold)
            db.session.add(stok_kalemi)
        db.session.commit()
        return redirect(url_for('stok'))
    stoklar = Stok.query.all()
    markalar = Marka.query.all()
    anahtarlar = AnahtarTip.query.all()
    return render_template('stok.html', stoklar=stoklar, markalar=markalar, anahtarlar=anahtarlar)

@app.route('/stok/cikart/<int:stok_id>', methods=['POST'])
def stok_cikart(stok_id):
    stok_kalemi = Stok.query.get_or_404(stok_id)
    miktar = int(request.form['miktar'])
    stok_kalemi.miktar = max(stok_kalemi.miktar - miktar, 0)
    db.session.commit()
    return redirect(url_for('stok'))

@app.route('/markalar', methods=['GET', 'POST'])
def markalar():
    if request.method == 'POST':
        marka_adi = request.form['marka']
        if marka_adi.strip():
            yeni_marka = Marka(ad=marka_adi.strip())
            db.session.add(yeni_marka)
            db.session.commit()
        return redirect(url_for('markalar'))
    markalar = Marka.query.all()
    return render_template('markalar.html', markalar=markalar)

@app.route('/anahtar/ekle/<int:marka_id>', methods=['POST'])
def anahtar_ekle(marka_id):
    tip = request.form['tip'].strip()
    if tip:
        db.session.add(AnahtarTip(tip=tip, marka_id=marka_id))
        db.session.commit()
    return redirect(url_for('markalar'))

@app.route('/anahtar/sil/<int:anahtar_id>', methods=['POST'])
def anahtar_sil(anahtar_id):
    anahtar = AnahtarTip.query.get_or_404(anahtar_id)
    db.session.delete(anahtar)
    db.session.commit()
    return redirect(url_for('markalar'))

@app.route('/marka/sil/<int:marka_id>', methods=['POST'])
def marka_sil(marka_id):
    marka = Marka.query.get_or_404(marka_id)
    db.session.delete(marka)
    db.session.commit()
    return redirect(url_for('markalar'))

@app.route('/gelir-gider', methods=['GET'])
def gelir_gider():
    hareketler = []
    return render_template('gelir_gider.html', hareketler=hareketler)

@app.route('/gelir-gider/ekle', methods=['POST'])
def gelir_gider_ekle():
    return redirect('/gelir-gider')

if __name__ == '__main__':
    app.run(debug=True)
