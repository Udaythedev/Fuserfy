from flask import Flask, render_template, redirect, request, session, url_for, flash
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from flask_cors import CORS
import os
import time

app = Flask(__name__)
CORS(app)

# Load environment variables (optional .env during development)
try:
    # python-dotenv is optional; if present it will load .env automatically
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Secret key for session (set `FLASK_SECRET_KEY` in production)
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or os.urandom(24)

# ---------------- Spotify API Credentials (from env) ---------------- #
SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5000/callback')
SCOPE = os.environ.get('SPOTIPY_SCOPE', "playlist-modify-public playlist-modify-private playlist-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing")

# OAuth object (reused)
sp_oauth = SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope=SCOPE
)

# Project name (used in templates/title)
PROJECT_NAME = os.environ.get('PROJECT_NAME', 'Fuserfy')

# ---------------- Routes ---------------- #
@app.route("/")
def index():
    if 'token_info' in session:
        return redirect(url_for('home'))
    else:
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if code:
        # Exchange code for token_info and store in session
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('home'))
    else:
        flash("Spotify login failed", "error")
        return redirect(url_for('index'))

def get_spotify():
    # Ensure we have token_info in session and refresh if needed
    token_info = session.get('token_info')
    if not token_info:
        return None

    # Refresh token if it's expired (allow 60s leeway)
    expires_at = token_info.get('expires_at')
    if expires_at and (int(time.time()) - int(expires_at)) >= 0:
        try:
            refreshed = sp_oauth.refresh_access_token(token_info.get('refresh_token'))
            token_info.update(refreshed)
            session['token_info'] = token_info
        except Exception:
            session.pop('token_info', None)
            return None

    access_token = token_info.get('access_token')
    if not access_token:
        return None

    sp = Spotify(auth=access_token)
    return sp

@app.route("/home")
def home():
    sp = get_spotify()
    if not sp:
        return redirect(url_for('index'))

    display_name = sp.current_user().get('display_name')
    playlists = sp.current_user_playlists().get('items', [])

    # Get currently playing song
    current = sp.current_playback()
    if current and current['is_playing']:
        now_playing = {
            'track_name': current['item']['name'],
            'artist_name': ', '.join([a['name'] for a in current['item']['artists']]),
            'album_image': current['item']['album']['images'][0]['url']
        }
    else:
        now_playing = {
            'track_name': 'No song playing',
            'artist_name': '',
            'album_image': ''
        }

    return render_template(
        "home.html",
        display_name=display_name,
        playlists=playlists,
        now_playing=now_playing,
        project_name=PROJECT_NAME
    )

# ---------------- Playlist Management ---------------- #
@app.route("/add_songs", methods=["POST"])
def add_songs():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))
    playlist_id = request.form.get('playlist_id')
    song_list = [s.strip() for s in request.form.get('song_list', '').splitlines() if s.strip()]

    track_uris = []
    for song in song_list:
        results = sp.search(q=song, limit=1, type='track')
        items = results.get('tracks', {}).get('items')
        if items:
            track_uris.append(items[0]['uri'])
        else:
            flash(f"Song not found: {song}", "error")

    if track_uris:
        sp.playlist_add_items(playlist_id, track_uris)
        flash(f"Added {len(track_uris)} songs!", "success")
    else:
        flash("No valid songs found.", "error")

    return redirect(url_for('home'))

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    name = request.form.get('new_playlist_name')
    user_id = sp.current_user().get('id')
    sp.user_playlist_create(user_id, name)
    flash(f"Playlist '{name}' created!", "success")
    return redirect(url_for('home'))

@app.route("/rename_playlist", methods=["POST"])
def rename_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    playlist_id = request.form.get('playlist_id')
    new_name = request.form.get('new_name')
    sp.playlist_change_details(playlist_id, name=new_name)
    flash(f"Playlist renamed to '{new_name}'!", "success")
    return redirect(url_for('home'))

@app.route("/delete_playlist", methods=["POST"])
def delete_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    playlist_id = request.form.get('playlist_id')
    sp.current_user_unfollow_playlist(playlist_id)
    flash("Playlist deleted!", "success")
    return redirect(url_for('home'))

# ---------------- Player Controls ---------------- #
@app.route("/player_control", methods=["POST"])
def player_control():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    action = request.form.get('action')

    try:
        if action == "play_pause":
            current = sp.current_playback()
            if current and current.get('is_playing'):
                sp.pause_playback()
            else:
                sp.start_playback()
        elif action == "next":
            sp.next_track()
        elif action == "previous":
            sp.previous_track()
    except Exception:
        flash("Player action failed", "error")

    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
