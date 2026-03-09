import os

from database.db import get_db_connection
from config import Config
from utils.file_utils import allowed_file


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