document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("youtube-search-input");
    const button = document.getElementById("youtube-search-btn");
    const results = document.getElementById("youtube-results");
    const player = document.getElementById("youtube-player");
    const nowPlaying = document.getElementById("now-playing");
    const loopBtn = document.getElementById("youtube-loop-btn");
    const loopStatus = document.getElementById("loopSongStatus");

    let loopSong = false;

    // Activar/desactivar bucle
    loopBtn.addEventListener("click", () => {
        loopSong = !loopSong;
        loopStatus.textContent = loopSong ? "Activado" : "Desactivado";
    });

    // Buscar en YouTube
    button.addEventListener("click", searchYoutube);
    input.addEventListener("keypress", e => {
        if(e.key === "Enter") searchYoutube();
    });

    async function searchYoutube() {
        const query = input.value.trim();
        if(!query) return;

        try {
            const res = await fetch("/youtube_search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            const data = await res.json();

            if(!data.success) {
                alert(data.error);
                return;
            }

            results.innerHTML = "";
            data.results.forEach(video => {
                const li = document.createElement("li");
                li.className = "youtube-video-item";

                li.innerHTML = `<span>${video.title}</span> <button>▶</button>`;
                li.querySelector("button").addEventListener("click", () => {
                    playVideo(video.url, video.title);
                });

                results.appendChild(li);
            });

        } catch(err) {
            console.error(err);
            alert("Error buscando en YouTube");
        }
    }

    async function playVideo(url, title) {
        try {
            const res = await fetch("/youtube_audio", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ url })
            });
            const data = await res.json();

            if(!data.success) {
                alert(data.error);
                return;
            }

            // Cambiar fuente y reproducir
            player.src = data.audio;
            player.play();

            nowPlaying.textContent = "Reproduciendo: " + title;

        } catch(err) {
            console.error(err);
            alert("Error reproduciendo video");
        }
    }

    // Manejar fin de canción para bucle
    player.addEventListener("ended", () => {
        if(loopSong) {
            player.currentTime = 0;
            player.play();
        }
    });
});