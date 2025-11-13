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

# Cookie/session security defaults
app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
# For production behind HTTPS, set SESSION_COOKIE_SECURE to True in env or here
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('FORCE_SESSION_SECURE') == '1':
    app.config.setdefault('SESSION_COOKIE_SECURE', True)

# ---------------- Spotify API Credentials (from env) ---------------- #
# We build the SpotifyOAuth per-request so redirect URIs can be dynamic (useful for
# local dev vs rendered/prod deployments). If `SPOTIPY_REDIRECT_URI` is set in the
# environment it will be used; otherwise the app will use the current request's
# root URL and append `/callback`.
SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SCOPE = os.environ.get('SPOTIPY_SCOPE', "playlist-modify-public playlist-modify-private playlist-read-private user-read-playback-state user-modify-playback-state user-read-currently-playing user-top-read")


def get_spotify_oauth(redirect_override: str | None = None):
    """Return a SpotifyOAuth configured for the current request.

    If `SPOTIPY_REDIRECT_URI` env var is set it is used. Otherwise if
    `redirect_override` is provided it's used. If neither is available and a
    request context is active, the function will use `request.url_root + 'callback'`.
    """
    redirect_uri = os.environ.get('SPOTIPY_REDIRECT_URI')
    if not redirect_uri and redirect_override:
        redirect_uri = redirect_override
    # If still not set, try to build from the active request
    try:
        if not redirect_uri and request:
            redirect_uri = request.url_root.rstrip('/') + '/callback'
    except RuntimeError:
        # No request context; fall back to localhost callback for offline tools
        redirect_uri = redirect_uri or 'http://127.0.0.1:5000/callback'

    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=redirect_uri,
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
        oauth = get_spotify_oauth()
        # show helpful message if creds are not configured
        if not SPOTIPY_CLIENT_ID or not SPOTIPY_CLIENT_SECRET:
            return (
                "Spotify client credentials are not configured. "
                "Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET in your environment."
            ), 500
        auth_url = oauth.get_authorize_url()
        return redirect(auth_url)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('index'))

@app.route("/callback")
def callback():
    code = request.args.get('code')
    if code:
        # Exchange code for token_info and store in session
        oauth = get_spotify_oauth()
        token_info = oauth.get_access_token(code)
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
            oauth = get_spotify_oauth()
            refreshed = oauth.refresh_access_token(token_info.get('refresh_token'))
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

    try:
        user_data = sp.current_user()
        display_name = user_data.get('display_name')
        profile_image = user_data.get('images', [{}])[0].get('url', '') if user_data.get('images') else ''
        
        playlists = sp.current_user_playlists().get('items', [])

        # Get currently playing song
        current = sp.current_playback()
        if current and current['is_playing']:
            now_playing = {
                'track_name': current['item']['name'],
                'artist_name': ', '.join([a['name'] for a in current['item']['artists']]),
                'album_image': current['item']['album']['images'][0]['url'],
                'is_playing': True
            }
        else:
            now_playing = {
                'track_name': 'No song playing',
                'artist_name': '',
                'album_image': '',
                'is_playing': False
            }

        # Get top tracks (last 4 weeks) - with error handling
        top_tracks_data = []
        try:
            top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term').get('items', [])
            top_tracks_data = [
                {
                    'name': track['name'],
                    'artist': ', '.join([a['name'] for a in track['artists']]),
                    'image': track['album']['images'][0]['url'] if track['album']['images'] else ''
                }
                for track in top_tracks
            ]
        except Exception as e:
            print(f"Error fetching top tracks: {e}")

        # Get top artists (last 4 weeks) - with error handling
        top_artists_data = []
        try:
            top_artists = sp.current_user_top_artists(limit=5, time_range='short_term').get('items', [])
            top_artists_data = [
                {
                    'name': artist['name'],
                    'image': artist['images'][0]['url'] if artist['images'] else '',
                    'genres': ', '.join(artist['genres'][:2]) if artist['genres'] else 'Genre N/A'
                }
                for artist in top_artists
            ]
        except Exception as e:
            print(f"Error fetching top artists: {e}")

        return render_template(
            "home.html",
            display_name=display_name,
            profile_image=profile_image,
            playlists=playlists,
            now_playing=now_playing,
            top_tracks=top_tracks_data,
            top_artists=top_artists_data,
            project_name=PROJECT_NAME
        )
    except Exception as e:
        error_msg = str(e)
        # Check for common Spotify errors
        if '403' in error_msg and 'user may not be registered' in error_msg.lower():
            flash(
                "Your Spotify account is not registered as a test user. "
                "Go to https://developer.spotify.com/dashboard, select your app, "
                "and add your Spotify account email under 'User Management'.",
                "error"
            )
        elif '401' in error_msg or 'unauthorized' in error_msg.lower():
            flash("Session expired. Please log in again.", "error")
            session.pop('token_info', None)
            return redirect(url_for('index'))
        elif '429' in error_msg:
            flash("Rate limited by Spotify. Please try again in a moment.", "error")
        else:
            flash(f"Error loading playlists: {error_msg}", "error")
        
        return redirect(url_for('index'))

