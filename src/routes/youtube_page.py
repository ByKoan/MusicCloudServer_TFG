# =============================================================================
# youtube_page.py — Búsqueda, reproducción y descarga de contenido de YouTube
# Usado en: youtube.html, youtube.js
#
# Responsabilidades:
#   - Renderizar la página del buscador de YouTube (protegida por sesión)
#   - Buscar vídeos en YouTube y devolver los 10 primeros resultados
#   - Obtener la URL de streaming de audio de un vídeo (sin descargarlo)
#   - Obtener la URL de streaming de vídeo+audio en MP4 (sin descargarlo)
#   - Descargar el audio de un vídeo como MP3 en la carpeta del usuario
#     e insertarlo en la tabla songs de la BD
#   - Registrar en BD una canción ya descargada por el frontend
#     (inserción de seguridad tras confirmación de descarga)
#
# Endpoints que expone:
#   GET  /youtube_page        → renderiza youtube.html
#   POST /youtube_search      → busca vídeos (JSON: {query}) → {results}
#   POST /youtube_audio       → URL de stream de solo audio (JSON: {url}) → {audio, title}
#   POST /youtube_video       → URL de stream de vídeo+audio (JSON: {url}) → {stream, title, thumbnail}
#   POST /youtube_download    → descarga MP3 y registra en BD (JSON: {url}) → {filename}
#   POST /add_song_to_db      → registra canción en BD (JSON: {filename, title}) → {success}
# =============================================================================

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from database.db import get_db_connection
import os
import yt_dlp
from dotenv import load_dotenv
from yt_dlp import YoutubeDL

youtube_bp = Blueprint("youtube", __name__, template_folder="../templates")

# Carpeta base donde se guardará la música descargada
BASE_MUSIC_FOLDER = os.getenv("BASE_MUSIC_FOLDER", "/app/music")

# Numero de resultados al buscar en youtube
YOUTUBE_NUMBER_RESULTS = int(os.getenv("YOUTUBE_NUMBER_RESULTS", 15))


# ===============================
# FUNCIÓN AUXILIAR — Protección de páginas
# Redirige al login si el usuario no tiene sesión activa.
# Devuelve None si la sesión es válida, o un redirect si no lo es.
# ===============================
def login_required_page():
    if "username" not in session:
        return redirect(url_for("auth.login"))
    return None


# ===============================
# PÁGINA DE YOUTUBE
# GET /youtube_page
# Protegida por sesión. Renderiza el buscador de YouTube (youtube.html).
# ===============================
@youtube_bp.route("/youtube_page")
def youtube_page():
    # Protegemos la página del buscador de YouTube
    redirect_login = login_required_page()
    if redirect_login:
        return redirect_login

    # Renderizamos la página principal de YouTube
    return render_template("youtube.html")


# ===============================
# BÚSQUEDA EN YOUTUBE
# POST /youtube_search
# Recibe JSON con query (texto de búsqueda).
# Usa yt-dlp en modo extract_flat para obtener los 10 primeros resultados
# sin descargar ni procesar los vídeos.
# Devuelve JSON {success, results: [{title, url}], error?}.
# ===============================
@youtube_bp.route("/youtube_search", methods=["POST"])
def youtube_search():

    # Verificamos que el usuario esté logueado
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    # Obtenemos el texto de búsqueda enviado por el frontend
    data = request.get_json()
    query = data.get("query")

    # Validamos que la query no esté vacía
    if not query:
        return jsonify({"success": False, "error": "Query vacía"}), 400

    try:
        # Configuración de yt-dlp para búsqueda rápida sin descargar
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "extract_flat": True
        }

        results = []

        # Realizamos búsqueda en YouTube (ytsearch10 = top 10 resultados)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search = ydl.extract_info(f"ytsearch{YOUTUBE_NUMBER_RESULTS}:{query}", download=False)

            # Procesamos cada resultado
            for entry in search["entries"]:
                video_id = entry.get("id")
                title = entry.get("title")

                # Si no hay ID válido, ignoramos el resultado
                if not video_id:
                    continue

                # Guardamos título y URL completa del video
                results.append({
                    "title": title,
                    "url": f"https://www.youtube.com/watch?v={video_id}"
                })

        # Devolvemos resultados al frontend
        return jsonify({"success": True, "results": results})

    except Exception as e:
        # Manejo de errores generales
        return jsonify({"success": False, "error": str(e)})


