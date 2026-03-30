package com.webviewer.app;

import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class MainActivity extends AppCompatActivity {

    private WebView webView;
    private SharedPreferences prefs;
    private static final String PREF_HOST = "host";
    private static final String PREF_PORT = "port";
    private static final String PREF_PROTO = "proto";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        prefs = getSharedPreferences("WebViewerPrefs", MODE_PRIVATE);
        webView = findViewById(R.id.webview);

        // Configurar WebView
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);

        webView.setWebViewClient(new WebViewClient());

        // Si no hay host guardado, pedir configuración
        String host = prefs.getString(PREF_HOST, null);
        if (host == null || host.isEmpty()) {
            showConfigDialog(true);
        } else {
            loadUrl();
        }
    }

    private void loadUrl() {
        String proto = prefs.getString(PREF_PROTO, "http");
        String host  = prefs.getString(PREF_HOST, "192.168.1.1");
        String port  = prefs.getString(PREF_PORT, "");

        String url;
        if (port.isEmpty()) {
            url = proto + "://" + host;
        } else {
            url = proto + "://" + host + ":" + port;
        }

        setTitle("Music Cloud Visualizer");
        webView.loadUrl(url);
    }

    private void showConfigDialog(boolean firstTime) {
        String savedProto = prefs.getString(PREF_PROTO, "http");
        String savedHost  = prefs.getString(PREF_HOST, "");
        String savedPort  = prefs.getString(PREF_PORT, "");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int pad = (int)(16 * getResources().getDisplayMetrics().density);
        layout.setPadding(pad, pad, pad, pad);

        // Protocolo
        TextView lblProto = new TextView(this);
        lblProto.setText("Protocolo:");
        layout.addView(lblProto);
        final EditText etProto = new EditText(this);
        etProto.setText(savedProto);
        etProto.setHint("http  o  https");
        layout.addView(etProto);

        // Host / IP
        TextView lblHost = new TextView(this);
        lblHost.setText("IP / Host:");
        layout.addView(lblHost);
        final EditText etHost = new EditText(this);
        etHost.setText(savedHost);
        etHost.setHint("192.168.1.100  o  miservidor.local");
        layout.addView(etHost);

        // Puerto (opcional)
        TextView lblPort = new TextView(this);
        lblPort.setText("Puerto (opcional):");
        layout.addView(lblPort);
        final EditText etPort = new EditText(this);
        etPort.setText(savedPort);
        etPort.setHint("8080  (dejar vacío si no hace falta)");
        layout.addView(etPort);

        AlertDialog.Builder builder = new AlertDialog.Builder(this)
                .setTitle("Configurar servidor")
                .setView(layout)
                .setPositiveButton("Conectar", (dialog, which) -> {
                    String proto = etProto.getText().toString().trim();
                    String host  = etHost.getText().toString().trim();
                    String port  = etPort.getText().toString().trim();

                    if (proto.isEmpty()) proto = "http";

                    prefs.edit()
                         .putString(PREF_PROTO, proto)
                         .putString(PREF_HOST, host)
                         .putString(PREF_PORT, port)
                         .apply();

                    loadUrl();
                });

        if (!firstTime) {
            builder.setNegativeButton("Cancelar", null);
        }

        builder.setCancelable(!firstTime).show();
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        menu.add(0, 1, 0, "⚙ Configurar servidor");
        menu.add(0, 2, 1, "↻ Recargar");
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == 1) {
            showConfigDialog(false);
            return true;
        } else if (item.getItemId() == 2) {
            webView.reload();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}
