// =============================================================================
// session_guard.js — Vigilancia de sesión en tiempo real (todas las pantallas)
//
// Responsabilidades:
//   - Detectar en tiempo real si el usuario ha sido eliminado de la BD
//   - Detectar en tiempo real si el usuario ha sido baneado
//   - Detectar cambios de rol (admin ↔ user) y actualizar el botón del panel
//
// Cómo funciona:
//   Hace polling a /check_role cada 5 segundos.
//   El servidor consulta la BD en cada llamada y devuelve el estado real.
//
// Respuestas del servidor:
//   200 { role }         → OK, sincroniza el botón "Panel admin" si existe
//   401                  → sesión expirada / no autenticado → redirige a /login
//   403 { banned_until } → usuario baneado → alerta + logout
//   404                  → usuario eliminado → logout
//
// Incluir en todas las plantillas protegidas (excepto login):
//   <script src="{{ url_for('static', filename='session_guard.js') }}"></script>
// =============================================================================

(function () {

    // ===============================
    // SINCRONIZAR BOTÓN "PANEL ADMIN"
    // Muestra u oculta el botón según el rol recibido del servidor.
    // Solo actúa si existe un dropdown de navegación en la página actual.
    // ===============================
    function syncAdminButton(role) {
        const adminBtn = document.querySelector(".dropdown-menu button[onclick*='admin']");

        if (role === "admin") {
            // Crea el botón si no existe
            if (!adminBtn) {
                const newBtn = document.createElement("button");
                newBtn.textContent = "Panel admin";
                newBtn.setAttribute("onclick", "location.href='/admin/'");

                const dropdown = document.getElementById("dropdownMenu");
                if (dropdown) dropdown.insertBefore(newBtn, dropdown.firstChild);
            }
        } else {
            // Elimina el botón si existe
            if (adminBtn) adminBtn.remove();
        }
    }

    // ===============================
    // POLLING PRINCIPAL
    // ===============================
    function pollRole() {
        fetch("/check_role")
            .then(function (res) {

                // Sesión expirada o no autenticado
                if (res.status === 401) {
                    window.location.href = "/login";
                    return null;
                }

                // Usuario eliminado de la BD
                if (res.status === 404) {
                    window.location.href = "/logout";
                    return null;
                }

                // Usuario baneado mientras estaba logueado
                if (res.status === 403) {
                    return res.json().then(function (data) {
                        const hasta = data.banned_until || "";
                        alert("Tu cuenta ha sido baneada hasta el " + hasta + ". Serás desconectado.");
                        window.location.href = "/logout";
                    });
                }

                return res.json();
            })
            .then(function (data) {
                if (data && data.role !== undefined) {
                    syncAdminButton(data.role);
                }
            })
            .catch(function () {
                // Error de red — se reintenta en el siguiente ciclo
            });
    }

    // Primera comprobación al cargar la página
    document.addEventListener("DOMContentLoaded", function () {
        pollRole();
        setInterval(pollRole, 5000);
    });

})();
