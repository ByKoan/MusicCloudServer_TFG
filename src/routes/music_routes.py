import os
from flask import Blueprint, render_template, request, redirect, url_for, session, send_file, jsonify

from services.music_service import get_user_folder
from utils.file_utils import allowed_file
from database.db import get_db_connection

music_bp = Blueprint("music", __name__)


@music_bp.route("/")
def index():

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    username = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT filename FROM songs WHERE uploaded_by = %s",
        (username,)
    )
    songs = [row["filename"] for row in cursor.fetchall()]

    cursor.execute(
        "SELECT id, name FROM playlists WHERE user_id = %s",
        (username,)
    )
    playlists = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        songs=songs,
        current_song="",
        playlists=playlists
    )


@music_bp.route("/play/<filename>")
def play(filename):

    if "user_id" not in session:
        return redirect(url_for("auth.login"))

    username = session["user_id"]

    user_folder = get_user_folder(username)
    file_path = os.path.join(user_folder, filename)

    if os.path.isfile(file_path) and allowed_file(filename):

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE songs
                SET plays = plays + 1
                WHERE filename = %s AND uploaded_by = %s
                """,
                (filename, username)
            )
            conn.commit()

        except Exception as e:
            print(f"Error al actualizar plays: {e}")

        finally:
            cursor.close()
            conn.close()

        return send_file(file_path)

    return "Archivo no encontrado", 404


@music_bp.route("/delete_song", methods=["POST"])
def delete_song():

    if "user_id" not in session:
        return jsonify({"error": "No autorizado"}), 403

    username = session["user_id"]

    data = request.get_json()
    filename = data.get("filename")

    if not filename or not allowed_file(filename):
        return jsonify({"error": "Archivo no válido"}), 400

    filepath = os.path.join(get_user_folder(username), filename)

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "DELETE FROM songs WHERE filename = %s AND uploaded_by = %s",
            (filename, username)
        )

        conn.commit()

    except Exception as e:

        return jsonify({"error": f"No se pudo borrar de la BD: {e}"}), 500

    finally:

        cursor.close()
        conn.close()

    if os.path.exists(filepath):

        try:
            os.remove(filepath)

        except Exception as e:
            return jsonify({"error": f"No se pudo borrar del disco: {e}"}), 500

    return jsonify({"success": True})
