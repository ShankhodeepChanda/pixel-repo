import sys
import os
import re
import json
import gc
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QTabWidget, QLabel, QDialog, QListWidget, QProgressBar, QListWidgetItem, QFrame
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QFont
from functools import partial
import speech_recognition as sr
from PyQt5.QtWidgets import QMessageBox

class BrowserTab(QWidget):
    def __init__(self, parent=None, is_dark_mode=False):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.browser = QWebEngineView()
        self.browser.setMinimumSize(400, 300)
        self.layout.addWidget(self.browser)
        self.history = []
        self.current_index = -1
        self.is_dark_mode = is_dark_mode

class DownloadManagerDialog(QDialog):
    def __init__(self, downloads, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Downloads")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        self.downloads = downloads
        self.refresh()

    def refresh(self):
        self.list_widget.clear()
        for d in self.downloads:
            status = d.get('status', 'In Progress')
            progress = d.get('progress', 0)
            item_text = f"{d['filename']} - {status} ({progress}%)"
            item = QListWidgetItem(item_text)
            self.list_widget.addItem(item)

class DownloadDropdown(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() | Qt.Popup)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #fff;
                border: 1px solid #ccc;
                border-radius: 8px;
            }
        """)
        self.setMinimumWidth(340)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(8)
        self.download_widgets = []

    def update_downloads(self, downloads):
        # Remove old widgets
        for w in self.download_widgets:
            self.layout.removeWidget(w)
            w.deleteLater()
        self.download_widgets = []
        if not downloads:
            label = QLabel("No downloads yet.")
            self.layout.addWidget(label)
            self.download_widgets.append(label)
            return
        for d in downloads:
            w = QWidget()
            h = QHBoxLayout(w)
            h.setContentsMargins(0, 0, 0, 0)
            h.setSpacing(6)
            v = QVBoxLayout()
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(2)
            name = QLabel(d['filename'])
            name.setMinimumWidth(120)
            v.addWidget(name)
            progress = QProgressBar()
            progress.setValue(d.get('progress', 0))
            progress.setMaximum(100)
            progress.setTextVisible(True)
            progress.setFormat(f"{d.get('status', 'In Progress')} (%p%)")
            progress.setFixedHeight(14)  # Lower the height for a sleeker look
            if d.get('status') == 'Completed':
                progress.setStyleSheet("QProgressBar::chunk { background: #4caf50; }")
            elif d.get('status') == 'Failed':
                progress.setStyleSheet("QProgressBar::chunk { background: #e53935; }")
            elif d.get('status') == 'Cancelled':
                progress.setStyleSheet("QProgressBar::chunk { background: #bdbdbd; }")
            v.addWidget(progress)
            h.addLayout(v, 1)
            # Cancel button
            cancel_btn = QPushButton("✖")
            cancel_btn.setFixedSize(24, 24)
            cancel_btn.setToolTip("Cancel download")
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background: none;
                    border: none;
                    font-size: 14px;
                    color: #e53935;
                    border-radius: 12px;
                }
                QPushButton:hover:enabled {
                    background-color: #ffeaea;
                }
            """)
            # Only show cancel if in progress
            if d.get('status') == 'In Progress':
                cancel_btn.setEnabled(True)
                cancel_btn.clicked.connect(d['cancel_callback'])
            else:
                cancel_btn.setEnabled(False)
            h.addWidget(cancel_btn)
            self.layout.addWidget(w)
            self.download_widgets.append(w)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.downloads = []  # Track download info for the download manager
        # Enable hardware acceleration and smooth scrolling for all QWebEngineViews
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-gpu-rasterization --enable-zero-copy --enable-features=SmoothScrolling,TouchpadAndWheelScrollLatching,CompositorThreadedScroll"
        
        self.setWindowTitle("Adapta")
        
        # Set window to full screen or maximized
        self.setMinimumSize(800, 600)  # Set minimum size
        self.showMaximized()  # Start maximized to cover full screen
        
      
        # History management
        self.history = []
        self.current_index = -1

        # Bookmarks initialization
        self.bookmarks = []  # List of dicts: {"url": ..., "title": ...}
        self.load_bookmarks()

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing

        # Create toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(60)  # Increased height for larger elements
        toolbar.setObjectName("toolbar")  # Add object name for styling
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 10, 16, 10)  # Increased margins
        toolbar_layout.setSpacing(15)  # Increased spacing between elements

        # Store reference to toolbar for styling
        self.toolbar = toolbar

        # Download button (define before adding to toolbar)
        self.download_button = QPushButton("⬇️")
        self.download_button.setFixedSize(32, 32)
        self.download_button.setToolTip("Show Downloads")
        self.download_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 20px;
                color: #0078d4;
                border-radius: 6px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(0, 120, 212, 0.08);
            }
        """)
        self.download_button.clicked.connect(self.toggle_download_dropdown)

        # Navigation buttons
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.reload_button = QPushButton("⟳")
        self.home_button = QPushButton("🏠")
        
        for btn in [self.back_button, self.forward_button, self.reload_button, self.home_button]:
            btn.setFixedSize(40, 40)  # Increased size
            btn.setStyleSheet("""
                QPushButton {
                    background: none;
                    border: none;
                    font-size: 20px;
                    color: #555;
                    border-radius: 8px;
                }
                QPushButton:hover:enabled {
                    background-color: rgba(0, 0, 0, 0.08);
                }
                QPushButton:disabled {
                    opacity: 0.5;
                }
            """)

        # Setup button tooltips
        self.back_button.setToolTip("Back")
        self.forward_button.setToolTip("Forward")
        self.reload_button.setToolTip("Reload")
        self.home_button.setToolTip("Home")

        # Dark mode setup
        self.is_dark_mode = False

        # URL input - centered with limited width
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Search or enter website name")
        self.url_input.setFixedWidth(600)  # Fixed width for centering
        self.url_input.setFixedHeight(36)  # Fixed height
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 30px;
                font-size: 28px;
                border: 1px solid #ccc;
                border-radius: 18px;
                background-color: #fdfdfd;
            }
            QLineEdit:focus {
                border-color: #007aff;
                background-color: #fff;
            }
        """)

        # Add widgets to toolbar with improved layout
        # Left side - navigation buttons with increased spacing
        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addSpacing(8)  # Extra space after back button
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addSpacing(20)  # Larger space before reload
        toolbar_layout.addWidget(self.reload_button)
        toolbar_layout.addSpacing(8)  # Space after reload
        toolbar_layout.addWidget(self.home_button)
        # Download button should be left of the search bar
        toolbar_layout.addWidget(self.download_button)
        
        # Center the search bar
        toolbar_layout.addStretch()  # Push search bar to center
        toolbar_layout.addWidget(self.url_input)
        toolbar_layout.addStretch()  # Push remaining elements to the right
        
        # Right side buttons
        # Add bookmark (star) button
        self.bookmark_button = QPushButton()
        self.bookmark_button.setFixedSize(40, 40)  # Increased size
        self.bookmark_button.setToolTip("Bookmark this page")
        self.bookmark_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 18px;
                color: #e0c200;
                border-radius: 8px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(255, 215, 0, 0.08);
            }
        """)
        self.bookmark_button.setText("☆")  # Outline star
        
        # Add plus button after search bar
        self.plus_button = QPushButton("＋")
        self.plus_button.setFixedSize(40, 40)  # Increased size
        self.plus_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 20px;
                color: #555;
                border-radius: 8px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(0, 0, 0, 0.08);
            }
        """)
        self.plus_button.setToolTip("New Tab")
        
        # Add kebab menu button
        self.menu_button = QPushButton("⋮")
        self.menu_button.setFixedSize(40, 40)
        self.menu_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 20px;
                color: #555;
                border-radius: 8px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(0, 0, 0, 0.08);
            }
        """)
        self.menu_button.setToolTip("Menu")
        
        toolbar_layout.addWidget(self.bookmark_button)
        toolbar_layout.addWidget(self.plus_button)
        toolbar_layout.addWidget(self.menu_button)

        # Add microphone button for voice commands
        self.mic_button = QPushButton("🎤")
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setToolTip("Voice Command - Click to speak")
        self.mic_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 20px;
                color: #0078d4;
                border-radius: 8px;
                transition: all 0.2s ease;
            }
            QPushButton:hover:enabled {
                background-color: rgba(0, 120, 212, 0.08);
                transform: scale(1.1);
            }
            QPushButton:pressed {
                background-color: rgba(0, 120, 212, 0.2);
            }
        """)
        self.mic_button.clicked.connect(self.handle_voice_command)
        # Add mic button to toolbar (right before menu)
        toolbar_layout = self.toolbar.layout()
        toolbar_layout.insertWidget(toolbar_layout.count() - 1, self.mic_button)

        # Tab widget for multiple tabs (under toolbar)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_tab_changed)
        layout.addWidget(toolbar, 0)
        layout.addWidget(self.tabs, 0)

        # Add first tab
        self.add_new_tab()

        # Connect signals
        self.url_input.returnPressed.connect(self.navigate_to_url)
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.reload_button.clicked.connect(self.reload_page)
        self.home_button.clicked.connect(self.go_home)
        self.plus_button.clicked.connect(self.add_new_tab)
        self.bookmark_button.clicked.connect(self.toggle_bookmark)
        self.menu_button.clicked.connect(self.show_menu)

        self.apply_theme()

        # Download dropdown initialization
        self.download_dropdown = DownloadDropdown(self)
        self.download_dropdown.hide()

    def add_new_tab(self, url=None):
        tab = BrowserTab(is_dark_mode=self.is_dark_mode)
        # Restore default QWebEngineView settings (no forced disabling of features)
        tab.browser.settings().setAttribute(tab.browser.settings().Accelerated2dCanvasEnabled, True)
        tab.browser.settings().setAttribute(tab.browser.settings().WebGLEnabled, True)
        tab.browser.settings().setAttribute(tab.browser.settings().JavascriptEnabled, True)
        tab.browser.settings().setAttribute(tab.browser.settings().LocalStorageEnabled, True)
        tab.browser.setAttribute(Qt.WA_OpaquePaintEvent, True)
        tab.browser.setAttribute(Qt.WA_NoSystemBackground, True)
        tab.browser.setFocusPolicy(True)
        idx = self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentIndex(idx)
        tab.browser.urlChanged.connect(self.url_changed)
        tab.browser.page().profile().downloadRequested.connect(self.handle_download_requested)
        if url:
            tab.browser.load(QUrl(url))
        else:
            self.go_home(tab=tab)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)

    def on_tab_changed(self, index):
        """Handle tab change"""
        tab = self.current_tab()
        if tab and tab.browser:
            current_url = tab.browser.url().toString()
            # Handle special home page URL
            if "adapta_home.html" in current_url:
                self.url_input.setText("adapta://home")
            else:
                self.url_input.setText(current_url)
            self.update_navigation_buttons()
        self.update_bookmark_icon()

    def current_tab(self):
        return self.tabs.currentWidget()

    def apply_theme(self):
        """Apply light or dark theme"""
        if self.is_dark_mode:
            # Dark theme
            toolbar_style = """
                QWidget {
                    background-color: #2d2d2d;
                    border-bottom: 1px solid #404040;
                }
            """
            
            button_style = """
                QPushButton {
                    background: none;
                    border: none;
                    font-size: 18px;
                    color: #e0e0e0;
                    border-radius: 6px;
                }
                QPushButton:hover:enabled {
                    background-color: rgba(255, 255, 255, 0.1);
                }
                QPushButton:disabled {
                    opacity: 0.5;
                    color: #808080;
                }
            """
            
            url_input_style = """
                QLineEdit {
                    padding: 8px 16px;
                    font-size: 16px;
                    border: 1px solid #555;
                    border-radius: 18px;
                    background-color: #404040;
                    color: #e0e0e0;
                }
                QLineEdit:focus {
                    border-color: #0078d4;
                    background-color: #505050;
                }
            """
            
            # Update main window background
            self.setStyleSheet("QMainWindow { background-color: #1e1e1e; }")
            
        else:
            # Light theme
            toolbar_style = """
                QWidget {
                    background-color: #f9f9f9;
                    border-bottom: 1px solid #ddd;
                }
            """
            
            button_style = """
                QPushButton {
                    background: none;
                    border: none;
                    font-size: 18px;
                    color: #555;
                    border-radius: 6px;
                }
                QPushButton:hover:enabled {
                    background-color: rgba(0, 0, 0, 0.08);
                }
                QPushButton:disabled {
                    opacity: 0.5;
                }
            """
            
            url_input_style = """
                QLineEdit {
                    padding: 8px 16px;
                    font-size: 16px;
                    border: 1px solid #ccc;
                    border-radius: 18px;
                    background-color: #fdfdfd;
                    color: #333;
                }
                QLineEdit:focus {
                    border-color: #007aff;
                    background-color: #fff;
                }
            """
            
            # Reset main window background
            self.setStyleSheet("")
        
        # Apply styles to widgets
        self.toolbar.setStyleSheet(toolbar_style)  # Apply to toolbar
        for btn in [self.back_button, self.forward_button, self.reload_button, self.home_button]:
            btn.setStyleSheet(button_style)
        
        # Apply button styles with appropriate sizes
        plus_button_style = button_style.replace("font-size: 18px;", "font-size: 20px;")
        self.plus_button.setStyleSheet(plus_button_style)
        
        menu_button_style = button_style.replace("font-size: 18px;", "font-size: 20px;")
        self.menu_button.setStyleSheet(menu_button_style)
        
        self.url_input.setStyleSheet(url_input_style)
        
        # Style the tab widget
        if self.is_dark_mode:
            tab_style = """
                QTabWidget::pane {
                    border: none;
                    background-color: #1e1e1e;
                }
                QTabBar::tab {
                    background-color: #2d2d2d;
                    color: #e0e0e0;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                QTabBar::tab:selected {
                    background-color: #404040;
                    color: #ffffff;
                }
                QTabBar::tab:hover {
                    background-color: #353535;
                }
            """
        else:
            tab_style = """
                QTabWidget::pane {
                    border: none;
                    background-color: #ffffff;
                }
                QTabBar::tab {
                    background-color: #f0f0f0;
                    color: #333;
                    padding: 8px 16px;
                    margin-right: 2px;
                    border-top-left-radius: 8px;
                    border-top-right-radius: 8px;
                }
                QTabBar::tab:selected {
                    background-color: #ffffff;
                    color: #000;
                }
                QTabBar::tab:hover {
                    background-color: #e8e8e8;
                }
            """
        
        self.tabs.setStyleSheet(tab_style)

    def create_home_page_html(self):
        """Create Safari-style home page HTML using external files and bookmarks"""
        import datetime
        import os
        current_time = datetime.datetime.now().strftime("%H:%M")
        current_date = datetime.datetime.now().strftime("%A, %B %d")
        # Read the HTML template
        template_path = os.path.join(os.path.dirname(__file__), "home.html")
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
        except FileNotFoundError:
            # Fallback to inline HTML if file not found
            return self.create_fallback_html()
        # Set theme class
        theme_class = "dark" if self.is_dark_mode else ""
        # Bookmarks HTML
        bookmarks_html = ""
        if self.bookmarks:
            bookmarks_html += '<div class="bookmarks-grid">'
            for bm in self.bookmarks:
                bookmarks_html += f'''
                <div class="bookmark-item" onclick="window.location.href='{bm["url"]}'">
                    <div class="bookmark-name">{bm["title"][:20] + ("..." if len(bm["title"]) > 20 else "")}</div>
                </div>'''
            bookmarks_html += '</div>'
        # Replace placeholders
        html_content = html_template.replace("{{current_time}}", current_time)
        html_content = html_content.replace("{{current_date}}", current_date)
        html_content = html_content.replace("{{theme_class}}", theme_class)
        html_content = html_content.replace("{{bookmarks_html}}", bookmarks_html)
        return html_content

    def create_fallback_html(self):
        """Fallback HTML if external files are not found, with bookmarks"""
        current_time = __import__('datetime').datetime.now().strftime("%H:%M")
        current_date = __import__('datetime').datetime.now().strftime("%A, %B %d")
        theme_class = "dark" if self.is_dark_mode else ""
        bg_color = "#1e1e1e" if self.is_dark_mode else "#f5f5f7"
        text_color = "#e0e0e0" if self.is_dark_mode else "#1d1d1f"
        bookmarks_html = ""
        if self.bookmarks:
            bookmarks_html += '<div class="bookmarks-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 20px; max-width: 960px; margin: 0 auto; margin-top: 32px;">'
            for bm in self.bookmarks:
                bookmarks_html += f'''
                <div style="aspect-ratio: 1; border: 1px solid rgba(255,255,255,0.2); border-radius: 20px; padding: 20px; text-align: center; cursor: pointer; background: rgba(45,45,45,0.7); backdrop-filter: blur(10px); display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.3s ease; box-shadow: 0 4px 20px rgba(0,0,0,0.1);" onclick="window.location.href='{bm["url"]}'">
                    <div style="font-size: 0.9rem; font-weight: 500; color: inherit;">{bm["title"][:20] + ("..." if len(bm["title"]) > 20 else "")}</div>
                </div>'''
            bookmarks_html += '</div>'
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Adapta - Home</title>
            <style>
                body {{ background: {bg_color}; color: {text_color}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; text-align: center; padding: 60px 20px; }}
                .time {{ font-size: 4rem; font-weight: 300; margin-bottom: 10px; }}
            </style>
        </head>
        <body class=\"{theme_class}\">
            <div class=\"time\">{current_time}</div>
            <div class=\"date\">{current_date}</div>
            <p>Welcome to Adapta Browser</p>
            {bookmarks_html}
        </body>
        </html>
        """

    def go_home(self, tab=None):
        """Navigate to home page"""
        # Handle signal emission (clicked may pass a boolean)
        if isinstance(tab, bool):
            tab = None
        if tab is None:
            tab = self.current_tab()
        if not tab:
            return
            
        home_html = self.create_home_page_html()
        import tempfile
        import os
        import shutil
        
        temp_dir = tempfile.gettempdir()
        home_file = os.path.join(temp_dir, "adapta_home.html")
        
        try:
            # Write the HTML file
            with open(home_file, 'w', encoding='utf-8') as f:
                f.write(home_html)
            
            # Copy CSS and JS files to temp directory if they exist
            script_dir = os.path.dirname(__file__)
            css_source = os.path.join(script_dir, "home.css")
            js_source = os.path.join(script_dir, "home.js")
            
            css_dest = os.path.join(temp_dir, "home.css")
            js_dest = os.path.join(temp_dir, "home.js")
            
            if os.path.exists(css_source):
                shutil.copy2(css_source, css_dest)
            
            if os.path.exists(js_source):
                shutil.copy2(js_source, js_dest)
            
            home_url = QUrl.fromLocalFile(home_file)
            tab.browser.load(home_url)
            
            # Only update URL input if this is the current tab
            if tab == self.current_tab():
                self.url_input.setText("adapta://home")
                
        except Exception as e:
            print(f"Error creating home page: {e}")
            # Load fallback HTML directly
            fallback_html = self.create_fallback_html()
            with open(home_file, 'w', encoding='utf-8') as f:
                f.write(fallback_html)
            home_url = QUrl.fromLocalFile(home_file)
            tab.browser.load(home_url)

    def is_valid_url(self, string):
        """Check if string is a valid URL"""
        try:
            result = QUrl(string)
            return result.isValid() and result.scheme() in ['http', 'https']
        except:
            return False

    def format_url(self, input_text):
        """Format input as URL or search query"""
        input_text = input_text.strip()
        
        if not input_text:
            return ""
        
        # If it's already a valid URL, return as is
        if input_text.startswith(('http://', 'https://')):
            return input_text
        
        # Check if it looks like a domain
        domain_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}$'
        if re.match(domain_pattern, input_text) or 'localhost' in input_text or '.' in input_text:
            return f"https://{input_text}"
        
        # Otherwise, treat as search query
        return f"https://www.google.com/search?q={input_text.replace(' ', '+')}"

    def navigate_to_url(self, url=None):
        """Navigate to URL or search query"""
        tab = self.current_tab()
        if not tab:
            return
            
        if url is None:
            url = self.url_input.text()
        
        if isinstance(url, bool):  # Handle signal emission
            url = self.url_input.text()
        
        formatted_url = self.format_url(url)
        if formatted_url:
            qurl = QUrl(formatted_url)
            tab.browser.load(qurl)

    def url_changed(self, qurl):
        """Update URL input when page changes and update favicon"""
        # Find which tab triggered this signal
        sender_browser = self.sender()
        current_tab = self.current_tab()
        # Only update if this is the current tab
        if current_tab and sender_browser == current_tab.browser:
            url = qurl.toString()
            # Only update if URL actually changed
            if self.url_input.text() != url:
                self.url_input.setText(url)
            # Update favicon in tab only
            def set_favicon():
                icon = current_tab.browser.icon()
                tab_index = self.tabs.indexOf(current_tab)
                if tab_index >= 0:
                    self.tabs.setTabIcon(tab_index, icon)
            current_tab.browser.iconChanged.connect(lambda _: set_favicon())
            set_favicon()
            
            # Update history per tab
            if not current_tab.history or current_tab.current_index < 0 or current_tab.history[current_tab.current_index] != url:
                if current_tab.current_index < len(current_tab.history) - 1:
                    current_tab.history = current_tab.history[:current_tab.current_index + 1]
                current_tab.history.append(url)
                current_tab.current_index = len(current_tab.history) - 1
            
            self.update_navigation_buttons()
            # Update tab title
            tab_index = self.tabs.indexOf(current_tab)
            if tab_index >= 0:
                self.tabs.setTabText(tab_index, self.page_title(current_tab))
            self.update_bookmark_icon()

    def page_title(self, tab):
        title = tab.browser.title() or "New Tab"
        return title[:20] + ("..." if len(title) > 20 else "")

    def go_back(self):
        """Go back in history"""
        tab = self.current_tab()
        if tab and tab.current_index > 0:
            tab.current_index -= 1
            url = tab.history[tab.current_index]
            tab.browser.load(QUrl(url))

    def go_forward(self):
        """Go forward in history"""
        tab = self.current_tab()
        if tab and tab.current_index < len(tab.history) - 1:
            tab.current_index += 1
            url = tab.history[tab.current_index]
            tab.browser.load(QUrl(url))

    def reload_page(self):
        """Reload current page"""
        tab = self.current_tab()
        if tab:
            tab.browser.reload()

    def update_navigation_buttons(self):
        """Update navigation button states"""
        tab = self.current_tab()
        if tab:
            self.back_button.setEnabled(tab.current_index > 0)
            self.forward_button.setEnabled(tab.current_index < len(tab.history) - 1)
        else:
            self.back_button.setEnabled(False)
            self.forward_button.setEnabled(False)

    def toggle_bookmark(self):
        """Add or remove current page from bookmarks"""
        tab = self.current_tab()
        if not tab:
            return
        url = tab.browser.url().toString()
        title = tab.browser.title() or url
        # Check if already bookmarked
        for bm in self.bookmarks:
            if bm["url"] == url:
                self.bookmarks.remove(bm)
                self.bookmark_button.setText("☆")  # Outline star
                self.bookmark_button.setToolTip("Bookmark this page")
                self.save_bookmarks()
                self.update_home_bookmarks()
                return
        # Add new bookmark
        self.bookmarks.append({"url": url, "title": title})
        self.bookmark_button.setText("★")  # Filled star
        self.bookmark_button.setToolTip("Remove bookmark")
        self.save_bookmarks()
        self.update_home_bookmarks()  # Save changes to bookmarks

    def update_bookmark_icon(self):
        """Update the star icon based on whether current page is bookmarked"""
        tab = self.current_tab()
        if not tab:
            self.bookmark_button.setText("☆")
            self.bookmark_button.setToolTip("Bookmark this page")
            return
        url = tab.browser.url().toString()
        for bm in self.bookmarks:
            if bm["url"] == url:
                self.bookmark_button.setText("★")
                self.bookmark_button.setToolTip("Remove bookmark")
                return
        self.bookmark_button.setText("☆")
        self.bookmark_button.setToolTip("Bookmark this page")

    def update_home_bookmarks(self):
        """Force refresh of home page if visible to update bookmarks grid"""
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab.browser:
                current_url = tab.browser.url().toString()
                if "adapta_home.html" in current_url or "adapta://home" in current_url:
                    self.go_home(tab=tab)

    def load_bookmarks(self):
        """Load bookmarks from a JSON file if it exists, otherwise use defaults"""
        import os
        
        # Default bookmarks if no file exists
        default_bookmarks = [
            {
                "url": "https://www.google.com/",
                "title": "Google"
            }
        ]
        
        try:
            bookmarks_path = os.path.join(os.path.dirname(__file__), "bookmarks.json")
            if os.path.exists(bookmarks_path):
                with open(bookmarks_path, "r", encoding="utf-8") as f:
                    self.bookmarks = json.load(f)
            else:
                # No file exists, use defaults and create the file
                self.bookmarks = default_bookmarks.copy()
                self.save_bookmarks()  # Create the file with defaults
        except Exception as e:
            print(f"Error loading bookmarks: {e}")
            # Fallback to defaults if there's an error
            self.bookmarks = default_bookmarks.copy()

    def save_bookmarks(self):
        """Save bookmarks to a JSON file"""
        import os
        try:
            bookmarks_path = os.path.join(os.path.dirname(__file__), "bookmarks.json")
            with open(bookmarks_path, "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving bookmarks: {e}")

    def handle_download_requested(self, download):
        """Handle file download requests"""
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        suggested_path = download.path()
        # Ask user where to save the file
        save_path, _ = QFileDialog.getSaveFileName(self, "Save File", suggested_path)
        if save_path:
            download.setPath(save_path)
            download.accept()
            download_info = {
                'filename': os.path.basename(save_path),
                'status': 'In Progress',
                'progress': 0
            }
            # Now that download_info exists, add the cancel_callback
            download_info['cancel_callback'] = partial(self.cancel_download, download, download_info)
            self.downloads.append(download_info)
            def on_progress(received, total):
                percent = int(received * 100 / total) if total > 0 else 0
                download_info['progress'] = percent
                self.download_dropdown.update_downloads(self.downloads)
            def on_finished():
                if download.state() == download.DownloadCancelled:
                    download_info['status'] = 'Cancelled'
                elif download.state() == download.DownloadCompleted:
                    download_info['status'] = 'Completed'
                    download_info['progress'] = 100
                else:
                    download_info['status'] = 'Failed'
                self.download_dropdown.update_downloads(self.downloads)
            download.downloadProgress.connect(on_progress)
            download.finished.connect(on_finished)
            QMessageBox.information(self, "Download Started", f"Downloading to: {save_path}")
            self.download_dropdown.update_downloads(self.downloads)
        else:
            download.cancel()
        # Hide dropdown if no downloads
        if not self.downloads:
            self.download_dropdown.hide()

    def cancel_download(self, download, download_info):
        download.cancel()
        download_info['status'] = 'Cancelled'
        self.download_dropdown.update_downloads(self.downloads)

    def toggle_download_dropdown(self):
        if self.download_dropdown.isVisible():
            self.download_dropdown.hide()
        else:
            self.download_dropdown.update_downloads(self.downloads)
            # Position dropdown aligned to the left of the download button
            btn_pos = self.download_button.mapToGlobal(self.download_button.rect().bottomLeft())
            dropdown_width = self.download_dropdown.sizeHint().width()
            btn_width = self.download_button.width()
            # Align left edge of dropdown with left edge of button
            left_aligned_pos = btn_pos
            self.download_dropdown.move(left_aligned_pos)
            self.download_dropdown.show()

    def show_downloads(self):
        dlg = DownloadManagerDialog(self.downloads, self)
        dlg.exec_()

    def show_menu(self):
        """Show the kebab menu with browser options"""
        from PyQt5.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 4px;
                font-size: 14px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:hover {
                background-color: #f0f0f0;
            }
            QMenu::item:selected {
                background-color: #e8e8e8;
            }
        """)
        
        # Add menu actions
        menu.addAction("🌙 Toggle Dark Mode", self.toggle_dark_mode_menu)
        menu.addSeparator()
        menu.addAction("📊 View Page Source", self.view_page_source)
        menu.addAction("🛠️ Inspect Element", self.inspect_element)
        menu.addSeparator()
        menu.addAction("📋 Bookmarks Manager", self.open_bookmarks_manager)
        menu.addAction("⚙️ Settings", self.open_settings)
        menu.addSeparator()
        menu.addAction("❓ About Adapta", self.show_about)
        
        # Show menu at button position
        button_rect = self.menu_button.geometry()
        menu_pos = self.menu_button.mapToGlobal(button_rect.bottomLeft())
        menu.exec_(menu_pos)

    def inspect_element(self):
        """Open the built-in inspector/devtools for the current page (like Inspect Element in browsers)"""
        tab = self.current_tab()
        if tab and tab.browser:
            # Robust DevTools window creation for PyQt5
            if not hasattr(tab, '_devtools_window') or tab._devtools_window is None:
                from PyQt5.QtWebEngineWidgets import QWebEngineView
                devtools = QWebEngineView()
                devtools.setWindowTitle("DevTools")
                devtools.resize(900, 600)
                devtools.show()
                tab._devtools_window = devtools
                tab.browser.page().setDevToolsPage(devtools.page())
            else:
                tab._devtools_window.show()
                tab._devtools_window.raise_()
                tab._devtools_window.activateWindow()
            # Always trigger InspectElement to highlight
            tab.browser.page().triggerAction(tab.browser.page().InspectElement)

    def toggle_dark_mode_menu(self):
        """Toggle dark mode from menu"""
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()
        
        # Refresh home page for all tabs that are currently showing home page
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab.browser:
                current_url = tab.browser.url().toString()
                if "adapta_home.html" in current_url or "adapta://home" in current_url:
                    self.go_home(tab=tab)

    def view_page_source(self):
        """View page source (placeholder)"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Page Source", "Page source viewer coming soon!")

    def open_dev_tools(self):
        """Open developer tools (placeholder)"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Developer Tools", "Developer tools coming soon!")

    def open_bookmarks_manager(self):
        """Open bookmarks manager (placeholder)"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Bookmarks", "Bookmarks manager coming soon!")

    def open_settings(self):
        """Open settings (placeholder)"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "Settings", "Settings panel coming soon!")

    def show_about(self):
        """Show about dialog"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "About Adapta", 
                         "Adapta Browser\n\nA modern, fast browser built with PyQt5\n\nVersion 1.0")

    def handle_voice_command(self):
        """Handle voice commands for browser navigation and control"""
        recognizer = sr.Recognizer()
        
        # Show listening indicator
        self.mic_button.setText("🔴")  # Red dot to indicate listening
        self.mic_button.setToolTip("Listening...")
        
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                # Show listening dialog
                QMessageBox.information(self, "Voice Command", "Listening... Please speak your command.\n\nExample commands:\n• 'Go to YouTube'\n• 'Open new tab'\n• 'Go back'\n• 'Reload page'\n• 'Switch to [tab name]'")
                
                # Listen for audio
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=5)
                
                # Recognize speech
                command = recognizer.recognize_google(audio).lower()
                print(f"Voice command received: {command}")
                
                # Process the command
                self.process_voice_command(command)
                
        except sr.WaitTimeoutError:
            QMessageBox.warning(self, "Voice Command", "No speech detected. Please try again.")
        except sr.UnknownValueError:
            QMessageBox.warning(self, "Voice Command", "Could not understand the command. Please try again.")
        except sr.RequestError as e:
            QMessageBox.warning(self, "Voice Command", f"Speech recognition service error: {e}")
        except Exception as e:
            QMessageBox.warning(self, "Voice Command", f"An error occurred: {e}")
        finally:
            # Reset microphone button
            self.mic_button.setText("🎤")
            self.mic_button.setToolTip("Voice Command")

    def process_voice_command(self, command):
        """Process and execute voice commands"""
        command = command.strip().lower()
        
        # Navigation commands
        if any(phrase in command for phrase in ["go to", "open", "navigate to", "visit"]):
            # Extract the site name/URL
            for phrase in ["go to", "open", "navigate to", "visit"]:
                if phrase in command:
                    site = command.split(phrase, 1)[1].strip()
                    if site:
                        # Handle common site shortcuts
                        shortcuts = {
                            "youtube": "https://www.youtube.com",
                            "google": "https://www.google.com",
                            "facebook": "https://www.facebook.com",
                            "twitter": "https://www.twitter.com",
                            "instagram": "https://www.instagram.com",
                            "reddit": "https://www.reddit.com",
                            "wikipedia": "https://www.wikipedia.org",
                            "github": "https://www.github.com"
                        }
                        
                        url = shortcuts.get(site, site)
                        self.url_input.setText(url)
                        self.navigate_to_url()
                        QMessageBox.information(self, "Voice Command", f"Navigating to: {site}")
                        return
        
        # Tab management commands
        elif "new tab" in command or "open tab" in command:
            self.add_new_tab()
            QMessageBox.information(self, "Voice Command", "New tab opened")
            return
            
        elif "close tab" in command:
            if self.tabs.count() > 1:
                self.close_tab(self.tabs.currentIndex())
                QMessageBox.information(self, "Voice Command", "Tab closed")
            else:
                QMessageBox.information(self, "Voice Command", "Cannot close the last tab")
            return
            
        elif any(phrase in command for phrase in ["switch to", "go to tab"]):
            # Switch to specific tab
            for phrase in ["switch to", "go to tab"]:
                if phrase in command:
                    tab_name = command.split(phrase, 1)[1].strip()
                    found = False
                    for i in range(self.tabs.count()):
                        tab = self.tabs.widget(i)
                        if tab and tab.browser:
                            title = tab.browser.title().lower() if tab.browser.title() else ""
                            url = tab.browser.url().toString().lower()
                            if tab_name in title or tab_name in url:
                                self.tabs.setCurrentIndex(i)
                                QMessageBox.information(self, "Voice Command", f"Switched to: {tab.browser.title()}")
                                found = True
                                break
                    if not found:
                        QMessageBox.information(self, "Voice Command", f"No tab found matching: {tab_name}")
                    return
        
        # Navigation commands
        elif "go back" in command or "back" in command:
            self.go_back()
            QMessageBox.information(self, "Voice Command", "Going back")
            return
            
        elif "go forward" in command or "forward" in command:
            self.go_forward()
            QMessageBox.information(self, "Voice Command", "Going forward")
            return
            
        elif "reload" in command or "refresh" in command:
            self.reload_page()
            QMessageBox.information(self, "Voice Command", "Page reloaded")
            return
            
        elif "home" in command or "go home" in command:
            self.go_home()
            QMessageBox.information(self, "Voice Command", "Going to home page")
            return
        
        # Bookmark commands
        elif "bookmark" in command or "add bookmark" in command:
            self.toggle_bookmark()
            QMessageBox.information(self, "Voice Command", "Bookmark toggled")
            return
            
        # Theme commands
        elif "dark mode" in command or "toggle dark mode" in command:
            self.toggle_dark_mode_menu()
            mode = "dark" if self.is_dark_mode else "light"
            QMessageBox.information(self, "Voice Command", f"Switched to {mode} mode")
            return
        
        # Search commands
        elif "search for" in command:
            search_term = command.split("search for", 1)[1].strip()
            if search_term:
                search_url = f"https://www.google.com/search?q={search_term.replace(' ', '+')}"
                self.url_input.setText(search_url)
                self.navigate_to_url()
                QMessageBox.information(self, "Voice Command", f"Searching for: {search_term}")
                return
        
        # If no command matched
        QMessageBox.information(self, "Voice Command", f"Command not recognized: '{command}'\n\nTry commands like:\n• 'Go to YouTube'\n• 'Open new tab'\n• 'Go back'\n• 'Search for cats'")
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())