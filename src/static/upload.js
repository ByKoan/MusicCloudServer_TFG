// =============================================================================
// upload.js — Página de subida de canciones
// Usado en: upload.html
//
// Responsabilidades:
//   - Drag & drop de archivos de audio
//   - Vista previa de archivos seleccionados (lista de pills)
//   - Simulación de barra de progreso durante el envío del formulario
//   - Limpiar la selección de archivos
//
// Nota: La subida real del archivo se gestiona por el formulario HTML
// (multipart/form-data hacia POST /upload). common.js gestiona el menú móvil.
// =============================================================================

document.addEventListener('DOMContentLoaded', function () {

    const fileInput     = document.getElementById('fileInput');
    const fileList      = document.getElementById('fileList');
    const uploadActions = document.getElementById('uploadActions');
    const dropZone      = document.getElementById('dropZone');

    if (!fileInput) return;

    fileInput.addEventListener('change', function () {
        renderFiles(fileInput.files);
    });

    function renderFiles(files) {
        fileList.innerHTML = '';
        if (!files || files.length === 0) {
            uploadActions.style.display = 'none';
            return;
        }
        Array.from(files).forEach(function (f, i) {
            const div = document.createElement('div');
            div.className = 'file-pill';
            div.style.animationDelay = (i * 0.04) + 's';
            div.innerHTML =
                '<span class="fp-icon">🎵</span>' +
                '<span class="fp-name">' + f.name + '</span>' +
                '<span class="fp-size">' + (f.size / 1024 / 1024).toFixed(1) + ' MB</span>';
            fileList.appendChild(div);
        });
        uploadActions.style.display = 'flex';
    }

    window.clearFiles = function () {
        fileInput.value = '';
        fileList.innerHTML = '';
        uploadActions.style.display = 'none';
    };

    // Drag & drop
    dropZone.addEventListener('dragover', function (e) {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    dropZone.addEventListener('dragleave', function () {
        dropZone.classList.remove('drag-over');
    });
    dropZone.addEventListener('drop', function (e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        renderFiles(e.dataTransfer.files);
    });

    // Barra de progreso al enviar
    const form = document.getElementById('uploadForm');
    if (form) {
        form.addEventListener('submit', function () {
            const wrap = document.getElementById('progressWrap');
            const bar  = document.getElementById('progressBarInner');
            if (!wrap || !bar) return;
            wrap.style.display = 'block';
            let p = 0;
            const iv = setInterval(function () {
                p += 5;
                bar.style.width = Math.min(p, 90) + '%';
                if (p >= 90) clearInterval(iv);
            }, 150);
        });
    }
});
