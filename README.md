
# Anymovies - Simple Flask starter (with sample movie)
This is a simple, legal starter movie site built with Flask. It includes one sample movie (external test file) so you can see how pages behave.

## Quick start (local)
1. Copy `.env.example` to `.env` and set `ADMIN_KEY`.
2. Create virtual env and install:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Run:
   ```bash
   export FLASK_APP=app.py
   flask run
   ```
4. Open http://127.0.0.1:5000

Admin panel: /admin (use ADMIN_KEY from .env)
