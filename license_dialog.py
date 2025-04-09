import os
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QFrame, QGraphicsDropShadowEffect
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from utils import load_svg_logo

class LicenseDialog(QDialog):
    """Dialog for license verification before starting the application."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("License Verification")
        self.setFixedSize(500, 400)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        # Apply gradient background
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f0f2f5,
                    stop: 0.5 #e8eaf6,
                    stop: 1 #f0f2f5
                );
            }
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        
        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(25, 25, 25, 25)
        
        # Create white panel with rounded corners
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            background-color: white;
            border-radius: 15px;
            padding: 20px;
        """)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 30))
        content_frame.setGraphicsEffect(shadow)
        
        # Create layout for content
        content_layout = QVBoxLayout(content_frame)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add logo at the top
        logo_path = os.path.join(os.path.dirname(__file__), 'Logo EVident - Vector.svg')
        if os.path.exists(logo_path):
            logo_pixmap = load_svg_logo(logo_path, width=300)
            logo_label = QLabel()
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("margin-top: 40px; margin-bottom: 40px;")
            content_layout.addWidget(logo_label)
        
        # Add title
        title_label = QLabel("EVident Battery Control Panel")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #1a237e;
            margin-bottom: 15px;
            margin-top: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title_label)
        
        # Add instruction
        instruction_label = QLabel("Please enter your license code to continue:")
        instruction_label.setStyleSheet("""
            font-size: 14px;
            color: #424242;
            margin-bottom: 15px;
            margin-top: 10px;
        """)
        instruction_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(instruction_label)
        
        # Add license code input
        self.license_input = QLineEdit()
        self.license_input.setEchoMode(QLineEdit.Password)
        self.license_input.setAlignment(Qt.AlignCenter)
        self.license_input.setStyleSheet("""
            padding: 12px;
            font-size: 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background-color: white;
            margin-bottom: 10px;
            line-height: 15px;
            padding-top: 30px;
            padding-bottom: 30px;
        """)
        self.license_input.setFixedHeight(45)
        self.license_input.returnPressed.connect(self.verify_license)
        content_layout.addWidget(self.license_input)
        
        # Add status message (initially empty)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #f44336; font-size: 14px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(self.status_label)
        
        # Add verify button
        verify_btn = QPushButton("Verify License")
        verify_btn.setStyleSheet("""
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #2962ff,
                stop: 1 #3d5afe
            );
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
            min-height: 20px;
            min-width: 200px;
        """)
        verify_btn.clicked.connect(self.verify_license)
        
        # Center the button
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(verify_btn)
        button_layout.addStretch(1)
        content_layout.addLayout(button_layout)
        
        # Add content frame to main layout
        main_layout.addWidget(content_frame)
        
        # Set focus to the input field
        self.license_input.setFocus()
        
    def verify_license(self):
        """Verify the entered license code."""
        # For development, accept any code
        entered_code = self.license_input.text().strip()
        
        if entered_code:  # Accept any non-empty code for now
            self.accept()
        else:
            self.status_label.setText("Please enter a license code.")
            self.license_input.setFocus() 
