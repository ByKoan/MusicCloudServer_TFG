# =============================================================================
# auth_routes.py — Autenticación de usuarios (login, registro, logout)
# Usado en: login.html, login.js
#
# Responsabilidades:
#   - Login: validar credenciales, comprobar baneo y guardar sesión
#   - Registro: cifrar contraseña e insertar nuevo usuario en la BD
#   - Logout: limpiar datos de sesión y redirigir al login
#   - Bloquear acceso a /register por GET (solo acepta POST)
#
# Endpoints que expone:
#   GET  /login     → muestra el formulario de inicio de sesión
#   POST /login     → procesa credenciales y crea sesión
#   POST /register  → crea un nuevo usuario (API JSON)
#   GET  /register  → redirige a /login (acceso directo no permitido)
#   GET  /logout    → cierra sesión y redirige a /login
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from services.auth_service import validate_user                    # Valida usuario y contraseña
from database.db import get_user_role, get_user_ban, get_db_connection  # Funciones de BD
from werkzeug.security import generate_password_hash               # Cifrado de contraseñas
from datetime import datetime                                       # Manejo de fechas (baneo)

# Blueprint de autenticación (login, registro, logout)
auth_bp = Blueprint("auth", __name__)


# ===============================
# LOGIN
# GET  → muestra el formulario
# POST → valida credenciales, comprueba baneo y guarda sesión
# ===============================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():

    # Si se envía el formulario (POST)
    if request.method == 'POST':

        # Obtiene datos del formulario y normaliza a minúsculas
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()

        # Valida credenciales (contraseña + existencia en BD)
        if validate_user(username, password):

            # Comprueba si el usuario está baneado temporalmente
            banned_until = get_user_ban(username)

            # Si está baneado y aún no ha pasado el tiempo → bloqueo
            if banned_until and banned_until > datetime.now():
                return render_template(
                    "login.html",
                    error=f"Usuario baneado hasta {banned_until}"
                )

            # Guarda datos del usuario en la sesión
            session['username'] = username
            session['user_id']  = username          # username actúa como ID
            session['role']     = get_user_role(username)  # guarda el rol (user / admin)

            # Redirige a la página principal de música
            return redirect(url_for('music.index'))

        # Credenciales incorrectas → muestra error en el formulario
        return render_template("login.html", error="Credenciales incorrectas")

    # Si es GET → muestra el formulario vacío
    return render_template("login.html")


# ===============================
# REGISTRO (POST — API JSON)
# Crea un nuevo usuario con contraseña cifrada.
# Devuelve JSON en lugar de redirigir (lo consume login.js).
# ===============================
@auth_bp.route("/register", methods=["POST"])
def register():

    # Obtiene datos JSON (no formulario HTML)
    data     = request.get_json()
    username = data.get("username", "").lower()
    password = data.get("password", "")

    # Validación básica: ambos campos son obligatorios
    if not username or not password:
        return jsonify({
            "success": False,
            "error": "Todos los campos son obligatorios"
        }), 400

    # Cifra la contraseña antes de guardarla en la BD
    hashed_password = generate_password_hash(password)

    # Conexión a la base de datos
    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        # Inserta el nuevo usuario en la BD
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, hashed_password)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Usuario registrado correctamente"
        })

    except Exception as e:
        # Error de duplicado (usuario ya existe en BD)
        if "Duplicate entry" in str(e):
            return jsonify({
                "success": False,
                "error": "El usuario ya existe"
            }), 409

        # Otro error inesperado
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

    finally:
        # Cierra conexión SIEMPRE (haya error o no)
        cursor.close()
        conn.close()


# ===============================
# REGISTRO (GET)
# Evita que alguien acceda a /register desde el navegador directamente
# ===============================
@auth_bp.route("/register", methods=["GET"])
def register_get():
    # Acceso directo por URL → redirige al login
    return redirect(url_for("auth.login"))


# ===============================
# CHECK ROLE (API JSON — tiempo real)
# Consulta el rol actual del usuario en la BD y actualiza la sesión.
# Llamado periódicamente desde el frontend para detectar cambios de rol
# sin necesidad de cerrar sesión.
#
# Devuelve: { "role": "admin" | "user" }
# Redirige a /login si el usuario no está logueado.
# ===============================
@auth_bp.route('/check_role')
def check_role():

    # El usuario debe estar logueado para consultar su rol
    if 'user_id' not in session:
        return jsonify({'error': 'not_authenticated'}), 401

    # Consulta el rol actual directamente en la BD (ignora la sesión cacheada)
    current_role = get_user_role(session['user_id'])

    # Si el usuario ya no existe en la BD (fue eliminado) → cierra la sesión
    if current_role is None:
        session.pop('user_id',  None)
        session.pop('username', None)
        session.pop('role',     None)
        return jsonify({'error': 'user_deleted'}), 404

    # Comprueba si el usuario tiene un ban activo en este momento
    banned_until = get_user_ban(session['user_id'])
    if banned_until and banned_until > datetime.now():
        session.pop('user_id',  None)
        session.pop('username', None)
        session.pop('role',     None)
        return jsonify({
            'error':        'user_banned',
            'banned_until': banned_until.strftime('%d/%m/%Y %H:%M')
        }), 403

    # Sincroniza la sesión con el valor real de la BD
    session['role'] = current_role

    return jsonify({'role': current_role})


# ===============================
# LOGOUT
# Limpia todos los datos de sesión y redirige al login
# ===============================
@auth_bp.route('/logout')
def logout():

    # Elimina cada clave de sesión de forma segura (None si no existe)
    session.pop('user_id',  None)
    session.pop('username', None)
    session.pop('role',     None)

    # Redirige al formulario de login
    return redirect(url_for('auth.login'))