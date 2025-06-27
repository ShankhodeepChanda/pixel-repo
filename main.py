import sys
import os
import re
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLineEdit
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont

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
        toolbar_layout.addWidget(self.dark_mode_button)

        # Web view setup
        self.browser = QWebEngineView()
        self.browser.setMinimumSize(400, 300)  # Set minimum size for web view

        # Add to main layout - ensure browser takes full remaining space
        layout.addWidget(toolbar, 0)  # Don't stretch toolbar
        layout.addWidget(self.browser, 1)  # Stretch browser to fill remaining space

        # Connect signals
        self.url_input.returnPressed.connect(self.navigate_to_url)
        self.back_button.clicked.connect(self.go_back)
        self.forward_button.clicked.connect(self.go_forward)
        self.reload_button.clicked.connect(self.reload_page)
        self.home_button.clicked.connect(self.go_home)
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.browser.urlChanged.connect(self.url_changed)

        # Load initial page (home page)
        self.go_home()
        self.update_navigation_buttons()
        self.apply_theme()  # Apply initial theme

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
        self.url_input.setStyleSheet(url_input_style)

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
        
        # Refresh home page if currently on home page
        current_url = self.browser.url().toString()
        if "adapta_home.html" in current_url or self.url_input.text() == "adapta://home":
            self.go_home()

    def create_home_page_html(self):
        """Create Safari-style home page HTML"""
        current_time = __import__('datetime').datetime.now().strftime("%H:%M")
        current_date = __import__('datetime').datetime.now().strftime("%A, %B %d")
        
        # Define popular sites
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
        
        # Create bookmarks grid
        bookmarks_html = ""
        for site in popular_sites:
            bookmarks_html += f"""
                <div class="bookmark-item" onclick="window.location.href='{site['url']}'">
                    <div class="bookmark-icon">{site['icon']}</div>
                    <div class="bookmark-name">{site['name']}</div>
                </div>
            """
        
        # Choose theme colors
        if self.is_dark_mode:
            bg_color = "#1e1e1e"
            text_color = "#e0e0e0"
            secondary_text = "#a0a0a0"
            card_bg = "#2d2d2d"
            card_border = "#404040"
            search_bg = "#404040"
            search_border = "#555"
            bookmark_hover = "#404040"
        else:
            bg_color = "#f5f5f7"
            text_color = "#1d1d1f"
            secondary_text = "#6e6e73"
            card_bg = "#ffffff"
            card_border = "#e5e5e7"
            search_bg = "#ffffff"
            search_border = "#d1d1d6"
            bookmark_hover = "#f0f0f0"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Adapta - Home</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                    background: {bg_color};
                    color: {text_color};
                    line-height: 1.6;
                    min-height: 100vh;
                    padding: 0 20px;
                }}
                
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 60px 0;
                }}
                
                .header {{
                    text-align: center;
                    margin-bottom: 60px;
                }}
                
                .time {{
                    font-size: 4rem;
                    font-weight: 300;
                    margin-bottom: 10px;
                    color: {text_color};
                }}
                
                .date {{
                    font-size: 1.2rem;
                    color: {secondary_text};
                    margin-bottom: 40px;
                }}
                
                .search-container {{
                    display: flex;
                    justify-content: center;
                    margin-bottom: 60px;
                }}
                
                .search-box {{
                    width: 100%;
                    max-width: 600px;
                    padding: 16px 24px;
                    font-size: 18px;
                    border: 1px solid {search_border};
                    border-radius: 50px;
                    background: {search_bg};
                    color: {text_color};
                    outline: none;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                
                .search-box:focus {{
                    border-color: #007aff;
                    box-shadow: 0 0 0 4px rgba(0, 122, 255, 0.1);
                }}
                
                .search-box::placeholder {{
                    color: {secondary_text};
                }}
                
                .bookmarks-section {{
                    margin-bottom: 40px;
                }}
                
                .section-title {{
                    font-size: 1.5rem;
                    font-weight: 600;
                    margin-bottom: 30px;
                    color: {text_color};
                }}
                
                .bookmarks-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                    gap: 20px;
                    max-width: 960px;
                    margin: 0 auto;
                }}
                
                .bookmark-item {{
                    background: {card_bg};
                    border: 1px solid {card_border};
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }}
                
                .bookmark-item:hover {{
                    background: {bookmark_hover};
                    transform: translateY(-2px);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                }}
                
                .bookmark-icon {{
                    font-size: 2.5rem;
                    margin-bottom: 8px;
                }}
                
                .bookmark-name {{
                    font-size: 0.9rem;
                    font-weight: 500;
                    color: {text_color};
                }}
                
                .footer {{
                    text-align: center;
                    margin-top: 60px;
                    color: {secondary_text};
                    font-size: 0.9rem;
                }}
                
                @media (max-width: 768px) {{
                    .time {{
                        font-size: 3rem;
                    }}
                    
                    .search-box {{
                        font-size: 16px;
                        padding: 14px 20px;
                    }}
                    
                    .bookmarks-grid {{
                        grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                        gap: 15px;
                    }}
                    
                    .bookmark-item {{
                        padding: 15px;
                    }}
                    
                    .bookmark-icon {{
                        font-size: 2rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="time">{current_time}</div>
                    <div class="date">{current_date}</div>
                    
                    <div class="search-container">
                        <input type="text" class="search-box" placeholder="Search or enter website URL" 
                               onkeypress="if(event.key==='Enter') handleSearch(this.value)">
                    </div>
                </div>
                
                <div class="bookmarks-section">
                    <h2 class="section-title">Frequently Visited</h2>
                    <div class="bookmarks-grid">
                        {bookmarks_html}
                    </div>
                </div>
                
                <div class="footer">
                    <p>Welcome to Adapta Browser - Your gateway to the web</p>
                </div>
            </div>
            
            <script>
                function handleSearch(query) {{
                    if (query.trim()) {{
                        window.location.href = query;
                    }}
                }}
                
                // Update time every second
                function updateTime() {{
                    const now = new Date();
                    const timeString = now.toLocaleTimeString('en-US', {{
                        hour12: false,
                        hour: '2-digit',
                        minute: '2-digit'
                    }});
                    const timeElement = document.querySelector('.time');
                    if (timeElement) {{
                        timeElement.textContent = timeString;
                    }}
                }}
                
                setInterval(updateTime, 1000);
                
                // Focus search box on load
                window.addEventListener('load', function() {{
                    const searchBox = document.querySelector('.search-box');
                    if (searchBox) {{
                        searchBox.focus();
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        return html_content

    def go_home(self):
        """Navigate to home page"""
        home_html = self.create_home_page_html()
        
        # Create temporary HTML file
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        home_file = os.path.join(temp_dir, "adapta_home.html")
        
        with open(home_file, 'w', encoding='utf-8') as f:
            f.write(home_html)
        
        # Load the home page
        home_url = QUrl.fromLocalFile(home_file)
        self.browser.load(home_url)
        self.url_input.setText("adapta://home")

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
        if url is None:
            url = self.url_input.text()
        
        if isinstance(url, bool):  # Handle signal emission
            url = self.url_input.text()
        
        formatted_url = self.format_url(url)
        if formatted_url:
            qurl = QUrl(formatted_url)
            self.browser.load(qurl)

    def url_changed(self, qurl):
        """Update URL input when page changes"""
        url = qurl.toString()
        self.url_input.setText(url)
        
        # Update history
        if not self.history or self.history[self.current_index] != url:
            # Remove forward history if we're not at the end
            if self.current_index < len(self.history) - 1:
                self.history = self.history[:self.current_index + 1]
            
            self.history.append(url)
            self.current_index = len(self.history) - 1
        
        self.update_navigation_buttons()

    def go_back(self):
        """Go back in history"""
        if self.current_index > 0:
            self.current_index -= 1
            url = self.history[self.current_index]
            self.browser.load(QUrl(url))

    def go_forward(self):
        """Go forward in history"""
        if self.current_index < len(self.history) - 1:
            self.current_index += 1
            url = self.history[self.current_index]
            self.browser.load(QUrl(url))

    def reload_page(self):
        """Reload current page"""
        self.browser.reload()

    def update_navigation_buttons(self):
        """Update navigation button states"""
        self.back_button.setEnabled(self.current_index > 0)
        self.forward_button.setEnabled(self.current_index < len(self.history) - 1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
