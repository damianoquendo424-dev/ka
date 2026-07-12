from flask import Flask, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)

# ===== CHANGE THESE =====
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'admin'
# =======================

app.config['SECRET_KEY'] = 'secret-key-change-me'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

class AuthKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(25), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    hwid = db.Column(db.String(255))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    expires_date = db.Column(db.DateTime)
    is_banned = db.Column(db.Boolean, default=False)

def generate_key():
    parts = []
    for _ in range(4):
        part = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(5))
        parts.append(part)
    return '-'.join(parts)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        auth_key = AuthKey.query.filter_by(username=username).first()
        if auth_key and check_password_hash(auth_key.password, password):
            if auth_key.is_banned:
                return jsonify({'success': False, 'message': 'Key banned'}), 403
            if auth_key.expires_date < datetime.utcnow():
                return jsonify({'success': False, 'message': 'Key expired'}), 403
            session['user_id'] = auth_key.id
            return jsonify({'success': True}), 200

        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

    return '''<!DOCTYPE html><html><head><title>Login</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;display:flex;justify-content:center;align-items:center;min-height:100vh;color:#fff}.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:40px;width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{font-size:2.5em;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}.form-group{margin-bottom:20px}label{display:block;margin-bottom:8px;color:#bbb}input{width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;margin-bottom:10px}.btn{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer;font-weight:600;margin-top:10px}.btn:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(102,126,234,0.4)}.message{padding:12px;border-radius:5px;margin-bottom:20px;display:none}.message.error{background:rgba(244,67,54,0.2);color:#f44336}.message.success{background:rgba(76,175,80,0.2);color:#4caf50}</style></head><body><div class="card"><div class="logo"><h1>🔑 Login</h1></div><div class="message" id="msg"></div><form id="form"><div class="form-group"><label>Username</label><input type="text" id="u" placeholder="admin" required></div><div class="form-group"><label>Password</label><input type="password" id="p" placeholder="password" required></div><button class="btn" type="submit">Login</button></form></div><script>document.getElementById("form").addEventListener("submit",async e=>{e.preventDefault();const r=await fetch("/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:document.getElementById("u").value,password:document.getElementById("p").value})}),d=await r.json();d.success?(document.getElementById("msg").textContent="✓ Logged in!",document.getElementById("msg").className="message success",document.getElementById("msg").style.display="block",setTimeout(()=>window.location.href="/dashboard",1500)):(document.getElementById("msg").textContent="✗ "+d.message,document.getElementById("msg").className="message error",document.getElementById("msg").style.display="block")});</script></body></html>'''

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = AuthKey.query.get(session.get('user_id'))
    if not user:
        session.clear()
        return redirect(url_for('login'))

    return f'''<!DOCTYPE html><html><head><title>Dashboard</title><style>*{{margin:0;padding:0;box-sizing:border-box}}body{{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;color:#fff;min-height:100vh;padding:20px}}.navbar{{background:rgba(0,0,0,0.3);padding:20px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between;align-items:center}}.navbar h1{{font-size:1.8em}}.container{{max-width:1200px;margin:0 auto}}.section{{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:30px;margin-bottom:30px}}.section h2{{margin-bottom:20px}}.info{{padding:15px;background:rgba(102,126,234,0.2);border-radius:5px;margin:10px 0}}.btn{{padding:10px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer}}.btn:hover{{transform:translateY(-2px)}}</style></head><body><div class="navbar"><h1>🔑 Welcome {user.username}!</h1><a onclick="window.location.href=\\'/logout\\'" style="color:#667eea;cursor:pointer">Logout</a></div><div class="container"><div class="section"><h2>Your Account</h2><div class="info"><strong>Username:</strong> {user.username}</div><div class="info"><strong>Key:</strong> {user.key}</div><div class="info"><strong>Expires:</strong> {user.expires_date.strftime('%Y-%m-%d') if user.expires_date else 'Never'}</div><div class="info"><strong>Status:</strong> {'BANNED' if user.is_banned else 'ACTIVE'}</div></div></div></body></html>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return jsonify({'success': True}), 200
        return jsonify({'success': False, 'message': 'Invalid'}), 401

    if 'admin_id' not in session:
        return '''<!DOCTYPE html><html><head><title>Admin</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;display:flex;justify-content:center;align-items:center;min-height:100vh;color:#fff}.card{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:40px;width:400px}.logo{text-align:center;margin-bottom:30px}.logo h1{font-size:2.5em;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);background-clip:text;-webkit-background-clip:text;-webkit-text-fill-color:transparent}.form-group{margin-bottom:20px}label{display:block;margin-bottom:8px;color:#bbb}input{width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;margin-bottom:10px}.btn{width:100%;padding:12px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer;font-weight:600;margin-top:10px}.btn:hover{transform:translateY(-2px);box-shadow:0 5px 20px rgba(102,126,234,0.4)}.message{padding:12px;border-radius:5px;margin-bottom:20px;display:none}.message.error{background:rgba(244,67,54,0.2);color:#f44336}</style></head><body><div class="card"><div class="logo"><h1>🔑 Admin</h1></div><div class="message" id="msg"></div><form id="form"><div class="form-group"><label>Username</label><input type="text" id="u" required></div><div class="form-group"><label>Password</label><input type="password" id="p" required></div><button class="btn" type="submit">Login</button></form></div><script>document.getElementById("form").addEventListener("submit",async e=>{e.preventDefault();const r=await fetch("/admin",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:document.getElementById("u").value,password:document.getElementById("p").value})}),d=await r.json();d.success?window.location.href="/admin/panel":(document.getElementById("msg").textContent="✗ "+d.message,document.getElementById("msg").className="message error",document.getElementById("msg").style.display="block")});</script></body></html>'''

    return '''<!DOCTYPE html><html><head><title>Admin Panel</title><style>*{margin:0;padding:0;box-sizing:border-box}body{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);font-family:Segoe UI;color:#fff;min-height:100vh;padding:20px}.navbar{background:rgba(0,0,0,0.3);padding:20px;border-radius:10px;margin-bottom:30px;display:flex;justify-content:space-between}.container{max-width:1200px;margin:0 auto}.section{background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:10px;padding:30px;margin-bottom:30px}.section h2{margin-bottom:20px}.form-group{margin-bottom:15px}label{display:block;margin-bottom:5px;color:#aaa}input{width:100%;padding:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:5px;color:#fff;margin-bottom:10px}.btn{padding:10px 20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);border:none;border-radius:5px;color:#fff;cursor:pointer}.btn:hover{transform:translateY(-2px)}.btn-danger{background:linear-gradient(135deg,#f44336 0%,#d32f2f 100%)}.message{padding:12px;border-radius:5px;margin-bottom:20px;display:none}.message.error{background:rgba(244,67,54,0.2);color:#f44336}.message.success{background:rgba(76,175,80,0.2);color:#4caf50}.table{width:100%;border-collapse:collapse;margin-top:15px}.table th,.table td{padding:10px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.1);font-size:0.9em}.table th{background:rgba(255,255,255,0.05)}</style></head><body><div class="navbar"><h1>🔑 Admin Panel</h1><a onclick="window.location.href=\\'/logout\\'" style="color:#667eea;cursor:pointer">Logout</a></div><div class="container"><div class="section"><h2>Create New User Key</h2><div class="message" id="msg"></div><div class="form-group"><label>Username</label><input type="text" id="u" placeholder="johndoe" required></div><div class="form-group"><label>Password</label><input type="password" id="p" placeholder="password123" required></div><div class="form-group"><label>Days Valid</label><input type="number" id="d" value="30"></div><button class="btn" onclick="gen()">Create Key</button><div id="o"></div></div><div class="section"><h2>All Keys</h2><button class="btn" onclick="load()">Refresh</button><table class="table" id="t"><tr><th>Username</th><th>Key</th><th>Expires</th><th>Status</th><th>Action</th></tr></table></div></div><script>async function gen(){const u=document.getElementById("u").value;const p=document.getElementById("p").value;const d=document.getElementById("d").value;const msg=document.getElementById("msg");if(!u||!p){msg.textContent="✗ Username and password required";msg.className="message error";msg.style.display="block";return}const r=await fetch("/api/generate",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:u,password:p,days:d})}),res=await r.json();if(res.success){msg.textContent="✓ Key created! Username: "+res.username;msg.className="message success";msg.style.display="block";document.getElementById("u").value="";document.getElementById("p").value="";document.getElementById("o").innerHTML=`<div style="background:rgba(76,175,80,0.2);padding:12px;margin:15px 0;border-radius:3px;font-family:monospace"><strong>Key:</strong> ${res.key}<br><strong>Username:</strong> ${res.username}</div>`;load()}else{msg.textContent="✗ "+(res.message||"Error");msg.className="message error";msg.style.display="block"}}async function load(){const r=await fetch("/api/keys"),d=await r.json();let h='<tr><th>Username</th><th>Key</th><th>Expires</th><th>Status</th><th>Action</th></tr>';d.keys.forEach(k=>{const s=k.banned?"BANNED":"ACTIVE";h+=`<tr><td>${k.username}</td><td style="font-family:monospace;font-size:0.85em">${k.key}</td><td>${k.expires}</td><td>${s}</td><td><button class="btn btn-danger" onclick="ban(\\'${k.username}\\')">Ban</button></td></tr>`}),document.getElementById("t").innerHTML=h}async function ban(username){if(confirm("Ban this key?")){const r=await fetch("/api/ban",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({username:username})}),d=await r.json();d.success?load():alert("Error")}}load();</script></body></html>'''

@app.route('/api/generate', methods=['POST'])
def api_generate():
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    data = request.get_json()
    days = int(data.get('days', 30))
    username = data.get('username', '')
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'}), 400

    if AuthKey.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400

    k = generate_key()
    exp = datetime.utcnow() + timedelta(days=days)
    key_obj = AuthKey(
        key=k,
        username=username,
        password=generate_password_hash(password),
        expires_date=exp
    )
    db.session.add(key_obj)
    db.session.commit()

    return jsonify({'success': True, 'key': k, 'username': username}), 201

@app.route('/api/keys')
def api_keys():
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    keys = AuthKey.query.order_by(AuthKey.created_date.desc()).all()
    return jsonify({'keys': [{'key': k.key, 'username': k.username, 'hwid': k.hwid, 'expires': k.expires_date.strftime('%Y-%m-%d'), 'banned': k.is_banned} for k in keys]})

@app.route('/api/ban', methods=['POST'])
def api_ban():
    if 'admin_id' not in session:
        return jsonify({'success': False}), 401
    data = request.get_json()
    username = data.get('username')
    key = AuthKey.query.filter_by(username=username).first()
    if not key:
        return jsonify({'success': False}), 404
    key.is_banned = True
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
