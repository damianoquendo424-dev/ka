from flask import Flask, request, jsonify, session, redirect, url_for
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

    return '''<!DOCTYPE html><html><head><title>KeyAuth</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI,Tahoma;display:flex;justify-content:center;align-items:center;min-height:100vh;color:#fff}.container{width:100%;max-width:400px;padding:20px}.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:40px;backdrop-filter:blur(10px)}.logo{text-align:center;margin-bottom:30px}.logo h1{font-size:2.5em;font-weight:bold;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}.logo p{color:#aaa;font-size:0.9em}.form-group{margin-bottom:20px}label{display:block;margin-bottom:8px;font-size:0.9em;color:#bbb;font-weight:500}input[type="text"],input[type="password"]{width:100%;padding:12px 15px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;font-size:1em;transition:all 0.3s ease}.btn{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;font-size:1em;font-weight:600;cursor:pointer;transition:all 0.3s ease;margin-top:10px}.btn:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(102,126,234,0.4)}.message{padding:12px;border-radius:5px;margin-bottom:20px;text-align:center;font-size:0.9em;display:none}.message.success{background:rgba(76,175,80,0.2);color:#4caf50}.message.error{background:rgba(244,67,54,0.2);color:#f44336}</style></head><body><div class="container"><div class="card"><div class="logo"><h1>🔑 KeyAuth</h1><p>License Key Management</p></div><div class="message" id="message"></div><form id="loginForm"><div class="form-group"><label>Username</label><input type="text" id="username" required></div><div class="form-group"><label>Password</label><input type="password" id="password" required></div><button type="submit" class="btn">Login</button></form><div style="text-align:center;margin-top:20px;font-size:0.9em;color:#aaa">Default: deu / deu</div></div></div><script>document.getElementById("loginForm").addEventListener("submit",async(e)=>{e.preventDefault();const u=document.getElementById("username").value,p=document.getElementById("password").value;try{const r=await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:u,password:p})}),d=await r.json();d.success?(document.getElementById("message").textContent="✓ Logged in!",document.getElementById("message").className="message success",document.getElementById("message").style.display="block",setTimeout(()=>window.location.href="/dashboard",1500)):(document.getElementById("message").textContent="✗ "+d.message,document.getElementById("message").className="message error",document.getElementById("message").style.display="block")}catch(e){document.getElementById("message").textContent="✗ Error",document.getElementById("message").className="message error",document.getElementById("message").style.display="block"}});</script></body></html>'''

