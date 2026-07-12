from flask import Flask, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)

# ===== CHANGE THESE =====
ADMIN_USERNAME = 'deu'
ADMIN_PASSWORD = 'deu'
# =======================

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
    name = db.Column(db.String(255), default="Unnamed")
    is_used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.String(255))
    used_ip = db.Column(db.String(45))
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
    return '''<!DOCTYPE html><html><head><title>KeyAuth</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;display:flex;justify-content:center;align-items:center;min-height:100vh;color:#fff}.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:40px;width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{font-size:2.5em;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}.form-group{margin-bottom:20px}label{display:block;margin-bottom:8px;color:#bbb}input{width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;margin-bottom:10px}.btn{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer;font-weight:600;margin-top:10px}.btn:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(102,126,234,0.4)}.message{padding:12px;border-radius:5px;margin-bottom:20px;display:none}.message.error{background:rgba(244,67,54,0.2);color:#f44336}.message.success{background:rgba(76,175,80,0.2);color:#4caf50}</style></head><body><div class="card"><div class="logo"><h1>🔑 KeyAuth</h1></div><div class="message" id="msg"></div><form id="form"><div class="form-group"><label>Username</label><input type="text" id="u" required></div><div class="form-group"><label>Password</label><input type="password" id="p" required></div><button class="btn" type="submit">Login</button></form></div><script>document.getElementById("form").addEventListener("submit",async e=>{e.preventDefault();const r=await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:document.getElementById("u").value,password:document.getElementById("p").value})}),d=await r.json();d.success?window.location.href="/dashboard":(document.getElementById("msg").textContent="✗ "+d.message,document.getElementById("msg").className="message error",document.getElementById("msg").style.display="block")});</script></body></html>'''

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    return '''<!DOCTYPE html><html><head><title>Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;color:#fff;min-height:100vh;padding:20px}.navbar{background:rgba(0,0,0,0.3);padding:20px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center}.navbar h1{font-size:1.8em}.container{max-width:1200px;margin:0 auto}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;margin-bottom:30px}.stat{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);padding:20px;border-radius:10px;text-align:center}.stat-num{font-size:2.5em;font-weight:bold;color:#667eea}.section{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:30px;margin-bottom:30px}.section h2{margin-bottom:20px}.form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;color:#aaa}input{width:100%;padding:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;margin-bottom:10px}.btn{padding:10px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer;font-weight:600}.btn:hover{transform:translateY(-2px)}.btn-danger{background:linear-gradient(135deg,#f44336 0%,#d32f2f 100%)}.btn-small{padding:5px 10px;font-size:0.85em;margin:5px 2px}.output{background:rgba(0,0,0,0.3);padding:15px;margin-top:15px;border-radius:5px;max-height:300px;overflow-y:auto;display:none}.table{width:100%;border-collapse:collapse;margin-top:15px}.table th,.table td{padding:10px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);font-size:0.9em}.table th{background:rgba(255,255,255,0.05)}</style></head><body><div class="navbar"><h1>🔑 Dashboard</h1><a onclick="window.location.href=\\'/logout\\'" style="color:#667eea;cursor:pointer">Logout</a></div><div class="container"><div class="stats"><div class="stat"><div class="stat-num" id="t">0</div>Total</div><div class="stat"><div class="stat-num" id="u">0</div>Used</div><div class="stat"><div class="stat-num" id="a">0</div>Available</div><div class="stat"><div class="stat-num" id="b">0</div>Banned</div></div><div class="section"><h2>Generate Keys</h2><div class="form-group"><label>Key Name</label><input type="text" id="n" placeholder="Customer A"></div><div class="form-group"><label>Days</label><input type="number" id="d" value="30"></div><div class="form-group"><label>Max Uses</label><input type="number" id="m" value="1"></div><div class="form-group"><label>Quantity</label><input type="number" id="q" value="1"></div><button class="btn" onclick="gen()">Generate</button><button class="btn" onclick="copy()" style="margin-left:10px">Copy All</button><div class="output" id="o"></div></div><div class="section"><h2>All Keys</h2><button class="btn" onclick="load()">Load Keys</button><div id="k"></div></div></div><script>async function gen(){const r=await fetch("/api/generate-key",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:document.getElementById("n").value||"Unnamed",days_valid:document.getElementById("d").value,max_uses:document.getElementById("m").value,quantity:document.getElementById("q").value})}),d=await r.json();if(d.success){document.getElementById("o").innerHTML=d.keys.map(x=>`<div style="background:rgba(76,175,80,0.2);padding:8px;margin:5px 0;border-radius:3px">${x.name}<br><code>${x.key}</code></div>`).join(""),document.getElementById("o").style.display="block",stats(),load()}else alert("Error: "+(d.error||"Unknown"))}async function stats(){const r=await fetch("/api/stats"),d=await r.json();document.getElementById("t").textContent=d.total,document.getElementById("u").textContent=d.used,document.getElementById("a").textContent=d.available,document.getElementById("b").textContent=d.banned}async function load(){const r=await fetch("/api/all-keys"),d=await r.json();if(d.success){let h="<table class=\\"table\\"><tr><th>Name</th><th>Key</th><th>Status</th><th>Used By</th><th>IP</th><th>Expires</th><th>Actions</th></tr>";d.keys.forEach(x=>{const s=x.banned?"BANNED":x.used?"USED":"ACTIVE";h+=`<tr><td>${x.name}</td><td style="font-size:0.8em;font-family:monospace">${x.key}</td><td>${s}</td><td>${x.used_by||"-"}</td><td>${x.used_ip||"-"}</td><td>${x.expires}</td><td><button class="btn btn-small" onclick="ext(\\'${x.key}\\')">+Days</button><button class="btn btn-small btn-danger" onclick="ban(\\'${x.key}\\')">Ban</button></td></tr>`}),h+="</table>",document.getElementById("k").innerHTML=h}else alert("Error")}async function ban(key){if(confirm("Ban this key?")){const r=await fetch("/api/revoke-key",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:key})}),d=await r.json();d.success?(alert("✓ Banned"),load(),stats()):alert("Error: "+d.error)}}async function ext(key){const days=prompt("Add days:");if(days){const r=await fetch("/api/update-expiry",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:key,days:days})}),d=await r.json();d.success?(alert("✓ Extended"),load(),stats()):alert("Error: "+d.error)}}function copy(){const keys=document.querySelectorAll("code");let t="";keys.forEach(k=>t+=k.innerText+"\\n"),navigator.clipboard.writeText(t),alert("Copied!")}stats(),load();</script></body></html>'''

