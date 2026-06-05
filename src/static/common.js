// =============================================================================
// common.js — Utilidades compartidas entre todas las páginas
// Usado en: index.html, playlists.html, upload.html, youtube.html
// =============================================================================

// Menú móvil (navbar hamburger)
function toggleMobileMenu() {
    const menu = document.getElementById('mobileMenu');
    if (menu) menu.classList.toggle('show');
}

window.toggleMobileMenu = toggleMobileMenu;
window.toggleMenu = toggleMobileMenu;

document.addEventListener('click', function (e) {
    const menu = document.getElementById('mobileMenu');
    const btn  = document.querySelector('.menu-toggle-btn');
    if (!menu || !btn) return;
    if (!menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('show');
    }
});
