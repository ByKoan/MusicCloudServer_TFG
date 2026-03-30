import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView

app = QApplication(sys.argv)

browser = QWebEngineView()

print("Introduce aqui la URL (ej: http://192.168.1.10:8000):")
URL = input()

if not URL.startswith("http"):
    URL = "http://" + URL

browser.setUrl(QUrl(URL))

browser.resize(1200, 800)
browser.setWindowTitle("MusicCloudServer")
browser.show()

sys.exit(app.exec())