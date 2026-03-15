document.addEventListener("DOMContentLoaded", () => {

    const youtubeSearchInput = document.getElementById("youtube-search-input");
    const youtubeSearchBtn = document.getElementById("youtube-search-btn");
    const youtubeResultsList = document.getElementById("youtube-results");
    const youtubePlayer = document.getElementById("youtube-player");
    const nowPlaying = document.getElementById("now-playing");
    const loopBtn = document.getElementById("youtube-loop-btn");
    const loopStatusElem = document.getElementById("loopSongStatus");
    const songList = document.getElementById("songList");

    let loopSong = false;

    // ===============================
    // LOOP CONTROL
    // ===============================
    function toggleLoopSong() {
        loopSong = !loopSong;
        if (youtubePlayer) youtubePlayer.loop = loopSong;
        if (loopStatusElem) loopStatusElem.textContent = loopSong ? "Activado" : "Desactivado";
    }

    if(loopBtn) loopBtn.addEventListener("click", toggleLoopSong);

    if (youtubePlayer) {
        youtubePlayer.addEventListener("ended", () => {
            if(loopSong) {
                youtubePlayer.currentTime = 0;
                youtubePlayer.play();
            }
        });
    }

    // ===============================
    // YOUTUBE SEARCH
    // ===============================
    async function searchYoutube() {
        const query = youtubeSearchInput.value.trim();
        if(!query) return;

        try {
            const res = await fetch("/youtube_search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });

            const data = await res.json();
            if(!data.success){ 
                alert(data.error); 
                return; 
            }

            showYoutubeResults(data.results);

        } catch(err) {
            console.error(err);
            alert("Error al buscar en YouTube: " + err);
        }
    }

    function showYoutubeResults(videos){
        youtubeResultsList.innerHTML = "";

        videos.forEach(video => {
            const li = document.createElement("li");
            li.className = "youtube-video-item";

            const title = document.createElement("span");
            title.className = "youtube-video-title";
            title.textContent = video.title;

            const playBtn = document.createElement("button");
            playBtn.className = "youtube-play-btn";
            playBtn.textContent = "▶";
            playBtn.onclick = () => playYoutube(video.url, video.title);

            const downloadBtn = document.createElement("button");
            downloadBtn.className = "youtube-download-btn";
            downloadBtn.textContent = "⬇ Descargar";
            downloadBtn.onclick = async () => {
                try {
                    const res = await fetch("/youtube_download", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ url: video.url })
                    });
                    const data = await res.json();
                    if(!data.success){
                        alert("Error: " + data.error);
                        return;
                    }

                    alert(`"${data.filename}" descargada correctamente`);

                    // Agregar a la lista de canciones en la UI
                    const liSong = document.createElement("li");
                    liSong.className = "song-item";
                    liSong.dataset.filename = data.filename;
                    liSong.innerHTML = `
                        <span class="song-title" onclick="loadSong(${songs.length})">${data.filename}</span>
                        <div class="song-actions">
                            <button class="download-song-btn" data-filename="${data.filename}">Descargar</button>
                        </div>
                    `;
                    if (songList) songList.appendChild(liSong);
                    songs.push(data.filename);

                    // Guardar en la base de datos vía backend
                    await fetch("/add_song_to_db", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ filename: data.filename, title: video.title })
                    });

                } catch(err){
                    alert("Error al descargar: " + err);
                }
            };

            li.appendChild(title);
            li.appendChild(playBtn);
            li.appendChild(downloadBtn);
            youtubeResultsList.appendChild(li);
        });
    }

    // ===============================
    // PLAY YOUTUBE AUDIO
    // ===============================
    async function playYoutube(url, title){
        try {
            const res = await fetch("/youtube_audio", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });

            const data = await res.json();
            if(!data.success){ 
                alert(data.error); 
                return; 
            }

            if(youtubePlayer){
                youtubePlayer.src = data.audio;
                youtubePlayer.play();
            }

            if(nowPlaying) nowPlaying.textContent = "Reproduciendo: " + title;

        } catch(err){
            console.error(err);
            alert("Error al reproducir: " + err);
        }
    }

    // ===============================
    // EVENT LISTENERS
    // ===============================
    if(youtubeSearchBtn) 
        youtubeSearchBtn.addEventListener("click", searchYoutube);

    if(youtubeSearchInput) 
        youtubeSearchInput.addEventListener("keypress", e => { if(e.key === "Enter") searchYoutube(); });

});