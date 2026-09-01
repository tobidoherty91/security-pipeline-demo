import os
import uuid
import sqlite3
from flask import Flask, request, render_template, redirect, session, send_from_directory, abort

app = Flask(__name__)

# FIXED: Use environment variable for secret, fallback to random for development
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ------------------- DATABASE -------------------
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, role TEXT)''')
    # Insert default admin if not exists
    c.execute("INSERT OR IGNORE INTO users (id, username, password, role) VALUES (1, 'admin', 'admin', 'admin')")
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

# ------------------- HELPERS -------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ------------------- ROUTES -------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return "Username and password are required", 400
        
        conn = get_db()
        c = conn.cursor()
        try:
            # FIXED: Parameterized query to prevent SQL injection
            c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, 'user')", 
                      (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists", 400
        finally:
            conn.close()
        
        return redirect('/login')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        conn = get_db()
        c = conn.cursor()
        # FIXED: Parameterized query
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/profile')
        else:
            return "Invalid credentials", 401
    
    return render_template('login.html')

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    # FIXED: Only fetch the logged-in user's data (no IDOR)
    user_id = session['user_id']
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    conn.close()
    
    if not user:
        session.clear()
        return redirect('/login')
    
    return render_template('profile.html', user=user)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        return redirect('/login')
    
    if request.method == 'POST':
        # Check if file part exists
        if 'file' not in request.files:
            return "No file part", 400
        
        file = request.files['file']
        
        # Check if user selected a file
        if file.filename == '':
            return "No file selected", 400
        
        # FIXED 1: Validate file extension
        if not allowed_file(file.filename):
            return "File type not allowed", 400
        
        # FIXED 2: Check file size (read in chunks to avoid memory issues)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            return "File too large (max 5MB)", 400
        
        # FIXED 3: Generate a safe, random filename
        original_extension = file.filename.rsplit('.', 1)[1].lower()
        safe_filename = f"{uuid.uuid4().hex}.{original_extension}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)
        
        file.save(file_path)
        return f"File uploaded successfully! Filename: {safe_filename}"
    
    return render_template('upload.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    # FIXED: Use send_from_directory with a strict basename
    # This automatically prevents directory traversal ("../")
    safe_filename = os.path.basename(filename)
    return send_from_directory(UPLOAD_FOLDER, safe_filename)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# ------------------- MAIN -------------------
if __name__ == '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=5000)  # Set debug=False for production
