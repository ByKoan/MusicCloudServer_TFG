// =============================================================================
// session_guard.js — Vigilancia de sesión en tiempo real (todas las pantallas)
//
// Responsabilidades:
//   - Detectar en tiempo real si el usuario ha sido eliminado de la BD
//   - Detectar en tiempo real si el usuario ha sido baneado
//   - Detectar cambios de rol (admin ↔ user) y actualizar el menú al instante
//
// Cómo funciona:
//   Hace polling a /check_role cada 5 segundos.
//   El servidor consulta la BD en cada llamada y devuelve el estado real.
//
// Respuestas del servidor:
//   200 { role }         → OK, sincroniza el botón "Panel admin" si el rol cambió
//   401                  → sesión expirada / no autenticado → redirige a /login
//   403 { banned_until } → usuario baneado → muestra overlay de baneo en pantalla
//   404                  → usuario eliminado → muestra overlay de cuenta eliminada
//
// Incluir en todas las plantillas protegidas (excepto login):
//   <script src="{{ url_for('static', filename='session_guard.js') }}"></script>
// =============================================================================

(function () {

    'use strict';

    // Evita inicializar el guard más de una vez
    if (window.__sessionGuardActive) return;
    window.__sessionGuardActive = true;

    // ============================================================
    // OVERLAY GENÉRICO
    // ============================================================
    function showOverlay(iconHTML, title, message, buttonText, buttonHref) {
        if (document.getElementById('sg-overlay')) return;

        var overlay = document.createElement('div');
        overlay.id = 'sg-overlay';
        overlay.style.cssText = [
            'position:fixed',
            'inset:0',
            'z-index:99999',
            'display:flex',
            'align-items:center',
            'justify-content:center',
            'background:rgba(0,0,0,0.92)',
            'backdrop-filter:blur(6px)',
            '-webkit-backdrop-filter:blur(6px)',
            'font-family:system-ui,-apple-system,sans-serif'
        ].join(';');

        var card = document.createElement('div');
        card.style.cssText = [
            'background:#1a1a2e',
            'border:1px solid rgba(255,255,255,0.08)',
            'border-radius:16px',
            'padding:48px 40px',
            'text-align:center',
            'max-width:420px',
            'width:90%',
            'box-shadow:0 24px 64px rgba(0,0,0,0.6)'
        ].join(';');

        var iconEl = document.createElement('div');
        iconEl.innerHTML = iconHTML;
        iconEl.style.cssText = 'font-size:56px;margin-bottom:20px;line-height:1';

        var titleEl = document.createElement('h2');
        titleEl.textContent = title;
        titleEl.style.cssText = [
            'color:#fff',
            'font-size:22px',
            'font-weight:700',
            'margin:0 0 12px 0'
        ].join(';');

        var msgEl = document.createElement('p');
        msgEl.innerHTML = message;
        msgEl.style.cssText = [
            'color:#a0a0b8',
            'font-size:15px',
            'line-height:1.6',
            'margin:0 0 32px 0'
        ].join(';');

        var btn = document.createElement('a');
        btn.href = buttonHref;
        btn.textContent = buttonText;
        btn.style.cssText = [
            'display:inline-block',
            'background:#6c63ff',
            'color:#fff',
            'padding:12px 28px',
            'border-radius:8px',
            'font-size:15px',
            'font-weight:600',
            'text-decoration:none'
        ].join(';');
        btn.onmouseover = function () { btn.style.background = '#574fd6'; };
        btn.onmouseout  = function () { btn.style.background = '#6c63ff'; };

        card.appendChild(iconEl);
        card.appendChild(titleEl);
        card.appendChild(msgEl);
        card.appendChild(btn);
        overlay.appendChild(card);
        document.body.appendChild(overlay);

        stopPolling();
    }

    // ============================================================
    // OVERLAY DE BANEO
    // ============================================================
    function showBanOverlay(bannedUntil) {
        var fechaTexto = bannedUntil
            ? 'Tu cuenta est\u00e1 suspendida hasta el <strong style="color:#ff6b6b">' + bannedUntil + '</strong>.'
            : 'Tu cuenta ha sido suspendida temporalmente.';

        showOverlay(
            '\uD83D\uDEAB',
            'Cuenta suspendida',
            fechaTexto + '<br><br>Si crees que es un error, contacta con el administrador.',
            'Ir al inicio de sesi\u00f3n',
            '/logout'
        );
    }

    // ============================================================
    // OVERLAY DE CUENTA ELIMINADA
    // ============================================================
    function showDeletedOverlay() {
        showOverlay(
            '\uD83D\uDDD1\uFE0F',
            'Cuenta eliminada',
            'Tu cuenta ha sido eliminada del sistema.<br><br>Si crees que es un error, contacta con el administrador.',
            'Ir al inicio de sesi\u00f3n',
            '/logout'
        );
    }

    // ============================================================
    // SINCRONIZAR BOTÓN "PANEL ADMIN"
    // ============================================================
    function syncAdminButton(role) {
        var dropdown = document.getElementById('dropdownMenu');
        if (!dropdown) return;

        var adminBtn = document.getElementById('sg-admin-btn');

        if (role === 'admin') {
            if (!adminBtn) {
                var newBtn = document.createElement('button');
                newBtn.id = 'sg-admin-btn';
                newBtn.textContent = 'Panel admin';
                newBtn.setAttribute('onclick', "location.href='/admin/'");
                dropdown.insertBefore(newBtn, dropdown.firstChild);
            }
        } else {
            if (adminBtn) adminBtn.remove();
            // Elimina también el botón renderizado por Jinja si quedara sin id
            dropdown.querySelectorAll('button').forEach(function (btn) {
                var oc = btn.getAttribute('onclick') || '';
                if (oc.indexOf('/admin') !== -1) btn.remove();
            });
            // Si el usuario está en el panel de admin y ha sido degradado, redirigir
            if (window.location.pathname.indexOf('/admin') === 0) {
                stopPolling();
                window.location.href = '/';
            }
        }
    }

    // ============================================================
    // CONTROL DEL INTERVALO DE POLLING
    // ============================================================
    var _intervalId = null;

    function stopPolling() {
        if (_intervalId !== null) {
            clearInterval(_intervalId);
            _intervalId = null;
        }
    }

    // ============================================================
    // POLLING PRINCIPAL
    // ============================================================
    function pollRole() {
        fetch('/check_role', { credentials: 'same-origin' })
            .then(function (res) {

                if (res.status === 401) {
                    stopPolling();
                    window.location.href = '/login';
                    return null;
                }

                if (res.status === 404) {
                    showDeletedOverlay();
                    return null;
                }

                if (res.status === 403) {
                    return res.json().then(function (data) {
                        showBanOverlay(data.banned_until || null);
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

    // ============================================================
    // INICIALIZACIÓN
    // ============================================================
    document.addEventListener('DOMContentLoaded', function () {
        // Asigna id al botón admin renderizado por Jinja para no duplicarlo
        var dropdown = document.getElementById('dropdownMenu');
        if (dropdown) {
            dropdown.querySelectorAll('button').forEach(function (btn) {
                var oc = btn.getAttribute('onclick') || '';
                if (oc.indexOf('/admin') !== -1) {
                    btn.id = 'sg-admin-btn';
                }
            });
        }

        pollRole();
        _intervalId = setInterval(pollRole, 5000);
    });

})();
