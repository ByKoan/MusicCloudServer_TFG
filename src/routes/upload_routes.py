import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from services.music_service import get_user_folder
from utils.file_utils import allowed_file
from database.db import get_db_connection

# =========================
# Blueprint
# =========================
upload_bp = Blueprint(
    "upload",
    __name__,
    template_folder="../templates"  
)

# =========================
# Decorador de login
# =========================
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesión", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# =========================
# Upload de canciones
# =========================
@upload_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    user_id = session['user_id']
    username = session.get('username', f"user_{user_id}")  
    user_folder = get_user_folder(user_id)
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No se envió ningún archivo", "error")
            return redirect(url_for('upload.upload_file'))

        files = request.files.getlist('file')
        if not files:
            flash("No seleccionaste ningún archivo", "error")
            return redirect(url_for('upload.upload_file'))

        conn = get_db_connection()
        cursor = conn.cursor()
        for file in files:
            if file.filename == '':
                continue
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(user_folder, filename)
                file.save(file_path)

                try:
                    cursor.execute(
                        "INSERT INTO songs (title, filename, uploaded_by, plays) VALUES (%s, %s, %s, %s)",
                        (filename, filename, username, 0)
                    )
                    cursor.execute(
                        "UPDATE users SET total_songs = total_songs + 1 WHERE username = %s",
                        (username,)
                    )
                except Exception as e:
                    flash(f"No se pudo registrar '{filename}' en la base de datos: {e}", "error")

        conn.commit()
        cursor.close()
        conn.close()

        flash("Archivos subidos correctamente", "success")
        return redirect(url_for('music.index'))

    # Renderizar template de upload
    return render_template("upload.html")