# ---------------- Playlist Management ---------------- #
@app.route("/add_songs", methods=["POST"])
def add_songs():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))
    playlist_id = request.form.get('playlist_id')
    song_list = [s.strip() for s in request.form.get('song_list', '').splitlines() if s.strip()]

    try:
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
    except Exception as e:
        flash(f"Error adding songs: {str(e)}", "error")

    return redirect(url_for('home'))

@app.route("/create_playlist", methods=["POST"])
def create_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    name = request.form.get('new_playlist_name')
    try:
        user_id = sp.current_user().get('id')
        sp.user_playlist_create(user_id, name)
        flash(f"Playlist '{name}' created!", "success")
    except Exception as e:
        flash(f"Error creating playlist: {str(e)}", "error")
    
    return redirect(url_for('home'))

@app.route("/rename_playlist", methods=["POST"])
def rename_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    playlist_id = request.form.get('playlist_id')
    new_name = request.form.get('new_name')
    try:
        sp.playlist_change_details(playlist_id, name=new_name)
        flash(f"Playlist renamed to '{new_name}'!", "success")
    except Exception as e:
        flash(f"Error renaming playlist: {str(e)}", "error")
    
    return redirect(url_for('home'))

@app.route("/delete_playlist", methods=["POST"])
def delete_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))

    playlist_id = request.form.get('playlist_id')
    try:
        sp.current_user_unfollow_playlist(playlist_id)
        flash("Playlist deleted!", "success")
    except Exception as e:
        flash(f"Error deleting playlist: {str(e)}", "error")
    
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
        elif action == "shuffle":
            current = sp.current_playback()
            new_state = not current.get('shuffle_state', False) if current else True
            sp.shuffle(new_state)
        elif action == "repeat":
            # Cycle through repeat states: off -> context -> track -> off
            current = sp.current_playback()
            repeat_state = current.get('repeat_state', 'off') if current else 'off'
            if repeat_state == 'off':
                sp.repeat('context')
            elif repeat_state == 'context':
                sp.repeat('track')
            else:
                sp.repeat('off')
    except Exception as e:
        error_msg = str(e)
        if '404' in error_msg:
            flash("No active device found. Play something on Spotify first.", "error")
        else:
            flash(f"Player action failed: {error_msg}", "error")

    return redirect(url_for('home'))

@app.route("/search_songs", methods=["POST"])
def search_songs():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))
    
    query = request.form.get('search_query', '').strip()
    if not query:
        flash("Please enter a search term.", "error")
        return redirect(url_for('home'))
    
    try:
        results = sp.search(q=query, limit=10, type='track')
        tracks = results.get('tracks', {}).get('items', [])
        search_results = [
            {
                'uri': track['uri'],
                'name': track['name'],
                'artist': ', '.join([a['name'] for a in track['artists']]),
                'image': track['album']['images'][0]['url'] if track['album']['images'] else '',
                'id': track['id']
            }
            for track in tracks
        ]
        
        return render_template(
            "search_results.html",
            search_query=query,
            search_results=search_results,
            project_name=PROJECT_NAME,
            playlists=sp.current_user_playlists().get('items', [])
        )
    except Exception as e:
        flash(f"Search failed: {str(e)}", "error")
        return redirect(url_for('home'))

@app.route("/add_song_to_playlist", methods=["POST"])
def add_song_to_playlist():
    sp = get_spotify()
    if not sp:
        flash("Not authenticated. Please sign in again.", "error")
        return redirect(url_for('index'))
    
    playlist_id = request.form.get('playlist_id')
    track_uri = request.form.get('track_uri')
    
    try:
        sp.playlist_add_items(playlist_id, [track_uri])
        flash("Song added to playlist!", "success")
    except Exception as e:
        flash(f"Error adding song: {str(e)}", "error")
    
    return redirect(request.referrer or url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
