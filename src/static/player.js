document.addEventListener("DOMContentLoaded", () => {

    const player = document.getElementById("player");
    const audioSource = document.getElementById("audioSource");
    const currentSongTitle = document.getElementById("currentSongTitle");

    let currentSongIndex = 0;
    let shuffle = false;
    let loop = false;

    // ===============================
    // LOAD SONG
    // ===============================
    function loadSong(index) {
        if (!songs || songs.length === 0) return;

        if (index < 0) currentSongIndex = songs.length - 1;
        else if (index >= songs.length) currentSongIndex = 0;
        else currentSongIndex = index;

        if (audioSource && player) {
            audioSource.src = "/play/" + encodeURIComponent(songs[currentSongIndex]);
            player.load();
            player.play();
        }

        if (currentSongTitle) currentSongTitle.textContent = songs[currentSongIndex];
        document.title = songs[currentSongIndex];

        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: songs[currentSongIndex],
                artist: "Koan",
                album: "MusicCloudServer",
                artwork: [{ src: "https://via.placeholder.com/96", sizes: "96x96", type: "image/png" }]
            });

            navigator.mediaSession.setActionHandler('play', () => player && player.play());
            navigator.mediaSession.setActionHandler('pause', () => player && player.pause());
            navigator.mediaSession.setActionHandler('previoustrack', () => handlePreviousClick());
            navigator.mediaSession.setActionHandler('nexttrack', () => handleNextClick());
        }
    }

    // ===============================
    // CONTROLS
    // ===============================
    function playPause() { if (player) player.paused ? player.play() : player.pause(); }

    function handleNextClick() {
        if (!songs || songs.length === 0) return;

        if (shuffle) {
            let newIndex;
            do { newIndex = Math.floor(Math.random() * songs.length); }
            while (newIndex === currentSongIndex && songs.length > 1);
            currentSongIndex = newIndex;
        } else {
            currentSongIndex++;
            if (currentSongIndex >= songs.length) currentSongIndex = 0;
        }
        loadSong(currentSongIndex);
    }

    function handlePreviousClick() {
        if (!songs || songs.length === 0 || !player) return;

        if (player.currentTime > 3) player.currentTime = 0;
        else {
            if (shuffle) {
                let newIndex;
                do { newIndex = Math.floor(Math.random() * songs.length); }
                while (newIndex === currentSongIndex && songs.length > 1);
                currentSongIndex = newIndex;
            } else {
                currentSongIndex--;
                if (currentSongIndex < 0) currentSongIndex = songs.length - 1;
            }
            loadSong(currentSongIndex);
        }
    }

    function toggleShuffle() {
        shuffle = !shuffle;
        const elem = document.getElementById("shuffleStatus");
        if (elem) elem.textContent = shuffle ? "Activado" : "Desactivado";
    }

    function toggleLoop() {
        loop = !loop;
        if (player) player.loop = loop;
        const elem = document.getElementById("loopStatus");
        if (elem) elem.textContent = loop ? "Activado" : "Desactivado";
    }

    // ===============================
    // SEARCH
    // ===============================
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const songList = document.getElementById("songList");
    const resetSearch = document.getElementById("resetSearch");

    if (searchForm && searchInput && songList) {
        searchForm.addEventListener("submit", (e) => {
            e.preventDefault();
            const query = searchInput.value.toLowerCase();
            const items = songList.querySelectorAll(".song-item");
            items.forEach(item => {
                const titleEl = item.querySelector(".song-title");
                const title = titleEl ? titleEl.textContent.toLowerCase() : "";
                item.style.display = title.includes(query) ? "" : "none";
            });
            const firstVisible = songList.querySelector(".song-item:not([style*='display: none']) .song-title");
            if (firstVisible) playSongByName(firstVisible.textContent);
        });
    }

    if (resetSearch && songList && searchInput) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item").forEach(item => item.style.display = "");
        });
    }

    // ===============================
    // PLAYLIST ADD/REMOVE
    // ===============================
    document.querySelectorAll(".add-to-playlist").forEach(container => {
        const addBtn = container.querySelector(".add-btn");
        const select = container.querySelector(".playlist-select");
        if (!addBtn || !select) return;

        addBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            const isOpen = select.style.display === "inline-block";
            document.querySelectorAll(".playlist-select").forEach(s => s.style.display = "none");
            if (!isOpen) select.style.display = "inline-block";
        });

        select.addEventListener("click", e => e.stopPropagation());

        select.addEventListener("change", async () => {
            const playlistId = select.value;
            if (!playlistId) return;
            const songItem = container.closest(".song-item");
            const filename = songItem ? songItem.dataset.filename : null;
            if (!filename) return;

            try {
                const res = await fetch("/add_to_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename, playlist_id: playlistId })
                });
                const data = await res.json();
                if (data.success) alert(`"${filename}" añadida a la playlist`);
                else alert(`Error: ${data.error}`);
            } catch (err) { alert("Error al añadir la canción: " + err); }

            select.style.display = "none";
            select.selectedIndex = 0;
        });
    });

    // ===============================
    // ELIMINAR PLAYLIST
    // ===============================
    document.querySelectorAll(".delete-playlist-btn").forEach(btn => {
        btn.addEventListener("click", async (e) => {
            e.preventDefault();
            const playlistId = btn.dataset.playlist;

            if (!confirm("¿Seguro que quieres eliminar esta playlist?")) return;

            try {
                const res = await fetch("/delete_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ playlist_id: playlistId })
                });

                const data = await res.json();

                if (data.success) {
                    const li = btn.closest(".playlist-item");
                    if (li) li.remove();
                } else {
                    alert("Error: " + data.error);
                }

            } catch (err) {
                alert("Error al eliminar playlist: " + err);
            }
        });
    });

    document.addEventListener("click", () => {
        document.querySelectorAll(".playlist-select").forEach(s => s.style.display = "none");
    });

    document.querySelectorAll(".remove-from-playlist").forEach(btn => {
        btn.addEventListener("click", async () => {
            const filename = btn.dataset.filename;
            const playlistId = btn.dataset.playlist;
            if(!confirm(`Quitar "${filename}" de la playlist?`)) return;

            try {
                const res = await fetch("/remove_from_playlist", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename, playlist_id: playlistId })
                });
                const data = await res.json();
                if(data.success){
                    const songItem = btn.closest(".song-item");
                    if(songItem) songItem.remove();
                    location.reload();
                } else alert(data.error);
            } catch(err){ alert("Error: " + err); }
        });
    });

    // ===============================
    // DELETE SONGS FROM INDEX
    // ===============================
    if (songList) {
        songList.addEventListener("click", async (e) => {
            if (!e.target.classList.contains("delete-song-btn")) return;

            const btn = e.target;
            const filename = btn.dataset.filename;
            if (!filename) return;

            const confirmDelete = confirm(`¿Estás seguro de que quieres borrar "${filename}"?`);
            if (!confirmDelete) return;

            try {
                const res = await fetch("/delete_song", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ filename })
                });

                const data = await res.json();

                if (data.success) {
                    const songItem = btn.closest(".song-item");
                    if (songItem) songItem.remove();
                    songs = songs.filter(s => s !== filename);
                    alert(`"${filename}" borrada correctamente`);
                } else {
                    alert(`Error: ${data.error}`);
                }
            } catch (err) {
                alert(`Error al borrar la canción: ${err}`);
            }
        });
    }

    // ===============================
    // BAN INLINE
    // ===============================
    document.querySelectorAll(".ban").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const form = btn.closest("form");
            const input = form.querySelector(".ban-hours-input");
            if (!input) return;

            if (input.style.display === "none") {
                input.style.display = "inline-block";
                input.focus();
            } else {
                if (input.value.trim() === "" || Number(input.value) <= 0) {
                    alert("Introduce un número válido de horas");
                    input.focus();
                    return;
                }
                form.submit(); 
            }
        });
    });

    // ===============================
    // CHANGE PASSWORD INLINE
    // ===============================
    document.addEventListener("click", (e) => {
        if (e.target.classList.contains("change-password-btn")) {
            const form = e.target.closest("form");
            if (!form) return;
            const input = form.querySelector(".password-input");
            if (!input) return;

            if (!input.style.display || input.style.display === "none") {
                input.style.display = "inline-block";
                input.focus();
            } else {
                if(input.value.trim() === "") {
                    alert("Introduce una contraseña válida");
                    input.focus();
                    return;
                }
                form.submit();
            }
        }
    });

    // ===============================
    // SELECT ROLE INLINE
    // ===============================

    document.querySelectorAll(".role-btn").forEach(btn => {
        btn.addEventListener("click", e => {
            const form = btn.closest(".role-form");
            const select = form.querySelector(".role-select");

            if (!select.style.display || select.style.display === "none") {
                select.style.display = "inline-block";
                select.focus();
            } else {
                if (!select.value) {
                    alert("Selecciona un rol válido");
                    select.focus();
                    return;
                }
                form.submit();
            }
        });
    });

    document.querySelectorAll(".role-select").forEach(select => {
        select.addEventListener("click", e => e.stopPropagation());
    });

    // ===============================
    // RENOMBRAR PLAYLIST INLINE
    // ===============================
    document.querySelectorAll(".rename-playlist-btn").forEach(btn => {

        btn.addEventListener("click", async () => {

            const playlistId = btn.dataset.playlist
            const li = btn.closest(".playlist-item")
            const nameElement = li.querySelector(".playlist-name")
            const input = li.querySelector(".rename-input")

            if (input.style.display === "none") {

                input.value = nameElement.textContent
                input.style.display = "inline-block"
                input.focus()

                return
            }

            const newName = input.value.trim()

            if (!newName) {
                alert("Nombre inválido")
                return
            }

            try {

                const res = await fetch("/rename_playlist", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        playlist_id: playlistId,
                        name: newName
                    })
                })

                const data = await res.json()

                if (data.success) {

                    nameElement.textContent = newName
                    input.style.display = "none"

                } else {

                    alert(data.error)

                }

            } catch(err){

                alert("Error: " + err)

            }

        })

    })

    // ===============================
    // SYSTEM STATS CHARTS (CPU / RAM / DISCO / RED)
    // ===============================
    if (window.systemStats) {

        function createChart(id, value, color) {
            return new Chart(document.getElementById(id), {
                type: "doughnut",
                data: {
                    datasets: [{
                        data: [value, 100 - value],
                        backgroundColor: [color, "#333"]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } }
                }
            });
        }

        const cpuChart = createChart("cpuChart", window.systemStats.cpu, "#ff6384");
        const ramChart = createChart("ramChart", window.systemStats.ram_percent, "#36a2eb");
        const diskChart = createChart("diskChart", window.systemStats.disk_percent, "#ffce56");
        const netUpChart = createChart("netUpChart", 0, "#4bc0c0");
        const netDownChart = createChart("netDownChart", 0, "#ff9f40");

        const netUpText = document.getElementById("netUpText");
        const netDownText = document.getElementById("netDownText");

        let lastSent = window.systemStats.net_sent;
        let lastRecv = window.systemStats.net_recv;

        async function updateSystemStats() {
            try {
                const res = await fetch("/admin/system_stats");
                const data = await res.json();

                // CPU
                cpuChart.data.datasets[0].data[0] = data.cpu;
                cpuChart.data.datasets[0].data[1] = 100 - data.cpu;
                cpuChart.update();

                // RAM
                ramChart.data.datasets[0].data[0] = data.ram_percent;
                ramChart.data.datasets[0].data[1] = 100 - data.ram_percent;
                ramChart.update();

                // DISCO
                diskChart.data.datasets[0].data[0] = data.disk_percent;
                diskChart.data.datasets[0].data[1] = 100 - data.disk_percent;
                diskChart.update();

                // RED
                const upload = ((data.net_sent - lastSent) / 1024 / 1024).toFixed(2);
                const download = ((data.net_recv - lastRecv) / 1024 / 1024).toFixed(2);

                lastSent = data.net_sent;
                lastRecv = data.net_recv;

                netUpChart.data.datasets[0].data[0] = Math.min(upload * 5, 100);
                netUpChart.data.datasets[0].data[1] = 100 - netUpChart.data.datasets[0].data[0];
                netUpChart.update();

                netDownChart.data.datasets[0].data[0] = Math.min(download * 5, 100);
                netDownChart.data.datasets[0].data[1] = 100 - netDownChart.data.datasets[0].data[0];
                netDownChart.update();

                if (netUpText) netUpText.textContent = `${upload} MB/s`;
                if (netDownText) netDownText.textContent = `${download} MB/s`;

                if (document.getElementById("cpuText")) document.getElementById("cpuText").textContent = `${data.cpu}%`;
                if (document.getElementById("ramText")) document.getElementById("ramText").textContent = `${data.ram_used} / ${data.ram_total} GB (${data.ram_percent}%)`;
                if (document.getElementById("diskText")) document.getElementById("diskText").textContent = `${data.disk_used} / ${data.disk_total} GB (${data.disk_percent}%)`;

            } catch (err) {
                console.error("Error al actualizar stats:", err);
            }
        }

        setInterval(updateSystemStats, 1000);
    }

    document.addEventListener("DOMContentLoaded", () => {

        const youtubeSearchInput = document.getElementById("youtube-search-input");
        const youtubeSearchBtn = document.getElementById("youtube-search-btn");
        const youtubeResultsList = document.getElementById("youtube-results");
        const youtubePlayer = document.getElementById("youtube-player");
        const nowPlaying = document.getElementById("now-playing");

        async function searchYoutube(){
            const query = youtubeSearchInput.value.trim();
            if(!query) return;

            try {
                const res = await fetch("/youtube_search", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ query })
                });

                const data = await res.json();
                if(!data.success){ alert(data.error); return; }
                showYoutubeResults(data.results);

            } catch(err){ console.error(err); }
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

                li.appendChild(title);
                li.appendChild(playBtn);
                youtubeResultsList.appendChild(li);
            });
        }

        async function playYoutube(url, title){
            try {
                const res = await fetch("/youtube_audio", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({ url })
                });

                const data = await res.json();
                if(!data.success){ alert(data.error); return; }

                // Adaptado a tu player principal
                if(youtubePlayer){
                    youtubePlayer.src = data.audio;
                    youtubePlayer.play();
                }

                if(nowPlaying) nowPlaying.textContent = "Reproduciendo: " + title;

            } catch(err){ console.error(err); }
        }

        if(youtubeSearchBtn)
            youtubeSearchBtn.addEventListener("click", searchYoutube);

        if(youtubeSearchInput)
            youtubeSearchInput.addEventListener("keypress", e => { if(e.key === "Enter") searchYoutube(); });

    });

    // ===============================
    // EXPOSE FUNCTIONS
    // ===============================
    window.playSongByName = function(name) {
        if (!songs) return;
        const index = songs.findIndex(s => s.toLowerCase() === name.toLowerCase());
        if (index !== -1) loadSong(index);
    };

    window.loadSong = loadSong;
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    if (player) {
        player.addEventListener("ended", () => {
            if (loop) loadSong(currentSongIndex);
            else handleNextClick();
        });
    }

    if (player && songs && songs.length > 0) loadSong(0);

    setInterval(updateServerStats, 5000);

});