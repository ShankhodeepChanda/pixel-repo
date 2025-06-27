.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Search or enter website name")
        self.url_input.setFixedWidth(600)  # Fixed width for centering
        self.url_input.setFixedHeight(36)  # Fixed height
        self.url_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 16px;
                font-size: 16px;
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