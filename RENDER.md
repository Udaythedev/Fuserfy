Fuserfy — Deploying to Render

This file contains quick steps to deploy the `Fuserfy` Flask app to Render (https://render.com).

1) Create a new Web Service on Render and connect your GitHub repository.

2) Build & Start commands
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn "wsgi:application" -b 0.0.0.0:$PORT -w 3`

3) Environment
- Set the following environment variables in Render (Dashboard → Environment):
  - `SPOTIPY_CLIENT_ID` (your Spotify app client id)
  - `SPOTIPY_CLIENT_SECRET` (your Spotify app client secret)
  - `FLASK_SECRET_KEY` (a secure random secret for Flask sessions)
  - `SPOTIPY_REDIRECT_URI` (e.g. `https://<your-render-url>/.*/callback` — set to your app's URL + `/callback`)

4) Spotify App Redirect URI
- In your Spotify Developer Dashboard, add the Render URL callback to Redirect URIs. Example:
  `https://<your-render-subdomain>.onrender.com/callback`

5) Notes
- Use `.env` locally for development; do NOT commit `.env` to the repository.
- If you previously pushed credentials, rotate them now in the Spotify Developer Dashboard.
