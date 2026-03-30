# WebViewer APK

App Android tipo WebView que permite configurar la IP/host a la que conectarse.

## Funcionalidades
- Primera vez: pide IP/host automáticamente
- Menú superior → "⚙ Configurar servidor" para cambiar IP/host/puerto en cualquier momento
- Menú superior → "↻ Recargar" para refrescar
- Botón atrás navega el historial del WebView
- Soporta HTTP y HTTPS
- Permite `usesCleartextTraffic` (HTTP sin certificado, ideal para red local)

## Cómo compilar con Android Studio

1. Instala [Android Studio](https://developer.android.com/studio)
2. Abre la carpeta `WebViewApp` como proyecto
3. Espera a que sincronice Gradle
4. Build → Generate Signed Bundle/APK → APK
   - O simplemente: Build → Build Bundle(s)/APK(s) → Build APK(s)
5. La APK queda en: `app/build/outputs/apk/debug/app-debug.apk`

## Instalación en el móvil
- Activa "Instalar fuentes desconocidas" en Ajustes → Seguridad
- Copia la APK al móvil y ábrela
- O usa `adb install app-debug.apk` con el móvil conectado por USB

## Uso
1. Al abrir la app la primera vez, aparece un diálogo pidiendo:
   - **Protocolo**: `http` o `https`
   - **IP / Host**: p.ej. `192.168.1.100` o `miservidor.local`
   - **Puerto** (opcional): p.ej. `8080`
2. Pulsa "Conectar" → carga la web
3. Para cambiar: menú (3 puntos) → Configurar servidor
