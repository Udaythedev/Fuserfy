# Fuserfy

Fuserfy is a small Flask web app to manage Spotify playlists and add songs via the Spotify Web API.

Prerequisites
- Python 3.10+
- A Spotify Developer app with Client ID/Secret and Redirect URI configured.

Quick start (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env to add your Spotify credentials
python app.py
```

Run with Gunicorn (production example)

```powershell
# On Linux/containers
gunicorn "wsgi:application" -w 3 -b 0.0.0.0:8000
```

Docker (build & run)

```powershell
docker build -t fuserfy .
docker run -e SPOTIPY_CLIENT_ID=... -e SPOTIPY_CLIENT_SECRET=... -e FLASK_SECRET_KEY=... -p 5000:5000 fuserfy
```

Notes
- Do NOT commit your real credentials. Use `.env` (and `.gitignore` prevents it from being committed).
- For production, set `FLASK_SECRET_KEY` and run behind a WSGI server or container orchestrator.
- If your Spotify credentials were committed previously, rotate them immediately.

Pre-push cleanup

Before you push the project to GitHub, run these commands to ensure local files are not tracked:

```powershell
# Remove local virtualenv from git index (if it was accidentally added)
git rm -r --cached venv || true
# Untrack .env file
git rm --cached .env || true
git add .gitignore
git commit -m "Remove local files from repo and update .gitignore"
```

Alternatively, run the helper script:

```powershell
.\scripts\cleanup_repo.ps1
```