@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))

    return '''<!DOCTYPE html><html><head><title>KeyAuth Dashboard</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;color:#fff;min-height:100vh;padding:20px}.navbar{background:rgba(0,0,0,0.3);border-bottom:1px solid rgba(255,255,255,0.1);padding:20px 40px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center}.navbar h1{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:1.8em}.navbar a{color:#667eea;text-decoration:none;cursor:pointer}.container{max-width:1200px;margin:0 auto}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:20px;margin-bottom:40px}.stat-card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:20px;text-align:center}.stat-card h3{color:#aaa;font-size:0.9em;margin-bottom:10px}.stat-card .number{font-size:2.5em;font-weight:bold;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}.section{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:30px;margin-bottom:30px}.section h2{margin-bottom:20px;font-size:1.5em}.form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;color:#aaa}.form-group input{width:100%;padding:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;margin-bottom:10px}.btn{padding:10px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer;font-weight:600;transition:all 0.3s ease}.btn:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(102,126,234,0.4)}.btn-small{padding:5px 10px;font-size:0.85em;margin:5px 2px}.btn-danger{background:linear-gradient(135deg,#f44336 0%,#d32f2f 100%)}.key-output{background:rgba(0,0,0,0.3);border:1px solid rgba(255,255,255,0.1);border-radius:5px;padding:15px;margin-top:15px;word-break:break-all;font-family:monospace;font-size:0.9em;max-height:300px;overflow-y:auto;display:none}.key-item{background:rgba(76,175,80,0.2);padding:10px;margin:8px 0;border-radius:3px;border-left:3px solid #4caf50}.key-name{font-weight:bold;color:#fff;margin-bottom:5px}.key-value{color:#aaa;font-size:0.85em}.message{padding:12px;border-radius:5px;margin-bottom:20px;display:none}.message.success{background:rgba(76,175,80,0.2);color:#4caf50}.message.error{background:rgba(244,67,54,0.2);color:#f44336}.key-table{width:100%;border-collapse:collapse;margin-top:15px}.key-table th,.key-table td{padding:10px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);font-size:0.9em}.key-table th{background:rgba(255,255,255,0.05);font-weight:bold}.key-table tr:hover{background:rgba(255,255,255,0.05)}</style></head><body><div class="navbar"><h1>🔑 KeyAuth Dashboard</h1><a onclick="window.location.href=\\'/logout\\'">Logout</a></div><div class="container"><div class="stats"><div class="stat-card"><h3>Total Keys</h3><div class="number" id="totalKeys">0</div></div><div class="stat-card"><h3>Used</h3><div class="number" id="usedKeys">0</div></div><div class="stat-card"><h3>Available</h3><div class="number" id="availableKeys">0</div></div><div class="stat-card"><h3>Banned</h3><div class="number" id="bannedKeys">0</div></div></div><div class="section"><h2>Generate Keys</h2><div class="message" id="message"></div><div class="form-group"><label>Key Name</label><input type="text" id="keyName" placeholder="e.g., Customer A"></div><div class="form-group"><label>Days Valid</label><input type="number" id="daysValid" value="30" min="1" max="365"></div><div class="form-group"><label>Max Uses</label><input type="number" id="maxUses" value="1" min="1" max="10"></div><div class="form-group"><label>Quantity</label><input type="number" id="quantity" value="1" min="1" max="100"></div><button class="btn" onclick="generateKeys()">Generate</button><button class="btn" onclick="copyAllKeys()" style="margin-left:10px">Copy All</button><div class="key-output" id="keyOutput"></div></div><div class="section"><h2>All Keys</h2><button class="btn" onclick="loadAllKeys()">Load All Keys</button><div id="allKeysContainer"></div></div></div><script>async function generateKeys(){const name=document.getElementById("keyName").value||"Unnamed",days=document.getElementById("daysValid").value,uses=document.getElementById("maxUses").value,qty=document.getElementById("quantity").value;try{const r=await fetch("/api/generate-key",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:name,days_valid:days,max_uses:uses,quantity:qty})}),d=await r.json();if(d.success){document.getElementById("message").textContent="✓ Keys generated!",document.getElementById("message").className="message success",document.getElementById("message").style.display="block";let html=d.keys.map(k=>`<div class="key-item"><div class="key-name">${k.name}</div><div class="key-value">${k.key}</div></div>`).join("");document.getElementById("keyOutput").innerHTML=html,document.getElementById("keyOutput").style.display="block",loadStats(),loadAllKeys()}else document.getElementById("message").textContent="✗ "+(d.error||d.message||"Error"),document.getElementById("message").className="message error",document.getElementById("message").style.display="block"}catch(e){document.getElementById("message").textContent="✗ "+e.message,document.getElementById("message").className="message error",document.getElementById("message").style.display="block"}}async function loadStats(){try{const r=await fetch("/api/stats"),d=await r.json();document.getElementById("totalKeys").textContent=d.total,document.getElementById("usedKeys").textContent=d.used,document.getElementById("availableKeys").textContent=d.available,document.getElementById("bannedKeys").textContent=d.banned}catch(e){console.error(e)}}async function loadAllKeys(){try{const r=await fetch("/api/all-keys"),d=await r.json();if(d.success){let html="<table class=\\"key-table\\"><tr><th>Name</th><th>Key</th><th>Status</th><th>Used By</th><th>IP</th><th>Expires</th><th>Actions</th></tr>";d.keys.forEach(k=>{const status=k.banned?"BANNED":k.used?"USED":"ACTIVE";html+=`<tr><td>${k.name}</td><td style="font-family:monospace;font-size:0.8em">${k.key}</td><td>${status}</td><td>${k.used_by||"-"}</td><td>${k.used_ip||"-"}</td><td>${k.expires}</td><td><button class="btn btn-small" onclick="updateKeyExpiry(\\'${k.key}\\')">Extend</button><button class="btn btn-small btn-danger" onclick="revokeKey(\\'${k.key}\\')">Revoke</button></td></tr>`}),html+="</table>",document.getElementById("allKeysContainer").innerHTML=html}else alert("Error loading keys")}catch(e){alert("Error: "+e.message)}}async function revokeKey(key){if(confirm("Ban this key?")){try{const r=await fetch("/api/revoke-key",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:key})}),d=await r.json();d.success?(alert("✓ Key banned"),loadAllKeys(),loadStats()):(alert("✗ Error: "+d.error),loadAllKeys())}catch(e){alert("Error: "+e.message)}}}async function updateKeyExpiry(key){const days=prompt("Add how many days?");if(days){try{const r=await fetch("/api/update-expiry",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({key:key,days:days})}),d=await r.json();d.success?(alert("✓ Expiry updated"),loadAllKeys(),loadStats()):(alert("✗ Error: "+d.error),loadAllKeys())}catch(e){alert("Error: "+e.message)}}}function copyAllKeys(){const keys=document.querySelectorAll(".key-value");let text="";keys.forEach(k=>text+=k.innerText+"\\n"),navigator.clipboard.writeText(text),alert("Copied!")}loadStats();</script></body></html>'''

@app.route('/api/generate-key', methods=['POST'])
def api_generate_key():
    try:
        if 'admin_id' not in session:
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
        data = request.get_json() or {}
        days = int(data.get('days_valid', 30))
        max_uses = int(data.get('max_uses', 1))
        qty = int(data.get('quantity', 1))
        name = str(data.get('name', 'Unnamed'))

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
        key_str = data.get('key')
        key = LicenseKey.query.filter_by(key=key_str).first()
        if not key:
            return jsonify({'success': False, 'error': 'Key not found'}), 404
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
        key_str = data.get('key')
        days = int(data.get('days', 30))
        key = LicenseKey.query.filter_by(key=key_str).first()
        if not key:
            return jsonify({'success': False, 'error': 'Key not found'}), 404
        key.expires_date = datetime.utcnow() + timedelta(days=days)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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
        if not Admin.query.filter_by(username='deu').first():
            admin = Admin(username='deu', password=generate_password_hash('deu'))
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True, host='0.0.0.0', port=5000)
