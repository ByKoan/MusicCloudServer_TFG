from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.db import get_db_connection
import os
import yt_dlp
from yt_dlp import YoutubeDL

youtube_bp = Blueprint("youtube", __name__, template_folder="../templates")
BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER", "/app/music")

def login_required_page():
    if "username" not in session:
        return redirect(url_for("auth.login"))
    return None


@youtube_bp.route("/youtube_page")
def youtube_page():
    redirect_login = login_required_page()
    if redirect_login:
        return redirect_login
    return render_template("youtube.html")


@youtube_bp.route("/youtube_search", methods=["POST"])
def youtube_search():
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    data = request.get_json()
    query = data.get("query")
    if not query:
        return jsonify({"success": False, "error": "Query vacía"}), 400

    try:
        ydl_opts = {"quiet": True, "skip_download": True, "extract_flat": True}
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

        return jsonify({"success": True, "results": results})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@youtube_bp.route("/youtube_audio", methods=["POST"])
def youtube_audio():
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"success": False, "error": "URL vacía"}), 400

    try:
        ydl_opts = {"format": "bestaudio/best", "quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        return jsonify({
            "success": True,
            "audio": audio_url,
            "title": info.get("title", "Unknown")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@youtube_bp.route("/youtube_download", methods=["POST"])
def youtube_download():
    if "username" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    data = request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"success": False, "error": "No se proporcionó URL"}), 400

    try:
        username = session["username"]  # para BD y carpeta
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

        base = os.path.splitext(filename)[0]
        filename = base + ".mp3"

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            title = info.get("title", "Unknown")
            cursor.execute("""
                INSERT IGNORE INTO songs (title, filename, uploaded_by)
                VALUES (%s, %s, %s)
            """, (title, os.path.basename(filename), username))

            cursor.execute("""
                UPDATE users
                SET total_songs = total_songs + 1
                WHERE username = %s
            """, (username,))

            conn.commit()
        finally:
            cursor.close()
            conn.close()

        return jsonify({"success": True, "filename": os.path.basename(filename)})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})