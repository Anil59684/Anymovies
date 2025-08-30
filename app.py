
import os, json, uuid
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
DB_PATH = os.path.join(os.getcwd(), 'data', 'db.json')
ADMIN_KEY = os.getenv('ADMIN_KEY', 'changeme123')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app = Flask(__name__, static_folder='static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024

def read_db():
    if not os.path.exists(DB_PATH):
        with open(DB_PATH, 'w') as f:
            json.dump({"movies": [], "requests": []}, f, indent=2)
    with open(DB_PATH, 'r') as f:
        return json.load(f)

def write_db(db):
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=2)

def slugify(s):
    return ''.join(c.lower() if c.isalnum() else '-' for c in s).strip('-')

@app.route('/')
def index():
    db = read_db()
    movies = sorted(db.get('movies', []), key=lambda m: m.get('views', 0), reverse=True)
    return render_template('index.html', movies=movies, current_year=2025)

@app.route('/movie/<slug>')
def movie_page(slug):
    db = read_db()
    movie = next((m for m in db['movies'] if m['slug'] == slug), None)
    if not movie:
        return "Not found", 404
    return render_template('movie.html', movie=movie, current_year=2025)

@app.route('/api/view/<slug>', methods=['POST'])
def api_view(slug):
    db = read_db()
    movie = next((m for m in db['movies'] if m['slug'] == slug), None)
    if not movie:
        return jsonify({"error":"not found"}), 404
    movie['views'] = movie.get('views', 0) + 1
    write_db(db)
    return jsonify({"ok": True, "views": movie['views']})

@app.route('/api/comment/<slug>', methods=['POST'])
def api_comment(slug):
    data = request.json or {}
    user = data.get('user', 'Anon')
    text = data.get('text', '').strip()
    if not text:
        return jsonify({"error": "empty"}), 400
    db = read_db()
    movie = next((m for m in db['movies'] if m['slug'] == slug), None)
    if not movie:
        return jsonify({"error":"not found"}), 404
    c = {"id": str(uuid.uuid4()), "user": user, "text": text}
    movie.setdefault('comments', []).append(c)
    write_db(db)
    return jsonify({"ok": True})

@app.route('/api/rate/<slug>', methods=['POST'])
def api_rate(slug):
    data = request.json or {}
    user = data.get('user', 'anon')
    r = int(data.get('rating', 0))
    r = max(1, min(5, r))
    db = read_db()
    movie = next((m for m in db['movies'] if m['slug'] == slug), None)
    if not movie:
        return jsonify({"error":"not found"}), 404
    ratings = movie.setdefault('ratings', [])
    existing = next((x for x in ratings if x['user'] == user), None)
    if existing:
        existing['rating'] = r
    else:
        ratings.append({'user': user, 'rating': r})
    write_db(db)
    avg = sum(x['rating'] for x in ratings) / len(ratings)
    return jsonify({"ok": True, "avg": avg, "count": len(ratings)})

@app.route('/api/request', methods=['POST'])
def api_request():
    data = request.json or {}
    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({"error":"title required"}), 400
    db = read_db()
    db.setdefault('requests', []).append({
        "id": str(uuid.uuid4()), "title": title, "notes": data.get('notes',''), "status": "pending"
    })
    write_db(db)
    return jsonify({"ok": True})

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'GET':
        return render_template('admin.html', current_year=2025)
    key = request.form.get('admin_key') or request.headers.get('X-Admin-Key','')
    if key != ADMIN_KEY:
        return "Unauthorized", 401
    title = request.form.get('title','').strip()
    year = request.form.get('year','').strip()
    genre = request.form.get('genre','').strip()
    description = request.form.get('description','').strip()
    trailer = request.form.get('trailer','').strip()
    source_url = request.form.get('source_url','').strip()
    poster_url = request.form.get('poster_url','').strip()
    download_url = request.form.get('download_url','').strip()
    source_type = request.form.get('sourceType','mp4')

    poster_path = poster_url
    if 'poster' in request.files and request.files['poster'].filename:
        f = request.files['poster']
        fn = secure_filename(f.filename)
        fpath = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(fpath)
        poster_path = '/uploads/' + fn
    source_path = source_url
    if 'video' in request.files and request.files['video'].filename:
        f = request.files['video']
        fn = secure_filename(f.filename)
        fpath = os.path.join(app.config['UPLOAD_FOLDER'], fn)
        f.save(fpath)
        source_path = '/uploads/' + fn
        if not download_url:
            download_url = source_path

    slug = slugify(f"{title}-{year}")
    db = read_db()
    movie = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "title": title,
        "year": year,
        "genre": genre,
        "description": description,
        "poster": poster_path or '/static/placeholder.jpg',
        "source": source_path,
        "sourceType": source_type,
        "download": download_url or source_path,
        "trailer": trailer,
        "views": 0,
        "ratings": [],
        "comments": []
    }
    db.setdefault('movies', []).insert(0, movie)
    write_db(db)
    return redirect(url_for('movie_page', slug=slug))

@app.route('/download/<slug>')
def download_interstitial(slug):
    db = read_db()
    movie = next((m for m in db['movies'] if m['slug'] == slug), None)
    if not movie:
        return "Not found", 404
    return render_template('download.html', movie=movie, current_year=2025)

@app.route('/go-download/<slug>')
def go_download(slug):
    db = read_db()
    movie = next((m for m in db['movies'] if m['slug'] == slug), None)
    if not movie:
        return "Not found", 404
    url = movie.get('download') or movie.get('source')
    return redirect(url)

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
