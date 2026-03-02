import os
from flask import Flask, jsonify, redirect, render_template_string, request, send_file, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import mysql.connector
import time

app = Flask(__name__)
app.secret_key = os.urandom(512)  # Clave secreta para manejar sesiones

BASE_MUSIC_FOLDER = r"" # La ruta hacia tu carpeta de la musica
ALLOWED_EXTENSIONS = {'mp3', 'm4a', 'wav'}

def get_db_connection():
    return mysql.connector.connect(
        host="db",          # nombre del servicio docker
        user="musicuser",
        password="musicpass",
        database="musicdb"
    )

def wait_for_db():
    while True:
        try:
            conn = get_db_connection()
            conn.close()
            print("MySQL conectado ✅")
            break
        except Exception as e:
            print("Esperando MySQL...", e)
            time.sleep(2)

def create_user_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def validate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM users WHERE username = %s",
        (username,)
    )

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return True
    return False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_folder = os.path.join(BASE_MUSIC_FOLDER, session['user_id'])
    os.makedirs(user_folder, exist_ok=True)

    if request.method == 'POST':
        if 'file' not in request.files:
            return "No se envió ningún archivo", 400
        
        files = request.files.getlist('file')
        if not files:
            return "No se seleccionaron archivos", 400

        for file in files:
            if file.filename == '': 
                continue
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(user_folder, filename))

        return redirect(url_for('index'))
    return "Sube tus archivos aquí."

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_folder = os.path.join(BASE_MUSIC_FOLDER, session['user_id'])
    os.makedirs(user_folder, exist_ok=True)

    songs = [f for f in os.listdir(user_folder) if allowed_file(f)]

    query = request.args.get('search', '').strip().lower()
    if query:
        songs = [song for song in songs if query in song.lower()]

    current_song = songs[0] if songs else "No hay canciones"

    return render_template_string(TEMPLATE, songs=songs, current_song=current_song)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ current_song }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(to right, #1d2671, #c33764);
            color: #fff;
            text-align: center;
            padding: 20px;
            margin: 0;
        }
        h1 {
            font-size: 40px;
            margin-bottom: 20px;
        }
        audio {
            margin: 20px auto;
            display: block;
            width: 80%;
            max-width: 600px;
        }
        button, .btn {
            background-color: #000;
            border: none;
            color: white;
            padding: 10px 20px;
            font-size: 16px;
            margin: 10px;
            cursor: pointer;
            border-radius: 5px;
            text-decoration: none;
        }
        button:hover, .btn:hover {
            background-color: #333;
        }
        .logout {
            position: absolute;
            top: 20px;
            right: 20px;
            background-color: #ff4c4c;
            color: white;
            font-size: 14px;
            padding: 10px 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .logout:hover {
            background-color: #e43f3f;
        }
        ul {
            list-style: none;
            padding: 0;
            margin: 20px auto;
            max-width: 600px;
        }
        ul li {
            padding: 10px;
            margin: 5px;
            background-color: #000;
            color: white;
            border-radius: 8px;
            text-align: left;
            cursor: pointer;
            display: block;
        }
        ul li:hover {
            background-color: #333;
        }
        ul li a {
            color: white;
            text-decoration: none;
            display: block;
            padding: 10px;
        }
        .file-input-container {
            margin-bottom: 20px;
        }
        input[type="file"] {
            color: black;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            display: inline-block;
        }
        input[type="file"]:hover {
            background-color: #333;
        }
        input[type="file"]::-webkit-file-upload-button {
            background-color: #000;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
        }
        input[type="file"]::-webkit-file-upload-button:hover {
            background-color: #333;
        }
        .search-form {
            margin-bottom: 20px;
        }
        .search-form input[type="text"] {
            padding: 8px;
            font-size: 16px;
            border-radius: 5px;
            border: none;
            width: 60%;
            max-width: 300px;
        }
        /* Estilos para formulario login */
        .login-container {
            max-width: 400px;
            margin: 60px auto;
            background-color: rgba(0, 0, 0, 0.5);
            padding: 30px;
            border-radius: 10px;
        }
        .login-container h2 {
            margin-bottom: 20px;
        }
        .login-container label {
            display: block;
            text-align: left;
            margin-bottom: 5px;
            font-weight: bold;
        }
        .login-container input[type="text"],
        .login-container input[type="password"] {
            width: 100%;
            padding: 10px;
            font-size: 16px;
            margin-bottom: 20px;
            border-radius: 5px;
            border: none;
        }
        .login-container input[type="submit"] {
            width: 100%;
            background-color: #000;
            color: #fff;
            border: none;
            padding: 12px;
            font-size: 18px;
            cursor: pointer;
            border-radius: 5px;
        }
        .login-container input[type="submit"]:hover {
            background-color: #333;
        }
    </style>
</head>
<body>
    {% if session.get('user_id') %}
        <button class="logout" onclick="window.location.href='/logout'">Cerrar sesión</button>
        <h1>Bienvenido, {{ session['user_id'] }}</h1>
        <h2>Canción actual: <span id="currentSongTitle">{{ current_song }}</span></h2>

        <form action="/" method="get" class="search-form">
            <input type="text" name="search" placeholder="Buscar canciones..." value="{{ request.args.get('search', '') }}">
            <button type="submit">Buscar</button>
            <a href="/" class="btn">Reiniciar</a>
        </form>

        <audio id="player" controls autoplay>
            <source id="audioSource" src="" type="audio/mpeg">
            Tu navegador no soporta el elemento de audio.
        </audio>

        <br>
        <button onclick="handlePreviousClick()">⏮️ Anterior</button>
        <button onclick="playPause()">⏯️ Reproducir/Pausa</button>
        <button onclick="handleNextClick()">⏭️ Siguiente</button>
        <br>
        <button onclick="toggleShuffle()">Modo Aleatorio: <span id='shuffleStatus'>Desactivado</span></button>
        <button onclick="toggleLoop()">Modo Bucle: <span id='loopStatus'>Desactivado</span></button>

        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="file-input-container">
                <label for="file" class="file-label">Selecciona archivos para subir:</label>
                <br>
                <input type="file" name="file" multiple>
                <button type="submit">Subir</button>
            </div>
        </form>

        <h2>Lista de Canciones</h2>
        <ul>
            {% for song in songs %}
                <li><a href="javascript:void(0);" onclick="loadSong({{ loop.index0 }})">{{ song }}</a></li>
            {% endfor %}
        </ul>
    {% else %}
        <div class="login-container">
            <h2>Iniciar sesión</h2>
            <form method="post" action="/login">
                <label for="username">Usuario:</label>
                <input type="text" id="username" name="username" autocomplete="username" required
                    oninput="this.value = this.value.toLowerCase()">
                <label for="password">Contraseña:</label>
                <input type="password" id="password" name="password" autocomplete="current-password" required>
                <input type="submit" value="Ingresar">
            </form>
        </div>
    {% endif %}
    <script>
        {% if session.get('user_id') %}
        let songs = {{ songs | tojson }};
        let currentSongIndex = 0;
        let shuffle = false;
        let loop = false;
        const player = document.getElementById('player');
        const audioSource = document.getElementById('audioSource');
        const currentSongTitle = document.getElementById('currentSongTitle');

        function loadSong(index) {
            if (songs.length === 0) return;
            if (index < 0) {
                currentSongIndex = songs.length - 1;
            } else if (index >= songs.length) {
                currentSongIndex = 0;
            } else {
                currentSongIndex = index;
            }
            audioSource.src = "/play/" + encodeURIComponent(songs[currentSongIndex]);
            player.load();
            player.play();
            currentSongTitle.textContent = songs[currentSongIndex];
            document.title = songs[currentSongIndex];

            if ('mediaSession' in navigator) {
                navigator.mediaSession.metadata = new MediaMetadata({
                    title: songs[currentSongIndex],
                    artist: 'Desconocido',
                    album: 'Desconocido',
                    artwork: [
                        { src: 'https://via.placeholder.com/96', sizes: '96x96', type: 'image/png' }
                    ]
                });
            }
        }

        function playPause() {
            if (player.paused) {
                player.play();
            } else {
                player.pause();
            }
        }

        function handleNextClick() {
            if (shuffle) {
                currentSongIndex = Math.floor(Math.random() * songs.length);
            } else {
                currentSongIndex++;
            }
            if (currentSongIndex >= songs.length) currentSongIndex = 0;
            loadSong(currentSongIndex);
        }

        function handlePreviousClick() {
            if (player.currentTime > 3) {
                // Si se ha reproducido más de 3 segundos, reiniciar la canción actual
                player.currentTime = 0;
                player.play();
            } else {
                // Si estamos cerca del principio, ir a la canción anterior
                if (shuffle) {
                    currentSongIndex = Math.floor(Math.random() * songs.length);
                } else {
                    currentSongIndex--;
                }
                if (currentSongIndex < 0) currentSongIndex = songs.length - 1;
                loadSong(currentSongIndex);
            }
        }

        function toggleShuffle() {
            shuffle = !shuffle;
            document.getElementById('shuffleStatus').textContent = shuffle ? 'Activado' : 'Desactivado';
        }

        function toggleLoop() {
            loop = !loop;
            player.loop = loop;
            document.getElementById('loopStatus').textContent = loop ? 'Activado' : 'Desactivado';
        }

        player.addEventListener('ended', () => {
            if (!loop) handleNextClick();
        });

        // Cargar la canción inicial
        loadSong(0);

        // Media Session API para pantalla bloqueo y botones multimedia
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: songs[currentSongIndex],
                artist: 'Desconocido',
                album: 'Desconocido',
                artwork: [
                    { src: 'https://via.placeholder.com/96', sizes: '96x96', type: 'image/png' }
                ]
            });

            navigator.mediaSession.setActionHandler('play', () => { player.play(); });
            navigator.mediaSession.setActionHandler('pause', () => { player.pause(); });
            navigator.mediaSession.setActionHandler('previoustrack', () => { handlePreviousClick(); });
            navigator.mediaSession.setActionHandler('nexttrack', () => { handleNextClick(); });
            navigator.mediaSession.setActionHandler('seekto', (details) => {
                if (details.fastSeek && 'fastSeek' in player) {
                    player.fastSeek(details.seekTime);
                    return;
                }
                player.currentTime = details.seekTime;
            });
        }
        {% endif %}
    </script>
</body>
</html>
"""

@app.route('/play/<filename>')
def play(filename):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_folder = os.path.join(BASE_MUSIC_FOLDER, session['user_id'])
    file_path = os.path.join(user_folder, filename)
    if os.path.isfile(file_path) and allowed_file(filename):
        return send_file(file_path)
    return "Archivo no encontrado", 404

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower() 
        password = request.form.get('password', '').strip()

        if validate_user(username, password):
            session['user_id'] = username
            return redirect(url_for('index'))
        else:
            return render_template_string(TEMPLATE, error="Credenciales incorrectas")

    return render_template_string(TEMPLATE)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    wait_for_db()
    create_user_db()
    app.run(host='0.0.0.0', port=5000)