# ===============================
# STREAM DE SOLO AUDIO
# POST /youtube_audio
# Recibe JSON con url (URL del vídeo de YouTube).
# Extrae la URL directa del mejor stream de audio disponible sin descargarlo.
# Devuelve JSON {success, audio, title, error?}.
# ===============================
@youtube_bp.route("/youtube_audio", methods=["POST"])
def youtube_audio():

    # Verificación de sesión
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    # Obtenemos URL del video
    data = request.get_json()
    url = data.get("url")

    # Validamos entrada
    if not url:
        return jsonify({"success": False, "error": "URL vacía"}), 400

    try:
        # Configuración para extraer solo audio
        ydl_opts = {
            "format": "bestaudio/best",
            "quiet": True
        }

        # Extraemos información del video sin descargarlo
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            audio_url = info["url"]

        # Respondemos con el enlace directo del audio
        return jsonify({
            "success": True,
            "audio": audio_url,
            "title": info.get("title", "Unknown")
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


# ===============================
# STREAM DE VÍDEO + AUDIO
# POST /youtube_video
# Recibe JSON con url (URL del vídeo de YouTube).
# Busca el primer formato disponible que combine vídeo y audio (prioriza MP4).
# Si no encuentra un formato combinado, usa la URL general del info dict.
# Devuelve JSON {success, stream, title, thumbnail, error?}.
# ===============================
@youtube_bp.route("/youtube_video", methods=["POST"])
def youtube_video():

    # Si el usuario no está logueado, se bloquea el acceso
    if "username" not in session:
        return jsonify({"success": False, "error": "No login"}), 401

    data = request.get_json()
    url = data.get("url")

    # Validamos que la URL exista
    if not url:
        return jsonify({"success": False, "error": "URL vacía"}), 400

    try:
        # - best[ext=mp4]/best → prioriza mp4 (mejor compatibilidad en navegadores)
        # - quiet → sin logs en consola
        # - noplaylist → evita procesar listas completas
        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "quiet": True,
            "noplaylist": True
        }

        # download=False → solo obtiene metadata y URLs de streaming
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Recorremos todos los formatos disponibles
        stream_url = None

        for f in info.get("formats", []):
            if (
                f.get("url")                    # tiene URL válida
                and f.get("vcodec") != "none"   # contiene video
                and f.get("acodec") != "none"   # contiene audio
            ):
                stream_url = f["url"]
                break  # usamos el primero válido

        # Si no encontramos formato combinado, usamos el general
        if not stream_url:
            stream_url = info.get("url")

        # Respuesta al frontend
        return jsonify({
            "success": True,
            "stream": stream_url,               # URL directa del stream
            "title": info.get("title"),         # título del video
            "thumbnail": info.get("thumbnail")  # miniatura
        })

    except Exception as e:
        # Manejo de errores
        return jsonify({"success": False, "error": str(e)})


# ===============================
# DESCARGA DE AUDIO EN MP3
# POST /youtube_download
# Recibe JSON con url (URL del vídeo de YouTube).
# Flujo:
#   1. Crea la carpeta del usuario si no existe.
#   2. Descarga el mejor audio disponible y lo convierte a MP3 192 kbps.
#   3. Detecta vídeos privados/eliminados (vía DownloadError o info=None)
#      y los rechaza con mensaje claro sin lanzar excepción.
#   4. Usa prepare_filename para obtener el nombre real sanitizado por yt-dlp.
#   5. Inserta la canción en la tabla songs y suma 1 al total_songs del usuario.
# Devuelve JSON {success, filename, error?}.
# ===============================
@youtube_bp.route("/youtube_download", methods=["POST"])
def youtube_download():

    # Verificación de sesión
    if "username" not in session:
        return jsonify({"success": False, "error": "No has iniciado sesión"}), 401

    # Obtenemos URL del video
    data = request.get_json()
    url = data.get("url")

    # Validamos que exista URL
    if not url:
        return jsonify({"success": False, "error": "No se proporcionó URL"}), 400

    try:
        username = session["username"]  # usuario actual

        # ===============================
        # COMPROBACIÓN ANTI-DUPLICADOS
        # Extraemos el video ID de la URL y comprobamos:
        #   1. Si ya existe en la BD por youtube_video_id (mismo video)
        #   2. Si el archivo ya existe en disco (mismo nombre)
        # Si hay duplicado → devolvemos error sin descargar nada.
        # ===============================
        video_id_match = None
        import re
        m = re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
        if m:
            video_id_match = m.group(1)

        conn_check = get_db_connection()
        cursor_check = conn_check.cursor(dictionary=True)

        try:
            if video_id_match:
                cursor_check.execute(
                    "SELECT title, filename FROM songs WHERE youtube_video_id = %s AND uploaded_by = %s LIMIT 1",
                    (video_id_match, username)
                )
                existing = cursor_check.fetchone()
                if existing:
                    return jsonify({
                        "success": False,
                        "duplicate": True,
                        "error": f"Ya tienes este video descargado: \"{existing['title']}\" ({existing['filename']})"
                    }), 200
        finally:
            cursor_check.close()
            conn_check.close()

        # Creamos carpeta del usuario si no existe
        user_folder = os.path.join(BASE_MUSIC_FOLDER, username)
        os.makedirs(user_folder, exist_ok=True)

        # ===============================
        # PRE-COMPROBACIÓN POR NOMBRE EN DISCO
        # Primero extraemos el título sin descargar para saber el nombre del archivo.
        # Si ya existe en disco, lo rechazamos antes de descargar nada.
        # ===============================
        ydl_opts_meta = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(user_folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            "skip_download": True,
        }

        with YoutubeDL(ydl_opts_meta) as ydl_meta:
            try:
                meta_info = ydl_meta.extract_info(url, download=False)
            except Exception:
                meta_info = None

        if meta_info:
            if meta_info.get("title") in ("[Private video]", "[Deleted video]"):
                return jsonify({"success": False, "error": f"Vídeo no disponible: {meta_info.get('title')}"}), 200

            pre_filename = ydl_meta.prepare_filename(meta_info)
            pre_base = os.path.splitext(pre_filename)[0]
            pre_mp3 = pre_base + ".mp3"

            if os.path.exists(pre_mp3):
                return jsonify({
                    "success": False,
                    "duplicate": True,
                    "error": f"Ya tienes una canción con ese nombre en tu biblioteca: \"{os.path.basename(pre_mp3)}\""
                }), 200

        # Configuración de descarga de audio en MP3
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(user_folder, "%(title)s.%(ext)s"),
            "quiet": True,
            "noplaylist": True,
            # ignoreerrors: permite detectar vídeos privados/no disponibles
            # sin lanzar excepción (devuelve None en su lugar)
            "ignoreerrors": True,
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192"
            }]
        }

        # Descargamos el audio desde YouTube
        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
            except yt_dlp.utils.DownloadError as e:
                err = str(e).lower()
                if "private" in err or "unavailable" in err or "not available" in err:
                    return jsonify({"success": False, "error": "Este vídeo es privado o no está disponible"}), 200
                raise

            # Con ignoreerrors, un vídeo privado devuelve None en lugar de lanzar excepción
            if not info:
                return jsonify({"success": False, "error": "Este vídeo es privado o no está disponible"}), 200

            # Comprobar título de vídeo no disponible
            if info.get("title") in ("[Private video]", "[Deleted video]"):
                return jsonify({"success": False, "error": f"Vídeo no disponible: {info.get('title')}"}), 200

            # Usar prepare_filename para obtener el nombre real sanitizado por yt-dlp
            filename = ydl.prepare_filename(info)

        # Ajustamos extensión final a mp3
        base = os.path.splitext(filename)[0]
        filename = base + ".mp3"

        # Guardamos información en base de datos
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            title = info.get("title", "Unknown")

            # Extraemos el video ID de la URL para guardarlo en BD
            yt_vid_id = None
            import re as _re
            _m = _re.search(r"(?:v=|/)([0-9A-Za-z_-]{11})", url)
            if _m:
                yt_vid_id = _m.group(1)

            # Insertamos canción en tabla songs (solo si no existe ya)
            cursor.execute("""
                INSERT IGNORE INTO songs (title, filename, uploaded_by, youtube_video_id)
                VALUES (%s, %s, %s, %s)
            """, (title, os.path.basename(filename), username, yt_vid_id))

            # Solo incrementamos el contador si se insertó una fila nueva
            if cursor.rowcount > 0:
                cursor.execute("""
                    UPDATE users
                    SET total_songs = total_songs + 1
                    WHERE username = %s
                """, (username,))

            conn.commit()

        finally:
            # Cerramos conexión a base de datos
            cursor.close()
            conn.close()

        # Respuesta exitosa con nombre del archivo
        return jsonify({"success": True, "filename": os.path.basename(filename)})

    except Exception as e:
        # Manejo de errores generales
        return jsonify({"success": False, "error": str(e)})