@app.route('/api/generate-key', methods=['POST'])
def api_generate_key():
    try:
        if 'admin_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        data = request.get_json() or {}
        name = str(data.get('name', 'Unnamed'))
        days = int(data.get('days_valid', 30))
        max_uses = int(data.get('max_uses', 1))
        qty = int(data.get('quantity', 1))
        
        keys = []
        for _ in range(min(qty, 100)):
            k = generate_license_key()
            exp = datetime.utcnow() + timedelta(days=days)
            key_obj = LicenseKey(key=k, name=name, expires_date=exp, max_uses=max_uses)
            db.session.add(key_obj)
            keys.append({'key': k, 'name': name})
        
        db.session.commit()
        return jsonify({'success': True, 'keys': keys}), 201
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def api_stats():
    total = LicenseKey.query.count()
    used = LicenseKey.query.filter_by(is_used=True).count()
    banned = LicenseKey.query.filter_by(is_banned=True).count()
    return jsonify({'total': total, 'used': used, 'available': total - used, 'banned': banned})

@app.route('/api/all-keys')
def api_all_keys():
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    keys = LicenseKey.query.order_by(LicenseKey.created_date.desc()).all()
    return jsonify({'success': True, 'keys': [{'name': k.name, 'key': k.key, 'used': k.is_used, 'used_by': k.used_by, 'used_ip': k.used_ip, 'banned': k.is_banned, 'expires': k.expires_date.strftime('%Y-%m-%d')} for k in keys]})

@app.route('/api/revoke-key', methods=['POST'])
def api_revoke_key():
    try:
        if 'admin_id' not in session:
            return jsonify({'success': False}), 401
        data = request.get_json()
        key = LicenseKey.query.filter_by(key=data.get('key')).first()
        if not key:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        key.is_banned = True
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/update-expiry', methods=['POST'])
def api_update_expiry():
    try:
        if 'admin_id' not in session:
            return jsonify({'success': False}), 401
        data = request.get_json()
        key = LicenseKey.query.filter_by(key=data.get('key')).first()
        if not key:
            return jsonify({'success': False, 'error': 'Not found'}), 404
        key.expires_date = datetime.utcnow() + timedelta(days=int(data.get('days', 30)))
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/validate-key', methods=['POST'])
def api_validate_key():
    data = request.get_json()
    key = LicenseKey.query.filter_by(key=data.get('key')).first()
    
    if not key:
        return jsonify({'success': False, 'message': 'Not found'}), 404
    if key.is_banned:
        return jsonify({'success': False, 'message': 'Banned'}), 403
    if key.current_uses >= key.max_uses:
        return jsonify({'success': False, 'message': 'Limit'}), 403
    if key.expires_date < datetime.utcnow():
        return jsonify({'success': False, 'message': 'Expired'}), 403
    
    key.is_used = True
    key.used_by = data.get('username', 'Unknown')
    key.used_ip = request.remote_addr
    key.current_uses += 1
    db.session.commit()
    
    return jsonify({'success': True}), 200

if __name__ == '__main__':
    with app.app_context():
        try:
            db.drop_all()
        except:
            pass
        db.create_all()
        if not Admin.query.filter_by(username=ADMIN_USERNAME).first():
            admin = Admin(username=ADMIN_USERNAME, password=generate_password_hash(ADMIN_PASSWORD))
            db.session.add(admin)
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
