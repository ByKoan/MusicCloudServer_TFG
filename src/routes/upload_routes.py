import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from services.music_service import get_user_folder
from utils.file_utils import allowed_file
from database.db import get_db_connection

upload_bp = Blueprint(
    "upload",
    __name__,
    template_folder="../templates"
)

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


@upload_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_file():

    username = session["user_id"]   
    user_folder = get_user_folder(username)

    os.makedirs(user_folder, exist_ok=True)

    if request.method == "POST":

        if "file" not in request.files:
            flash("No se envió ningún archivo", "error")
            return redirect(request.url)

        files = request.files.getlist("file")

        if not files:
            flash("No seleccionaste ningún archivo", "error")
            return redirect(request.url)

        conn = get_db_connection()
        cursor = conn.cursor()

        uploaded = False

        for file in files:

            if file.filename == "":
                continue

            if not allowed_file(file.filename):
                flash(f"Formato no permitido: {file.filename}", "error")
                continue

            filename = secure_filename(file.filename)
            file_path = os.path.join(user_folder, filename)

            try:

                # guardar archivo
                file.save(file_path)

                # insertar en tabla songs
                cursor.execute(
                    """
                    INSERT INTO songs (title, filename, uploaded_by, plays)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (filename, filename, username, 0)
                )

                # actualizar contador del usuario
                cursor.execute(
                    """
                    UPDATE users
                    SET total_songs = total_songs + 1
                    WHERE username = %s
                    """,
                    (username,)
                )

                uploaded = True

            except Exception as e:
                conn.rollback()
                flash(f"Error subiendo {filename}: {str(e)}", "error")

        conn.commit()
        cursor.close()
        conn.close()

        if uploaded:
            flash("Canciones subidas correctamente", "success")
            return redirect(url_for("music.index"))

        flash("No se subió ninguna canción", "error")
        return redirect(request.url)

    return render_template("upload.html")