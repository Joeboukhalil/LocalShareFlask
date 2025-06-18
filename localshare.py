from flask import Flask, request, send_from_directory, redirect, url_for, session, render_template_string
import os
import socket

app = Flask(__name__)
app.secret_key = 'verysecretkey'
SHARED_FOLDER = os.path.join(os.getcwd(), 'shared_files')
CONFIG_FILE = 'config.txt'
os.makedirs(SHARED_FOLDER, exist_ok=True)

# Load credentials
def load_credentials():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            f.write("username=admin\npassword=admin123\n")
    with open(CONFIG_FILE) as f:
        data = dict(line.strip().split('=') for line in f if '=' in line)
    return data.get('username', 'admin'), data.get('password', 'admin123')

# Save new credentials
def save_credentials(username, password):
    with open(CONFIG_FILE, "w") as f:
        f.write(f"username={username}\npassword={password}\n")

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head><title>File Share</title></head>
<body>
    <h1>📁 Local File Sharing</h1>
    {% if not session.get('logged_in') %}
        <form method="post" action="/login">
            <input name="username" placeholder="Username"><br>
            <input name="password" type="password" placeholder="Password"><br>
            <input type="submit" value="Login">
        </form>
        {% if error %}<p style="color:red;">{{ error }}</p>{% endif %}
    {% else %}
        <form method="post" action="/upload" enctype="multipart/form-data">
            <h3>Upload File</h3>
            <input type="file" name="file">
            <input type="submit" value="Upload">
        </form>
        <form method="post" action="/change_password">
            <h3>Change Username & Password</h3>
            <input name="new_username" placeholder="New Username"><br>
            <input name="new_password" type="password" placeholder="New Password"><br>
            <input type="submit" value="Update">
        </form>
        <h2>Files:</h2>
        {% for file in files %}
            <a href="/file/{{ file }}">{{ file }}</a><br>
        {% endfor %}
        <br><a href="/logout">Logout</a>
    {% endif %}
</body>
</html>
"""

# Get local IP address
def get_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except:
        return "127.0.0.1"
    finally:
        s.close()

USERNAME, PASSWORD = load_credentials()

@app.route('/', methods=['GET'])
def home():
    if not session.get('logged_in'):
        return render_template_string(HTML_PAGE, error=None)
    files = os.listdir(SHARED_FOLDER)
    return render_template_string(HTML_PAGE, files=files)

@app.route('/login', methods=['POST'])
def login():
    global USERNAME, PASSWORD
    user = request.form.get('username')
    pw = request.form.get('password')
    if user == USERNAME and pw == PASSWORD:
        session['logged_in'] = True
        return redirect(url_for('home'))
    return render_template_string(HTML_PAGE, error="Wrong credentials")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    file = request.files.get('file')
    if file:
        file.save(os.path.join(SHARED_FOLDER, file.filename))
    return redirect(url_for('home'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    new_user = request.form.get('new_username')
    new_pass = request.form.get('new_password')
    if new_user and new_pass:
        save_credentials(new_user, new_pass)
        global USERNAME, PASSWORD
        USERNAME, PASSWORD = load_credentials()
    return redirect(url_for('home'))

@app.route('/file/<path:filename>')
def serve_file(filename):
    if not session.get('logged_in'):
        return redirect(url_for('home'))
    return send_from_directory(SHARED_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print(f"Server running at: http://{get_ip()}:5000")
    app.run(host="0.0.0.0", port=5000)
