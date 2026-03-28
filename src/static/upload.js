// =========================
// MENU DESPLEGABLE HORIZONTAL
// =========================

// Espera a que el DOM cargue completamente
document.addEventListener('DOMContentLoaded', function() {

    // Buscamos todos los toggles y dropdowns (para poder reutilizar en varias páginas)
    const menuToggles = document.querySelectorAll('.menu-toggle');

    menuToggles.forEach(toggle => {

        // Encuentra el dropdown correspondiente dentro del mismo contenedor
        const menuContainer = toggle.closest('.menu-container');
        if (!menuContainer) return;
        const dropdownMenu = menuContainer.querySelector('.dropdown-menu');

        // Mostrar / ocultar el menú al hacer clic
        toggle.addEventListener('click', function(e) {
            e.stopPropagation(); // Evita que el clic se propague al document
            dropdownMenu.classList.toggle('show');
        });

        // Cerrar el menú si se hace clic fuera
        document.addEventListener('click', function(event) {
            if (!menuContainer.contains(event.target)) {
                dropdownMenu.classList.remove('show');
            }
        });

        // Cerrar el menú con la tecla Escape
        document.addEventListener('keydown', function(event) {
            if (event.key === "Escape") {
                dropdownMenu.classList.remove('show');
            }
        });

    });

});