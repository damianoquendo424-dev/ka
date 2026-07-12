from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)
app.config['SECRET_KEY'] = 'deu-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class LicenseKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(25), unique=True, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    expires_date = db.Column(db.DateTime)
    max_uses = db.Column(db.Integer, default=1)
    current_uses = db.Column(db.Integer, default=0)
    is_banned = db.Column(db.Boolean, default=False)

def generate_license_key():
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))
        parts.append(part)
    return '-'.join(parts)

@app.route('/')
def index():
    if 'admin_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return jsonify({'success': True}), 200
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/generate-key', methods=['POST'])
def api_generate_key():
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    data = request.get_json()
    days = data.get('days_valid', 30)
    max_uses = data.get('max_uses', 1)
    qty = data.get('quantity', 1)

    keys = []
    for _ in range(min(qty, 100)):
        k = generate_license_key()
        exp = datetime.utcnow() + timedelta(days=days)
        key_obj = LicenseKey(key=k, expires_date=exp, max_uses=max_uses)
        db.session.add(key_obj)
        keys.append(k)

    db.session.commit()
    return jsonify({'success': True, 'keys': keys}), 201

@app.route('/api/stats')
def api_stats():
    total = LicenseKey.query.count()
    used = LicenseKey.query.filter_by(is_used=True).count()
    banned = LicenseKey.query.filter_by(is_banned=True).count()
    return jsonify({'total': total, 'used': used, 'available': total - used, 'banned': banned})

@app.route('/api/validate-key', methods=['POST'])
def api_validate_key():
    data = request.get_json()
    key_str = data.get('key')
    key = LicenseKey.query.filter_by(key=key_str).first()

    if not key:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    if key.is_banned:
        return jsonify({'success': False, 'message': 'Banned'}), 403
    if key.current_uses >= key.max_uses:
        return jsonify({'success': False, 'message': 'Limit'}), 403
    if key.expires_date < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Expired'}), 403

    return jsonify({'success': True}), 200

@app.route('/api/redeem-key', methods=['POST'])
def api_redeem_key():
    data = request.get_json()
    key_str = data.get('key')
    username = data.get('username')
    hwid = data.get('hwid')

    key = LicenseKey.query.filter_by(key=key_str).first()

    if not key:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    if key.is_banned:
        return jsonify({'success': False, 'message': 'Banned'}), 403
    if key.current_uses >= key.max_uses:
        return jsonify({'success': False, 'message': 'Limit'}), 403
    if key.expires_date < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Expired'}), 403

    key.is_used = True
    key.used_by = username or f"User_{key_str[:8]}"
    key.current_uses += 1
    db.session.commit()

    return jsonify({'success': True, 'token': secrets.token_urlsafe(32)}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='deu').first():
            admin = Admin(username='deu', password=generate_password_hash('deu'))
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True, host='0.0.0.0', port=5000)
