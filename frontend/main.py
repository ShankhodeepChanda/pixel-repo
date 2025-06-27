import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit, QTabWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Adapta")
        
        # Set window to full screen or maximized
        self.setMinimumSize(800, 600)  # Set minimum size
        self.showMaximized()  # Start maximized to cover full screen
        
        # Alternative: Use this for true fullscreen
        # self.showFullScreen()

        # History management
        self.history = []
        self.current_index = -1

        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        layout.setSpacing(0)  # Remove spacing

        # Create toolbar
        toolbar = QWidget()
        toolbar.setFixedHeight(48)  # Set fixed height for toolbar
        toolbar.setObjectName("toolbar")  # Add object name for styling
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(10)

        # Store reference to toolbar for styling
        self.toolbar = toolbar

        # Navigation buttons
        self.back_button = QPushButton("←")
        self.forward_button = QPushButton("→")
        self.reload_button = QPushButton("⟳")
        self.home_button = QPushButton("🏠")
        self.dark_mode_button = QPushButton("🌙")
        
        for btn in [self.back_button, self.forward_button, self.reload_button, self.home_button, self.dark_mode_button]:
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("""
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
            """)

        # Setup button tooltips
        self.back_button.setToolTip("Back")
        self.forward_button.setToolTip("Forward")
        self.reload_button.setToolTip("Reload")
        self.home_button.setToolTip("Home")
        self.dark_mode_button.setToolTip("Toggle Dark Mode")

        # Dark mode setup
        self.is_dark_mode = False

        # URL input
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Search or enter website name")
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 16px;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 20px;
                background-color: #fdfdfd;
            }
            QLineEdit:focus {
                border-color: #007aff;
                background-color: #fff;
            }
        """)

        # Add widgets to toolbar
        toolbar_layout.addWidget(self.back_button)
        toolbar_layout.addWidget(self.forward_button)
        toolbar_layout.addWidget(self.reload_button)
        toolbar_layout.addWidget(self.home_button)
        toolbar_layout.addWidget(self.url_input)
        # Add plus button after search bar
        self.plus_button = QPushButton("＋")
        self.plus_button.setFixedSize(32, 32)
        self.plus_button.setStyleSheet("""
            QPushButton {
                background: none;
                border: none;
                font-size: 22px;
                color: #555;
                border-radius: 6px;
            }
            QPushButton:hover:enabled {
                background-color: rgba(0, 0, 0, 0.08);
            }
        """)
        self.plus_button.setToolTip("New Tab")
        toolbar_layout.addWidget(self.plus_button)
        toolbar_layout.addWidget(self.dark_mode_button)

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
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.plus_button.clicked.connect(self.add_new_tab)

        self.apply_theme()

    def add_new_tab(self, url=None):
        tab = BrowserTab(is_dark_mode=self.is_dark_mode)
        idx = self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentIndex(idx)
        tab.browser.urlChanged.connect(self.url_changed)
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
                    font-size: 14px;
                    border: 1px solid #555;
                    border-radius: 20px;
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
                    font-size: 14px;
                    border: 1px solid #ccc;
                    border-radius: 20px;
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
        for btn in [self.back_button, self.forward_button, self.reload_button, self.home_button, self.dark_mode_button]:
            btn.setStyleSheet(button_style)
        
        # Apply plus button style
        plus_button_style = button_style.replace("font-size: 18px;", "font-size: 22px;")
        self.plus_button.setStyleSheet(plus_button_style)
        
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
                QTabBar::close-button {
                    image: none;
                    background-color: #666;
                    border-radius: 8px;
                    width: 16px;
                    height: 16px;
                }
                QTabBar::close-button:hover {
                    background-color: #888;
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
                QTabBar::close-button {
                    image: none;
                    background-color: #ccc;
                    border-radius: 8px;
                    width: 16px;
                    height: 16px;
                }
                QTabBar::close-button:hover {
                    background-color: #999;
                }
            """
        
        self.tabs.setStyleSheet(tab_style)

    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        self.is_dark_mode = not self.is_dark_mode
        
        # Update button icon
        if self.is_dark_mode:
            self.dark_mode_button.setText("☀️")  # Sun icon for light mode
            self.dark_mode_button.setToolTip("Switch to Light Mode")
        else:
            self.dark_mode_button.setText("🌙")  # Moon icon for dark mode
            self.dark_mode_button.setToolTip("Switch to Dark Mode")
        
        self.apply_theme()
        
        # Refresh home page for all tabs that are currently showing home page
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if tab and tab.browser:
                current_url = tab.browser.url().toString()
                if "adapta_home.html" in current_url or "adapta://home" in current_url:
                    self.go_home(tab=tab)

    def create_home_page_html(self):
        """Create Safari-style home page HTML using external files"""
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
        
        # Generate bookmarks HTML
        popular_sites = [
            {"name": "Google", "url": "https://www.google.com", "icon": "🔍"},
            {"name": "YouTube", "url": "https://www.youtube.com", "icon": "📺"},
            {"name": "GitHub", "url": "https://www.github.com", "icon": "🐙"},
            {"name": "Stack Overflow", "url": "https://stackoverflow.com", "icon": "📚"},
            {"name": "Reddit", "url": "https://www.reddit.com", "icon": "🤖"},
            {"name": "Twitter", "url": "https://www.twitter.com", "icon": "🐦"},
            {"name": "Facebook", "url": "https://www.facebook.com", "icon": "📘"},
            {"name": "Instagram", "url": "https://www.instagram.com", "icon": "📷"},
            {"name": "LinkedIn", "url": "https://www.linkedin.com", "icon": "💼"},
            {"name": "Amazon", "url": "https://www.amazon.com", "icon": "🛒"},
            {"name": "Netflix", "url": "https://www.netflix.com", "icon": "🎬"},
            {"name": "Spotify", "url": "https://www.spotify.com", "icon": "🎵"}
        ]
        
        bookmarks_html = ""
        for site in popular_sites:
            bookmarks_html += f"""
                <div class="bookmark-item" onclick="window.location.href='{site['url']}'">
                    <div class="bookmark-icon">{site['icon']}</div>
                    <div class="bookmark-name">{site['name']}</div>
                </div>
            """
        
        # Set theme class
        theme_class = "dark" if self.is_dark_mode else ""
        
        # Replace placeholders in template
        html_content = html_template.replace("{{current_time}}", current_time)
        html_content = html_content.replace("{{current_date}}", current_date)
        html_content = html_content.replace("{{bookmarks_html}}", bookmarks_html)
        html_content = html_content.replace("{{theme_class}}", theme_class)
        
        return html_content

    def create_fallback_html(self):
        """Fallback HTML if external files are not found"""
        current_time = __import__('datetime').datetime.now().strftime("%H:%M")
        current_date = __import__('datetime').datetime.now().strftime("%A, %B %d")
        
        theme_class = "dark" if self.is_dark_mode else ""
        bg_color = "#1e1e1e" if self.is_dark_mode else "#f5f5f7"
        text_color = "#e0e0e0" if self.is_dark_mode else "#1d1d1f"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Adapta - Home</title>
            <style>
                body {{ background: {bg_color}; color: {text_color}; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; text-align: center; padding: 60px 20px; }}
                .time {{ font-size: 4rem; font-weight: 300; margin-bottom: 10px; }}
                .search-box {{ width: 100%; max-width: 600px; padding: 16px 24px; font-size: 18px; border: 1px solid #ccc; border-radius: 50px; }}
            </style>
        </head>
        <body class="{theme_class}">
            <div class="time">{current_time}</div>
            <div class="date">{current_date}</div>
            <br><br>
            <input type="text" class="search-box" placeholder="Search or enter website URL" onkeypress="if(event.key==='Enter') window.location.href=this.value">
            <p>Welcome to Adapta Browser</p>
        </body>
        </html>
        """

    def go_home(self, tab=None):
        """Navigate to home page"""
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
        """Update URL input when page changes"""
        # Find which tab triggered this signal
        sender_browser = self.sender()
        current_tab = self.current_tab()
        
        # Only update if this is the current tab
        if current_tab and sender_browser == current_tab.browser:
            url = qurl.toString()
            self.url_input.setText(url)
            
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
