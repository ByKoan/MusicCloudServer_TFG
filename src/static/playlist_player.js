document.addEventListener("DOMContentLoaded", () => {

    function getSongs() {
        return window.songs || [];
    }

    const player = document.getElementById("player");
    const audioSource = document.getElementById("audioSource");
    const currentSongTitle = document.getElementById("currentSongTitle");
    const songList = document.getElementById("songList");

    let currentSongIndex = 0;
    let shuffle = false;
    let loop = false;

    // ===============================
    // LOAD SONG
    // ===============================
    function loadSong(index) {
        const songs = getSongs();
        if (!songs.length || !player || !audioSource) return;

        if (index < 0) index = songs.length - 1;
        if (index >= songs.length) index = 0;

        currentSongIndex = index;

        const song = songs[currentSongIndex];

        audioSource.src = "/play/" + encodeURIComponent(song);
        player.load();

        player.play().catch(() => {});

        if (currentSongTitle)
            currentSongTitle.textContent = song;

        document.title = song;
    }

    // ===============================
    // CONTROLS
    // ===============================
    function playPause() {
        if (!player) return;
        player.paused ? player.play() : player.pause();
    }

    function handleNextClick() {
        const songs = getSongs();
        if (!songs.length) return;

        if (shuffle)
            currentSongIndex = Math.floor(Math.random() * songs.length);
        else
            currentSongIndex = (currentSongIndex + 1) % songs.length;

        loadSong(currentSongIndex);
    }

    function handlePreviousClick() {
        const songs = getSongs();
        if (!songs.length || !player) return;

        if (player.currentTime > 3) {
            player.currentTime = 0;
            return;
        }

        currentSongIndex--;
        if (currentSongIndex < 0)
            currentSongIndex = songs.length - 1;

        loadSong(currentSongIndex);
    }

    function toggleShuffle() {
        shuffle = !shuffle;
        document.getElementById("shuffleStatus").textContent =
            shuffle ? "Activado" : "Desactivado";
    }

    function toggleLoop() {
        loop = !loop;
        player.loop = loop;

        document.getElementById("loopStatus").textContent =
            loop ? "Activado" : "Desactivado";
    }

    // ===============================
    // CLICK SONG
    // ===============================
    function playSongByName(name) {
        const index = getSongs()
            .findIndex(s => s.toLowerCase() === name.toLowerCase());

        if (index !== -1)
            loadSong(index);
    }

    if (songList) {
        songList.addEventListener("click", e => {

            const title = e.target.closest(".song-title");
            if (!title) return;

            playSongByName(title.textContent.trim());
        });
    }

    // ===============================
    // SEARCH
    // ===============================
    const searchForm = document.getElementById("searchForm");
    const searchInput = document.getElementById("searchInput");
    const resetSearch = document.getElementById("resetSearch");

    if (searchForm && searchInput && songList) {
        searchForm.addEventListener("submit", e => {
            e.preventDefault();

            const query = searchInput.value.toLowerCase();

            songList.querySelectorAll(".song-item").forEach(item => {
                const title = item.querySelector(".song-title")
                    .textContent.toLowerCase();

                item.style.display =
                    title.includes(query) ? "" : "none";
            });
        });
    }

    if (resetSearch) {
        resetSearch.addEventListener("click", () => {
            searchInput.value = "";
            songList.querySelectorAll(".song-item")
                .forEach(i => i.style.display = "");
        });
    }

    // ===============================
    // EXPORT GLOBAL
    // ===============================
    window.playPause = playPause;
    window.handleNextClick = handleNextClick;
    window.handlePreviousClick = handlePreviousClick;
    window.toggleShuffle = toggleShuffle;
    window.toggleLoop = toggleLoop;

    // ===============================
    // INITIAL LOAD
    // ===============================
    if (player && getSongs().length > 0)
        loadSong(0);

});