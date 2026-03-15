import yt_dlp

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for

youtube_bp = Blueprint(
    "youtube",
    __name__,
    template_folder="../templates"
)


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
                results.append({
                    "title": entry["title"],
                    "url": entry["url"]
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
            "title": info["title"]
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })