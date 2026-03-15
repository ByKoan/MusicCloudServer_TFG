import yt_dlp
from yt_dlp import YoutubeDL
import os

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

youtube_bp = Blueprint(
    "youtube",
    __name__,
    template_folder="../templates"
)

# Carpeta base de música
BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER", "/app/music")


# ===============================
# LOGIN REQUIRED
# ===============================
def login_required_page():
    if "user_id" not in session:
        return redirect(url_for("auth.login"))
    return None


# ===============================
# PAGE
# ===============================
@youtube_bp.route("/youtube_page")
def youtube_page():

    redirect_login = login_required_page()
    if redirect_login:
        return redirect_login

    return render_template("youtube.html")


# ===============================
# SEARCH
# ===============================
@youtube_bp.route("/youtube_search", methods=["POST"])
def youtube_search():

    if "user_id" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    data = request.get_json()
    query = data.get("query")

    if not query:
        return jsonify({"success": False, "error": "Query vacía"}), 400

    try:

        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True
        }

        results = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search = ydl.extract_info(f"ytsearch10:{query}", download=False)

            for entry in search["entries"]:

                video_id = entry.get("id")
                title = entry.get("title")

                if not video_id:
                    continue

                results.append({
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

        return jsonify({
            "success": True,
            "results": results
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# ===============================
# GET AUDIO STREAM
# ===============================
@youtube_bp.route("/youtube_audio", methods=["POST"])
def youtube_audio():

    if "user_id" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"success": False, "error": "URL vacía"}), 400

    try:

        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        return jsonify({
            "success": True,
            "audio": audio_url,
            "title": info.get("title", "Unknown")
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })


# ===============================
# DOWNLOAD AUDIO LOCAL
# ===============================
@youtube_bp.route("/youtube_download", methods=["POST"])
def youtube_download():

    if "user_id" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    data = request.get_json()
    url = data.get("url")

    if not url:
        return jsonify({"success": False, "error": "No se proporcionó URL"}), 400

    try:

        # convertir a string por seguridad
        username = str(session["user_id"])

        user_folder = os.path.join(BASE_MUSIC_FOLDER, username)
        os.makedirs(user_folder, exist_ok=True)

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(user_folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

            # asegurar extensión mp3
            base = os.path.splitext(filename)[0]
            filename = base + ".mp3"

        return jsonify({
            "success": True,
            "filename": os.path.basename(filename)
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        })