import os

from database.db import get_db_connection
from config import Config
from utils.file_utils import allowed_file


def restore_user_songs(username):
    """
    Restaura en la BD las canciones del disco que pertenecen a `username`.
    Se llama justo después de crear un usuario para recuperar sus canciones
    si ya existía una carpeta previa con su mismo nombre.

    - Inserta en songs los archivos de disco que no estén ya en BD.
    - Actualiza total_songs del usuario.
    - No elimina nada: solo añade lo que falta.
    """

    user_folder = os.path.join(Config.BASE_MUSIC_FOLDER, username)

    # Si no hay carpeta previa no hay nada que restaurar
    if not os.path.isdir(user_folder):
        return

    conn   = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Canciones que ya están en BD para este usuario
        cursor.execute(
            "SELECT filename FROM songs WHERE uploaded_by = %s",
            (username,)
        )
        db_filenames = {row["filename"] for row in cursor.fetchall()}

        restored = 0

        for filename in os.listdir(user_folder):
            if not allowed_file(filename):
                continue
            if filename in db_filenames:
                continue  # ya existe en BD, no duplicar

            cursor.execute(
                """
                INSERT INTO songs (title, filename, uploaded_by, plays)
                VALUES (%s, %s, %s, 0)
                """,
                (filename, filename, username)
            )
            restored += 1

        # Recalcula total_songs para que quede consistente
        cursor.execute(
            """
            UPDATE users
            SET total_songs = (
                SELECT COUNT(*) FROM songs WHERE uploaded_by = %s
            )
            WHERE username = %s
            """,
            (username, username)
        )

        conn.commit()

        if restored:
            print(f"[RESTORE] {restored} canción(es) restauradas para '{username}'")

    finally:
        cursor.close()
        conn.close()


def sync_music_database():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    music_root = Config.BASE_MUSIC_FOLDER

    added_count = 0
    removed_count = 0

    # =========================
    # canciones existentes en BD
    # =========================
    cursor.execute("SELECT filename, uploaded_by FROM songs")
    db_songs = {(row["uploaded_by"], row["filename"]) for row in cursor.fetchall()}

    disk_songs = set()

    # =========================
    # recorrer carpetas usuarios
    # =========================
    for username in os.listdir(music_root):

        user_folder = os.path.join(music_root, username)

        if not os.path.isdir(user_folder):
            continue

        # Comprobar que el usuario existe en la BD
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone() is None:
            print(f"[WARN] Usuario '{username}' no encontrado en la BD. Se omitirán sus canciones.")
            continue 

        for filename in os.listdir(user_folder):

            if not allowed_file(filename):
                continue

            disk_songs.add((username, filename))

            if (username, filename) not in db_songs:
                cursor.execute(
                    """
                    INSERT INTO songs (title, filename, uploaded_by)
                    VALUES (%s, %s, %s)
                    """,
                    (filename, filename, username)
                )
                added_count += 1

    # =========================
    # borrar canciones que no existen en disco
    # =========================
    for username, filename in db_songs:

        if (username, filename) not in disk_songs:
            cursor.execute(
                "DELETE FROM songs WHERE filename=%s AND uploaded_by=%s",
                (filename, username)
            )
            removed_count += 1

    # =========================
    # actualizar total_songs
    # =========================
    cursor.execute("""
        UPDATE users u
        SET total_songs = (
            SELECT COUNT(*)
            FROM songs s
            WHERE s.uploaded_by = u.username
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    # =========================
    # LOG FINAL
    # =========================
    print(
        f"[SYNC] Sincronización completada | "
        f"Añadidas: {added_count} | Eliminadas: {removed_count}"
    )