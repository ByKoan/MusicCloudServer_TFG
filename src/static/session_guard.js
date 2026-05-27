// =============================================================================
// session_guard.js — Vigilancia de sesión en tiempo real (todas las pantallas)
//
// Responsabilidades:
//   - Detectar en tiempo real si el usuario ha sido eliminado de la BD
//   - Detectar en tiempo real si el usuario ha sido baneado / desbaneado
//   - Detectar cambios de contraseña y cerrar la sesión automáticamente
//   - Detectar cambios de rol (admin ↔ user) y actualizar el menú al instante
//
// Cómo funciona:
//   Hace polling a /check_role cada 5 segundos.
//   El servidor consulta la BD en cada llamada y devuelve el estado real.
//
// Respuestas del servidor:
//   200 { role }         → OK, sincroniza el botón "Panel admin" si el rol cambió
//   205                  → ban levantado → redirige a /login automáticamente
//   401 not_authenticated → sesión expirada → redirige a /login
//   401 password_changed  → contraseña cambiada → overlay + botón a /login
//   403 { banned_until }  → usuario baneado → overlay (polling CONTINÚA)
//   404                  → usuario eliminado → overlay + botón a /logout
// =============================================================================

(function () {

    'use strict';

    if (window.__sessionGuardActive) return;
    window.__sessionGuardActive = true;

    // ============================================================
    // ESTADO INTERNO
    // ============================================================
    var _intervalId  = null;
    var _banOverlayShown = false;   // true mientras el overlay de ban está visible

    function stopPolling() {
        if (_intervalId !== null) {
            clearInterval(_intervalId);
            _intervalId = null;
        }
    }

    // ============================================================
    // OVERLAY GENÉRICO — para estados TERMINALES (para el polling)
    // ============================================================
    function showFinalOverlay(iconHTML, title, message, buttonText, buttonHref) {
        if (document.getElementById('sg-overlay')) return;

        stopPolling();  // Solo los overlays terminales detienen el polling

        var overlay = document.createElement('div');
        overlay.id = 'sg-overlay';
        overlay.style.cssText = [
            'position:fixed', 'inset:0', 'z-index:99999',
            'display:flex', 'align-items:center', 'justify-content:center',
            'background:rgba(0,0,0,0.92)',
            'backdrop-filter:blur(6px)', '-webkit-backdrop-filter:blur(6px)',
            'font-family:system-ui,-apple-system,sans-serif'
        ].join(';');

        var card = document.createElement('div');
        card.style.cssText = [
            'background:#1a1a2e',
            'border:1px solid rgba(255,255,255,0.08)',
            'border-radius:16px', 'padding:48px 40px',
            'text-align:center', 'max-width:420px', 'width:90%',
            'box-shadow:0 24px 64px rgba(0,0,0,0.6)'
        ].join(';');

        var iconEl = document.createElement('div');
        iconEl.innerHTML = iconHTML;
        iconEl.style.cssText = 'font-size:56px;margin-bottom:20px;line-height:1';

        var titleEl = document.createElement('h2');
        titleEl.textContent = title;
        titleEl.style.cssText = 'color:#fff;font-size:22px;font-weight:700;margin:0 0 12px 0';

        var msgEl = document.createElement('p');
        msgEl.innerHTML = message;
        msgEl.style.cssText = 'color:#a0a0b8;font-size:15px;line-height:1.6;margin:0 0 32px 0';

        var btn = document.createElement('a');
        btn.href = buttonHref;
        btn.textContent = buttonText;
        btn.style.cssText = [
            'display:inline-block', 'background:#6c63ff', 'color:#fff',
            'padding:12px 28px', 'border-radius:8px',
            'font-size:15px', 'font-weight:600', 'text-decoration:none'
        ].join(';');
        btn.onmouseover = function () { btn.style.background = '#574fd6'; };
        btn.onmouseout  = function () { btn.style.background = '#6c63ff'; };

        card.appendChild(iconEl);
        card.appendChild(titleEl);
        card.appendChild(msgEl);
        card.appendChild(btn);
        overlay.appendChild(card);
        document.body.appendChild(overlay);
    }

    // ============================================================
    // OVERLAY DE BANEO — NO terminal: el polling sigue corriendo
    // ============================================================
    function showBanOverlay(bannedUntil) {
        if (_banOverlayShown) return;   // ya visible, no duplicar
        _banOverlayShown = true;

        var overlay = document.createElement('div');
        overlay.id = 'sg-ban-overlay';
        overlay.style.cssText = [
            'position:fixed', 'inset:0', 'z-index:99999',
            'display:flex', 'align-items:center', 'justify-content:center',
            'background:rgba(0,0,0,0.92)',
            'backdrop-filter:blur(6px)', '-webkit-backdrop-filter:blur(6px)',
            'font-family:system-ui,-apple-system,sans-serif'
        ].join(';');

        var card = document.createElement('div');
        card.style.cssText = [
            'background:#1a1a2e',
            'border:1px solid rgba(255,255,255,0.08)',
            'border-radius:16px', 'padding:48px 40px',
            'text-align:center', 'max-width:420px', 'width:90%',
            'box-shadow:0 24px 64px rgba(0,0,0,0.6)'
        ].join(';');

        var iconEl = document.createElement('div');
        iconEl.innerHTML = '\uD83D\uDEAB';
        iconEl.style.cssText = 'font-size:56px;margin-bottom:20px;line-height:1';

        var titleEl = document.createElement('h2');
        titleEl.textContent = 'Cuenta suspendida';
        titleEl.style.cssText = 'color:#fff;font-size:22px;font-weight:700;margin:0 0 12px 0';

        var fechaTexto = bannedUntil
            ? 'Tu cuenta está suspendida hasta el <strong style="color:#ff6b6b">' + bannedUntil + '</strong>.'
            : 'Tu cuenta ha sido suspendida temporalmente.';

        var msgEl = document.createElement('p');
        msgEl.innerHTML = fechaTexto +
            '<br><br>Si crees que es un error, contacta con el administrador.' +
            '<br><br><span style="color:#6c63ff;font-size:13px">' +
            '\u21bb Serás redirigido automáticamente cuando se levante la suspensión.</span>';
        msgEl.style.cssText = 'color:#a0a0b8;font-size:15px;line-height:1.6;margin:0 0 32px 0';

        var btn = document.createElement('a');
        btn.href = '/logout';
        btn.textContent = 'Cerrar sesión';
        btn.style.cssText = [
            'display:inline-block', 'background:#6c63ff', 'color:#fff',
            'padding:12px 28px', 'border-radius:8px',
            'font-size:15px', 'font-weight:600', 'text-decoration:none'
        ].join(';');
        btn.onmouseover = function () { btn.style.background = '#574fd6'; };
        btn.onmouseout  = function () { btn.style.background = '#6c63ff'; };

        card.appendChild(iconEl);
        card.appendChild(titleEl);
        card.appendChild(msgEl);
        card.appendChild(btn);
        overlay.appendChild(card);
        document.body.appendChild(overlay);
        // NOTA: NO se llama a stopPolling() aquí adrede
    }

    function removeBanOverlay() {
        var overlay = document.getElementById('sg-ban-overlay');
        if (overlay) overlay.remove();
        _banOverlayShown = false;
    }

    // ============================================================
    // OVERLAYS TERMINALES ESPECÍFICOS
    // ============================================================
    function showDeletedOverlay() {
        showFinalOverlay(
            '\uD83D\uDDD1\uFE0F',
            'Cuenta eliminada',
            'Tu cuenta ha sido eliminada del sistema.<br><br>Si crees que es un error, contacta con el administrador.',
            'Ir al inicio de sesión',
            '/logout'
        );
    }

    function showPasswordChangedOverlay() {
        showFinalOverlay(
            '\uD83D\uDD12',
            'Sesión cerrada',
            'Tu contraseña ha sido cambiada.<br><br>Inicia sesión de nuevo para continuar.',
            'Ir al inicio de sesión',
            '/login'
        );
    }

    function showUnbannedOverlay() {
        removeBanOverlay();
        showFinalOverlay(
            '\u2705',
            'Suspensión levantada',
            'Tu cuenta ya está desbloqueada.<br><br>Inicia sesión para continuar.',
            'Ir al inicio de sesión',
            '/login'
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
            dropdown.querySelectorAll('button').forEach(function (btn) {
                var oc = btn.getAttribute('onclick') || '';
                if (oc.indexOf('/admin') !== -1) btn.remove();
            });
            if (window.location.pathname.indexOf('/admin') === 0) {
                stopPolling();
                window.location.href = '/';
            }
        }
    }

    // ============================================================
    // POLLING PRINCIPAL
    // ============================================================
    function pollRole() {
        fetch('/check_role', { credentials: 'same-origin' })
            .then(function (res) {

                // Ban levantado → redirigir a login automáticamente
                if (res.status === 205) {
                    showUnbannedOverlay();
                    return null;
                }

                // Usuario eliminado
                if (res.status === 404) {
                    showDeletedOverlay();
                    return null;
                }

                // Usuario baneado — el polling NO se detiene
                if (res.status === 403) {
                    return res.json().then(function (data) {
                        showBanOverlay(data.banned_until || null);
                    });
                }

                // 401: sesión expirada o contraseña cambiada
                if (res.status === 401) {
                    return res.json().then(function (data) {
                        if (data && data.error === 'password_changed') {
                            showPasswordChangedOverlay();
                        } else {
                            stopPolling();
                            window.location.href = '/login';
                        }
                    });
                }

                return res.json();
            })
            .then(function (data) {
                if (!data) return;
                if (data.role !== undefined) {
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
        var dropdown = document.getElementById('dropdownMenu');
        if (dropdown) {
            dropdown.querySelectorAll('button').forEach(function (btn) {
                var oc = btn.getAttribute('onclick') || '';
                if (oc.indexOf('/admin') !== -1) btn.id = 'sg-admin-btn';
            });
        }

        pollRole();
        _intervalId = setInterval(pollRole, 5000);
    });

})();
