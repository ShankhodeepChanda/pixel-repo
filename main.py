import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adapta")
        self.setGeometry(100, 100, 1200, 800)

        # Web view setup
        self.browser = QWebEngineView()
        local_html = os.path.abspath("frontend/index.html")
        self.browser.load(QUrl.fromLocalFile(local_html))

        self.setCentralWidget(self.browser)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
