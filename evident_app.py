import os
import re
import time
import threading
import random
import string
import socket
import zipfile
import boto3
from botocore.exceptions import ClientError
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QComboBox, QPushButton, QHBoxLayout, 
    QVBoxLayout, QLabel, QLineEdit, QFileDialog, QProgressBar, QMessageBox, 
    QFrame, QGraphicsDropShadowEffect, QSizePolicy, QScrollArea, QTextEdit, 
    QRadioButton, QButtonGroup, QGroupBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer 
from PyQt5.QtGui import QColor, QIntValidator 
import requests

from utils import load_svg_logo
from shaker_controller import ShakerController
from data_collection_worker import DataCollectionWorker
from ip_finder import IPFinder
from custom_events import UpdateShakerBatteryEvent
from sensor_shaker_panel_widget import SensorPanel, ShakerPanel
from dotenv import load_dotenv
from video_panel import VideoPanel

# Load .env file
load_dotenv()


class EVidentApp(QMainWindow):
    """Main application window for the EVident Battery Control Panel."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize application state
        self.sensor_ip1 = '10.1.10.96'
        self.sensor_ip2 = '10.1.10.171'
        self.shaker_controller = ShakerController()
        self.dual_sensor_mode = True
        self.save_path = os.getcwd()
        self.test_number = 1
        self.worker = None
        self.ip_finder = None
        self.test_id = self.generate_test_id()
        self.had_redos_in_sequence = False  # Keep this as it might be used for other purposes
        self.redo_triggered = False  # Flag to prevent multiple redos
        self.had_outliers = False    # Flag to track if outliers were detected
        self.saved_to_aws = False  # Flag to track if data was saved to AWS
        
        # Instantiate the video panel
        self.video_panel = VideoPanel()
        
        # Setup UI
        self.initUI()
    
    def initUI(self):
        """Initialize the user interface."""
        self.setWindowTitle('EVident Battery Control Panel')
        self.setMinimumWidth(900)
        
        # Apply modern style with gradients
        self.setStyleSheet("""
            QMainWindow {
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
            QPushButton {
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
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1e88e5,
                    stop: 1 #3949ab
                );
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #1565c0,
                    stop: 1 #283593
                );
            }
            QPushButton:disabled {
                background: #cccccc;
                color: #888888;
            }
            QPushButton#stopButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #f44336,
                    stop: 1 #d32f2f
                );
            }
            QPushButton#stopButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #e53935,
                    stop: 1 #c62828
                );
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 1ex;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: #1a237e;
                font-size: 14px;
            }
            QComboBox {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                min-width: 150px;
                min-height: 20px;
            }
            QComboBox:hover {
                border: 2px solid #2962ff;
            }
            QLineEdit {
                padding: 8px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                font-size: 14px;
                min-height: 20px;
            }
            QLineEdit:focus {
                border: 2px solid #2962ff;
                background-color: #f8f9fa;
            }
            QLineEdit:disabled {
                background-color: #f5f5f5;
                color: #9e9e9e;
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #f0f0f0;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #2962ff,
                    stop: 1 #3d5afe
                );
                border-radius: 10px;
            }
            QLabel {
                color: #424242;
                font-size: 14px;
            }
            QFrame {
                background-color: white;
                border-radius: 15px;
                padding: 15px;
                margin: 8px;
            }
        """)
        
        # Create a scrollable container for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        scroll_area.setWidget(content_widget)
        self.setCentralWidget(scroll_area)
        
        # Main layout
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Add logo at the top of the application
        logo_container = QFrame()
        logo_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        logo_path = os.path.join(os.path.dirname(__file__), 'Logo EVident - Vector.svg')
        if os.path.exists(logo_path):
            logo_pixmap = load_svg_logo(logo_path, width=300)
            logo_label = QLabel()
            logo_label.setPixmap(logo_pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            logo_layout.addWidget(logo_label)
        
        # Add shadow effect to the logo container
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 30))
        logo_container.setGraphicsEffect(shadow)
        
        # Add logo to main layout
        main_layout.addWidget(logo_container)
        
        # Create configuration section (first panel)
        config_panel = self.create_configuration_panel()
        main_layout.addWidget(config_panel)
        
        # Create customer info section (second panel)
        customer_panel = self.create_customer_info_panel()
        main_layout.addWidget(customer_panel)
        
        # Create data collection section (third panel - now includes progress)
        data_panel = self.create_data_collection_panel()
        main_layout.addWidget(data_panel)
        
        # --- Create Video Panel Section ---
        video_group = QGroupBox("Live Video Feed")
        video_layout = QVBoxLayout(video_group)
        # Add the video panel widget to the group box layout
        self.video_panel.add_to_layout(video_layout)
        # Add shadow effect (optional)
        shadow_video = QGraphicsDropShadowEffect()
        shadow_video.setBlurRadius(20)
        shadow_video.setOffset(0, 10)
        shadow_video.setColor(QColor(0, 0, 0, 30))
        video_group.setGraphicsEffect(shadow_video)
        # Add the video group box to the main layout
        main_layout.addWidget(video_group)
        # --- End Video Panel Section ---
        
        # Create log section (fourth panel - moved up to replace the empty progress panel)
        log_panel = self.create_log_panel()
        main_layout.addWidget(log_panel)
        
        # Add stretch at the bottom
        main_layout.addStretch(1)
        
        # Update the UI based on current settings
        self.update_sensor_mode_ui()
        
        # Connect signals for file path updating AFTER all UI components are created
        self.connect_file_path_signals()
        
        # Connect signals for the video panel
        self.video_panel.connect_signals()
        
        # Now it's safe to update the file path display
        self.update_file_path_display()
        
        # Check the shaker battery status on startup
        QTimer.singleShot(1000, self.refresh_shaker_battery)
    
    def connect_file_path_signals(self):
        """Connect signals for updating the file path display."""
        # Connect signals for file path updating
        self.vin_entry.textChanged.connect(self.update_file_path_display)
        self.make_selector.currentIndexChanged.connect(self.update_file_path_display)
        self.model_selector.currentIndexChanged.connect(self.update_file_path_display)
        self.year_selector.currentIndexChanged.connect(self.update_file_path_display)
        self.mileage_entry.textChanged.connect(self.update_file_path_display)
        self.trim_selector.currentIndexChanged.connect(self.update_file_path_display)
        self.soc_selector.currentIndexChanged.connect(self.update_file_path_display)
        self.file_prefix_entry.textChanged.connect(self.update_file_path_display)
    
    def create_configuration_panel(self):
        """Create the configuration panel."""
        panel = QFrame()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(panel)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 30))
        panel.setGraphicsEffect(shadow)
        
        # Shaker Configuration section
        shaker_group = QGroupBox("Shaker Configuration")
        shaker_layout = QVBoxLayout(shaker_group)
        
        # Create shaker panel
        self.shaker_panel = ShakerPanel(self.shaker_controller)
        self.shaker_panel.add_to_layout(shaker_layout)
        
        # Add shaker group to panel layout
        layout.addWidget(shaker_group)
        
        # Sensor Configuration section
        sensor_group = QGroupBox("Sensor Configuration")
        sensor_layout = QVBoxLayout(sensor_group)
        
        # Sensor count selection
        sensor_count_layout = QHBoxLayout()
        sensor_count_label = QLabel("Number of Sensors:")
        
        # Create radio button group
        self.sensor_count_group = QButtonGroup(self)
        self.one_sensor_radio = QRadioButton("1 Sensor")
        self.two_sensors_radio = QRadioButton("2 Sensors")
        self.two_sensors_radio.setChecked(True)  # Default to dual sensor mode
        
        self.sensor_count_group.addButton(self.one_sensor_radio, 1)
        self.sensor_count_group.addButton(self.two_sensors_radio, 2)
        
        # Add to layout
        sensor_count_layout.addWidget(sensor_count_label)
        sensor_count_layout.addWidget(self.one_sensor_radio)
        sensor_count_layout.addWidget(self.two_sensors_radio)
        sensor_count_layout.addStretch()
        
        sensor_layout.addLayout(sensor_count_layout)
        
        # Create sensor panels
        self.sensor_panel1 = SensorPanel(1, "EVident_Battery_Sensor_1", self.sensor_ip1)
        self.sensor_panel2 = SensorPanel(2, "EVident_Battery_Sensor_2", self.sensor_ip2)
        
        # Add to sensor layout
        self.sensor_panel1.add_to_layout(sensor_layout)
        self.sensor_panel2.add_to_layout(sensor_layout)
        
        # Add sensor group to panel layout
        layout.addWidget(sensor_group)
        
        # Store sensor 2 UI elements for enabling/disabling
        self.sensor2_ui_elements = self.sensor_panel2.get_all_ui_elements()
        
        # Connect signals
        self.shaker_panel.connect_signals(self)
        self.sensor_panel1.connect_signals(self.auto_find_sensor, self.submit_sensor_ip, 1)
        self.sensor_panel2.connect_signals(self.auto_find_sensor, self.submit_sensor_ip, 2)
        
        # Connect sensor count change signal
        self.sensor_count_group.buttonClicked.connect(self.update_sensor_mode)
        
        return panel
    
    def create_customer_info_panel(self):
        """Create the customer information panel."""
        panel = QFrame()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(panel)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 30))
        panel.setGraphicsEffect(shadow)
        
        # Customer Info section
        customer_group = QGroupBox("Vehicle Information")
        customer_layout = QVBoxLayout(customer_group)
        customer_layout.addSpacing(20)
        
        # Row 1: VIN only
        row1_layout = QHBoxLayout()
        
        # VIN Entry
        vin_label = QLabel("VIN:")
        self.vin_entry = QLineEdit()
        self.vin_entry.setPlaceholderText("Vehicle Identification Number")
        
        # Add to row layout
        row1_layout.addWidget(vin_label)
        row1_layout.addWidget(self.vin_entry)
        
        # Row 2: Make, Model, Year, Trim (moved from row 3)
        row2_layout = QHBoxLayout()
        
        # Make dropdown
        make_label = QLabel("Make:")
        self.make_selector = QComboBox()
        self.make_selector.setMaximumWidth(100)
        self.make_selector.addItems(["Tesla", "Nissan"])
        
        # Model dropdown - initially populated with Tesla models
        model_label = QLabel("Model:")
        self.model_selector = QComboBox()
        self.model_selector.setMaximumWidth(100)
        
        # Year dropdown 
        year_label = QLabel("Year:")
        self.year_selector = QComboBox()
        self.year_selector.setMaximumWidth(100)
        self.year_selector.addItems([str(year) for year in range(2000, 2027)])
        self.year_selector.setCurrentText(str(datetime.now().year))  # Default to current year
        
        # Trim Level dropdown (moved from row 3)
        trim_label = QLabel("Trim Level:")
        self.trim_selector = QComboBox()
        self.trim_selector.setMaximumWidth(100)
        self.trim_selector.addItems(["All Wheel Drive", "Rear Wheel Drive", "Performance"])
        
        # Add to row layout
        row2_layout.addWidget(make_label)
        row2_layout.addWidget(self.make_selector)
        row2_layout.addSpacing(150)
        row2_layout.addWidget(model_label)
        row2_layout.addWidget(self.model_selector)
        row2_layout.addSpacing(150)
        row2_layout.addWidget(year_label)
        row2_layout.addWidget(self.year_selector)
        row2_layout.addSpacing(150)
        row2_layout.addWidget(trim_label)
        row2_layout.addWidget(self.trim_selector)
        
        # Row 3: Mileage and SOC dropdown (Trim moved to row 2)
        row3_layout = QHBoxLayout()
        
        # Mileage Entry
        mileage_label = QLabel("Mileage:")
        self.mileage_entry = QLineEdit()
        self.mileage_entry.setPlaceholderText("Vehicle Mileage")
        self.mileage_entry.setValidator(QIntValidator(0, 999999))
        
        # SOC dropdown (0-100%)
        soc_label = QLabel("SOC%:")
        self.soc_selector = QComboBox()
        for soc in range(0, 101, 5):  # Add values 0, 5, 10, ..., 100
            self.soc_selector.addItem(f"{soc}%")
        
        # Add to row layout
        row3_layout.addWidget(mileage_label)
        row3_layout.addWidget(self.mileage_entry)
        row3_layout.addWidget(soc_label)
        row3_layout.addWidget(self.soc_selector)
        row3_layout.addStretch()  # Add stretch to fill empty space
        
        # Row 4: Test ID and File Prefix
        row4_layout = QHBoxLayout()
        
        # Test ID (automatically generated and read-only)
        test_id_label = QLabel("Test ID:")
        self.test_id_entry = QLineEdit()
        self.test_id_entry.setText(self.test_id)
        self.test_id_entry.setReadOnly(True)
        self.test_id_entry.setStyleSheet("background-color: #f5f5f5; color: #757575;")
        
        # File prefix
        prefix_label = QLabel("File Prefix:")
        self.file_prefix_entry = QLineEdit()
        self.file_prefix_entry.setText("imu_data")
        self.file_prefix_entry.setPlaceholderText("File prefix")
        
        # Add to row layout
        row4_layout.addWidget(test_id_label)
        row4_layout.addWidget(self.test_id_entry, 2)
        row4_layout.addWidget(prefix_label)
        row4_layout.addWidget(self.file_prefix_entry)
        row4_layout.addStretch()
        
        # Add all rows to customer layout
        customer_layout.addLayout(row1_layout)
        customer_layout.addLayout(row2_layout)
        customer_layout.addLayout(row3_layout)
        customer_layout.addLayout(row4_layout)
        
        # Add customer group to panel layout
        layout.addWidget(customer_group)
        
        # Connect signals for models based on make selection
        self.make_selector.currentIndexChanged.connect(self.update_models)
        
        # Initial population of models
        self.update_models(0)  # Default to first item (Tesla)
        
        return panel
    
    def update_models(self, index):
        """Update available models based on selected make."""
        self.model_selector.clear()
        
        if self.make_selector.currentText() == "Tesla":
            self.model_selector.addItems(["Model Y", "Model 3", "Model S"])
        elif self.make_selector.currentText() == "Nissan":
            self.model_selector.addItems(["Leaf"])
    
    def create_data_collection_panel(self):
        """Create the data collection panel."""
        panel = QFrame()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout = QVBoxLayout(panel)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 30))
        panel.setGraphicsEffect(shadow)
        
        # Data Collection section
        data_collection_group = QGroupBox("Data Collection")
        data_collection_layout = QVBoxLayout(data_collection_group)
        
        # Create a label to show the save folder path
        save_location_layout = QHBoxLayout()
        self.save_path_label =  QLabel(f"Save Location: {self.save_path}")
        self.save_path_label.setStyleSheet("color: #757575; font-weight: bold; font-size: 12px;")
        save_location_layout.addWidget(self.save_path_label)

        # Row 1: Sample time and save location (removed calibration time)
        row1_layout = QHBoxLayout()

        # Removed calibration time entry
        sample_time_label = QLabel("Sample Time (s):")
        self.sample_time_entry = QLineEdit()
        self.sample_time_entry.setText("5")
        self.sample_time_entry.setValidator(QIntValidator(1, 300))
        self.sample_time_entry.setMaximumWidth(80)
        
        # Save location button
        self.save_location_button = QPushButton("Set Save Location")
        self.save_location_button.setMaximumWidth(200)

        aws_save_btn = QPushButton('Save to AWS')
        aws_save_btn.setMaximumWidth(200)

        # Add to row layout
        row1_layout.addWidget(sample_time_label)
        row1_layout.addWidget(self.sample_time_entry)
        row1_layout.addStretch()
        row1_layout.addWidget(self.save_location_button)
        row1_layout.addWidget(aws_save_btn)
        
        # Row for email entry (new)
        email_layout = QHBoxLayout()
        email_label = QLabel("Email:")
        self.email_entry = QLineEdit()
        self.email_entry.setPlaceholderText("Enter your email address")
        email_submit_button = QPushButton("Submit")
        
        # Add to email layout
        email_layout.addWidget(email_label)
        email_layout.addWidget(self.email_entry, 1)  # Give the email field more space
        email_layout.addWidget(email_submit_button)
        
        # Row for save path display
        path_layout = QHBoxLayout()
        # Add a label to display the full save path
        self.full_path_label = QLabel(f"Full save path: {self.save_path}")
        self.full_path_label.setStyleSheet("color: #757575; font-style: italic; font-size: 12px;")
        path_layout.addWidget(self.full_path_label)
        
        # Row 2: Collection controls - removed abort button
        row2_layout = QHBoxLayout()
        
        # Collection control button - only start button now
        start_collection_button = QPushButton("Start Collection")
        start_collection_button.setObjectName("startButton")
        
        # Add to row layout
        row2_layout.addStretch()
        row2_layout.addWidget(start_collection_button)
        
        # Progress section
        # Sensor 1 Progress
        sensor1_progress_layout = QHBoxLayout()
        sensor1_progress_label = QLabel("Sensor 1:")
        
        sensor1_progress_layout.addWidget(sensor1_progress_label)
        sensor1_progress_layout.addWidget(self.sensor_panel1.status_label)
        sensor1_progress_layout.addStretch()
        
        self.sensor1_progress_bar = QProgressBar()
        self.sensor1_progress_bar.setFixedHeight(20)
        self.sensor1_progress_bar.setTextVisible(True)
        self.sensor1_progress_bar.setFormat("Ready")
        
        # Sensor 2 Progress
        sensor2_progress_layout = QHBoxLayout()
        sensor2_progress_label = QLabel("Sensor 2:")
        
        sensor2_progress_layout.addWidget(sensor2_progress_label)
        sensor2_progress_layout.addWidget(self.sensor_panel2.status_label)
        sensor2_progress_layout.addStretch()
        
        self.sensor2_progress_bar = QProgressBar()
        self.sensor2_progress_bar.setFixedHeight(20)
        self.sensor2_progress_bar.setTextVisible(True)
        self.sensor2_progress_bar.setFormat("Ready")
        
        # Overall status
        self.overall_status_label = QLabel("Ready to start data collection")
        self.overall_status_label.setStyleSheet("""
            font-size: 14px;
            color: #2962ff;
            font-weight: bold;
            margin-top: 10px;
        """)
        
        # Add rows to main layout
        data_collection_layout.addLayout(row1_layout)
        data_collection_layout.addLayout(save_location_layout)
        data_collection_layout.addLayout(email_layout)  # Add the new email row
        # data_collection_layout.addLayout(path_layout)
        data_collection_layout.addLayout(row2_layout)
        data_collection_layout.addLayout(sensor1_progress_layout)
        data_collection_layout.addWidget(self.sensor1_progress_bar)
        data_collection_layout.addLayout(sensor2_progress_layout)
        data_collection_layout.addWidget(self.sensor2_progress_bar)
        data_collection_layout.addWidget(self.overall_status_label)
        
        # Add section to panel
        layout.addWidget(data_collection_group)
        
        # Add sensor 2 UI elements to the list
        self.sensor2_ui_elements.extend([
            sensor2_progress_label, 
            self.sensor_panel2.status_label,
            self.sensor_panel2.progress_bar
        ])
        
        # Connect signals - removed the abortion_collection_button connection
        start_collection_button.clicked.connect(self.start_data_collection)
        self.save_location_button.clicked.connect(self.set_save_location)
        aws_save_btn.clicked.connect(self.save_to_aws)
        email_submit_button.clicked.connect(self.submit_email)
        
        return panel
    
    def create_log_panel(self):
        """Create the log panel."""
        panel = QFrame()
        panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(panel)
        
        # Add shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 30))
        panel.setGraphicsEffect(shadow)
        
        # Log section
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.addSpacing(20)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            background-color: #fafafa;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            padding: 5px;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 13px;
        """)
        
        # Set minimum height
        self.log_text.setMinimumHeight(150)
        
        # Clear log button
        clear_log_button = QPushButton("Clear Log")
        clear_log_button.setMaximumWidth(120)
        
        # Add button in a layout to align to right
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(clear_log_button)
        
        # Add elements to log layout
        log_layout.addWidget(self.log_text)
        log_layout.addLayout(button_layout)
        
        # Add log group to panel layout
        layout.addWidget(log_group)
        
        # Connect signals
        clear_log_button.clicked.connect(self.clear_log)
        
        return panel
    
    def generate_test_id(self):
        """A 10-character string representing the current timestamp as the test ID."""
        timestamp = int(time.time())
        test_id = str(timestamp)
        
        return test_id
    
    def update_sensor_mode_ui(self):
        """Update UI elements based on sensor mode."""
        if self.dual_sensor_mode:
            # Enable Sensor 2 UI elements
            for element in self.sensor2_ui_elements:
                element.setEnabled(True)
                element.setStyleSheet(element.styleSheet().replace("color: #9e9e9e;", ""))
        else:
            # Disable Sensor 2 UI elements
            for element in self.sensor2_ui_elements:
                element.setEnabled(False)
                if "color:" not in element.styleSheet():
                    element.setStyleSheet(element.styleSheet() + "color: #9e9e9e;")
    
    def update_sensor_mode(self, button):
        """Handle sensor mode change."""
        self.dual_sensor_mode = (button == self.two_sensors_radio)
        self.update_sensor_mode_ui()
        
        mode_text = "dual" if self.dual_sensor_mode else "single"
        self.log_message(f"Switched to {mode_text} sensor mode", "INFO")
    
    def update_battery_status(self, sensor_id, percentage):
        """Update battery status display."""
        sensor_panel = self.sensor_panel1 if sensor_id == 1 else self.sensor_panel2
        sensor_panel.update_battery_status(percentage)
        self.log_message(f"Sensor {sensor_id} battery: {percentage:.0f}%", "BATTERY")
    
    def log_message(self, message, category=None):
        """Add a message to the log with timestamp and optional category."""
        timestamp = time.strftime('%H:%M:%S')
        
        if category:
            formatted_message = f"[{timestamp}] [{category}] {message}"
        else:
            formatted_message = f"[{timestamp}] {message}"
        
        # Format message based on category
        if category == "ERROR":
            html_message = f'<span style="color: #f44336;">{formatted_message}</span>'
        elif category == "SENSOR 1":
            html_message = f'<span style="color: #2196f3;">{formatted_message}</span>'
        elif category == "SENSOR 2":
            html_message = f'<span style="color: #4caf50;">{formatted_message}</span>'
        elif category == "BATTERY":
            html_message = f'<span style="color: #ff9800;">{formatted_message}</span>'
        elif category == "SUCCESS":
            html_message = f'<span style="color: #4caf50; font-weight: bold;">{formatted_message}</span>'
        else:
            html_message = formatted_message
        
        # Append to log
        self.log_text.append(html_message)
        
        # Scroll to bottom
        scroll_bar = self.log_text.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
    
    def clear_log(self):
        """Clear the log text area."""
        self.log_text.clear()
        self.log_message("Log cleared", "INFO")
    
    def set_save_location(self):
        """Set the save location for data files."""
        folder = QFileDialog.getExistingDirectory(self, "Select Save Folder")
        if folder:
            self.save_path = folder
            self.save_path_label.setText("Save Folder: " + folder)
            self.log_message(f"Save folder set to: {folder}", "INFO")
    
    # Shaker control methods
    def start_shaker(self):
        """Start the shaker with the selected frequency."""
        try:
            # Get frequency from dropdown or direct input
            if self.shaker_panel.direct_freq_entry.text():
                frequency = float(self.shaker_panel.direct_freq_entry.text())
            else:
                frequency = float(self.shaker_panel.freq_selector.currentText().split()[0])
                
            if self.shaker_controller.set_frequency(frequency):
                self.log_message(f"Shaker started at {frequency} Hz", "SUCCESS")
                self.overall_status_label.setText(f"Shaker running at {frequency} Hz")
            else:
                self.log_message("Failed to start shaker", "ERROR")
        except ValueError:
            self.log_message("Invalid frequency value", "ERROR")
    
    def set_direct_frequency(self):
        """Set frequency from direct input field."""
        self.start_shaker()
    
    def stop_shaker(self):
        """Stop the shaker."""
        if self.shaker_controller.stop():
            self.log_message("Shaker stopped", "SUCCESS")
            self.overall_status_label.setText("Shaker stopped")
        else:
            self.log_message("Failed to stop shaker", "ERROR")
    
    def home_shaker(self):
        """Return shaker to home position."""
        if self.shaker_controller.home():
            self.log_message("Shaker returned to home position", "SUCCESS")
            self.overall_status_label.setText("Shaker at home position")
        else:
            self.log_message("Failed to return shaker to home", "ERROR")
    
    def calibrate_shaker(self):
        """Calibrate the shaker."""
        # Show confirmation dialog using the original style
        confirm = QMessageBox.question(
            self, 
            "Calibrate Shaker",
            "Ensure that the shaker head can move freely. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                self.log_message("Calibrating shaker...", "INFO")
                self.overall_status_label.setText("Calibrating shaker...")
                
                # Send the calibration request directly instead of using the controller class
                response = requests.get(f"{self.shaker_controller.base_url}/calibrate")
                
                if response.status_code == 200:
                    self.log_message("Shaker calibrated successfully", "SUCCESS")
                    
                    # Don't enable the auto raise button yet - move it to after home position is set
                    
                    # Ask to set home position, using the same style as the first dialog
                    set_home = QMessageBox.question(
                        self,
                        "Set Home Position",
                        "Confirm that the shaker head is in the lowest position",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    
                    if set_home == QMessageBox.Yes:
                        self.set_home_position()
                    else:
                        self.overall_status_label.setText("Home position setup cancelled")
                        self.log_message("Home position setup cancelled", "WARNING")
                else:
                    self.log_message(f"Shaker calibration failed with status code: {response.status_code}", "ERROR")
                    self.overall_status_label.setText(f"Calibration failed: {response.status_code}")
                    
            except requests.RequestException as e:
                self.log_message(f"Error calibrating shaker: {str(e)}", "ERROR")
                self.overall_status_label.setText(f"Calibration error: {str(e)}")
    
    def set_home_position(self):
        """Set the home position of the shaker."""
        try:
            self.log_message("Setting home position...", "INFO")
            self.overall_status_label.setText("Setting home position...")
            
            # Send the set home request directly
            response = requests.get(f"{self.shaker_controller.base_url}/set_home")
            
            if response.status_code == 200:
                self.log_message("Home position set successfully", "SUCCESS")
                self.overall_status_label.setText("Calibration complete, home position set")
                
                # Enable the auto raise button here, after home position is successfully set
                self.shaker_panel.auto_raise_button.setEnabled(True)
            else:
                self.log_message(f"Failed to set home position: {response.status_code}", "ERROR")
                self.overall_status_label.setText(f"Failed to set home position: {response.status_code}")
                
        except requests.RequestException as e:
            self.log_message(f"Error setting home position: {str(e)}", "ERROR")
            self.overall_status_label.setText(f"Error setting home position: {str(e)}")
    
    def auto_raise_shaker(self):
        """Automatically raise the shaker."""
        if self.shaker_controller.auto_raise():
            self.log_message("Shaker auto-raise initiated", "SUCCESS")
            self.overall_status_label.setText("Shaker auto-raise in progress")
        else:
            self.log_message("Failed to start auto-raise", "ERROR")
    
    def lower_shaker_pressed(self):
        """Handle lower button press."""
        if self.shaker_controller.lower(True):
            self.log_message("Lowering shaker...", "INFO")
    
    def lower_shaker_released(self):
        """Handle lower button release."""
        if self.shaker_controller.lower(False):
            self.log_message("Stopped lowering shaker", "INFO")
    
    # Controller IP methods
    def auto_find_controller(self):
        """Automatically find shaker controller IP."""
        self.log_message("Searching for shaker controller...", "INFO")
        self.overall_status_label.setText("Searching for shaker controller...")
        self.shaker_panel.controller_progress.setValue(0)
        
        # Create and run IP finder in a separate thread
        self.controller_finder = IPFinder("raspberrypi")
        self.controller_finder_thread = threading.Thread(target=self.controller_finder.run)
        
        # Connect signals
        self.controller_finder.progress.connect(self.update_controller_find_progress)
        self.controller_finder.found_ip.connect(self.set_controller_ip)
        self.controller_finder.error.connect(self.show_error)
        self.controller_finder.finished.connect(self.finder_finished)
        
        # Start thread
        self.controller_finder_thread.start()
    
    def submit_controller_ip(self):
        """Update controller IP from entry field."""
        ip = self.shaker_panel.controller_ip_entry.text().strip()
        if ip:
            # Test connection before setting
            if self.test_controller_connection(ip):
                self.set_controller_ip(ip)
            else:
                self.log_message("Failed to connect to shaker controller", "ERROR")
                self.shaker_panel.controller_progress.setFormat("Failed to connect to shaker controller")
                # popup a message box to the user
                QMessageBox.warning(self, "Shaker Controller Connection Error", "Failed to connect to shaker controller")
    
    def test_controller_connection(self, ip):
        """Test connection to the shaker controller."""
        if not ip.startswith("http://"):
            ip = f"http://{ip}"
        
        controller = ShakerController(ip)
        return controller.ping()
    
    def update_controller_find_progress(self, message, value):
        """Update progress for controller IP finder."""
        self.shaker_panel.controller_progress.setValue(value)
        self.shaker_panel.controller_progress.setFormat(message)
    
    def set_controller_ip(self, ip):
        """Set the controller IP and update the UI."""
        if not ip.startswith("http://"):
            ip = f"http://{ip}"
        
        self.shaker_controller.base_url = ip
        self.shaker_panel.controller_ip_entry.setText(ip.replace("http://", ""))
        self.log_message(f"Shaker controller IP set to {ip}", "SUCCESS")
        self.shaker_panel.controller_progress.setFormat(f"Shaker controller IP set to {ip.replace("http://", "")}")
        self.overall_status_label.setText(f"Shaker controller IP: {ip}")
        
        # Refresh battery status with new IP
        self.refresh_shaker_battery()
    
    def show_error(self, message):
        """Display error message in the UI."""
        self.log_message(message, "ERROR")
        self.overall_status_label.setText(f"Error: {message}")
    
    def finder_finished(self):
        """Handle completion of IP finder."""
        self.log_message("IP search complete", "INFO")
    
    def auto_find_sensor(self, sensor_id):
        """Automatically find sensor IP."""
        # Get the hostname from the input field
        sensor_panel = self.sensor_panel1 if sensor_id == 1 else self.sensor_panel2
        device_name = sensor_panel.hostname_entry.text().strip()
            
        if not device_name:
            self.show_error(f"Please enter a hostname for Sensor {sensor_id}")
            return
            
        self.log_message(f"Searching for sensor {sensor_id} with hostname: {device_name}...", "INFO")
        
        # Reset the progress bar
        sensor_panel.finder_progress.setValue(0)
        
        # Create and run IP finder in a separate thread
        self.sensor_finder = IPFinder(device_name)
        self.sensor_finder_thread = threading.Thread(target=self.sensor_finder.run)
        
        # Connect signals
        self.sensor_finder.progress.connect(lambda msg, val: self.update_sensor_find_progress(sensor_id, msg, val))
        self.sensor_finder.found_ip.connect(lambda ip: self.set_sensor_ip(sensor_id, ip))
        self.sensor_finder.error.connect(self.show_error)
        self.sensor_finder.finished.connect(self.finder_finished)
        
        # Start thread
        self.sensor_finder_thread.start()
    
    def update_sensor_find_progress(self, sensor_id, message, value):
        """Update progress for sensor IP finder."""
        sensor_panel = self.sensor_panel1 if sensor_id == 1 else self.sensor_panel2
        sensor_panel.status_label.setText(message)
        sensor_panel.finder_progress.setValue(value)
        sensor_panel.finder_progress.setFormat(message)
    
    def set_sensor_ip(self, sensor_id, ip):
        """Set the sensor IP and update the UI."""
        sensor_panel = self.sensor_panel1 if sensor_id == 1 else self.sensor_panel2
        sensor_panel.ip_entry.setText(ip)
        
        if sensor_id == 1:
            self.sensor_ip1 = ip
        else:
            self.sensor_ip2 = ip
        
        self.log_message(f"Sensor {sensor_id} IP set to {ip}", "SUCCESS")
    
    def submit_sensor_ip(self, sensor_id):
        """Update sensor IP from entry field."""
        sensor_panel = self.sensor_panel1 if sensor_id == 1 else self.sensor_panel2
        ip = sensor_panel.ip_entry.text().strip()
            
        if ip:
            self.set_sensor_ip(sensor_id, ip)
    
    def start_data_collection(self):
        """Start the data collection process."""
        # Validate inputs
        try:
            # Fixed 5-second calibration time (removed from UI)
            calibration_time = 5  
            sample_time = int(self.sample_time_entry.text())
            # Use the internal test_number property instead of getting it from UI
            test_number = self.test_number
            
            if not self.sensor_ip1:
                self.show_error("Please set Sensor 1 IP address")
                return
                
            # Add debug logging for IP addresses
            self.log_message(f"Using Sensor 1 IP: {self.sensor_ip1}", "INFO")
            
            if self.dual_sensor_mode and not self.sensor_ip2:
                self.show_error("Please set Sensor 2 IP address for dual sensor mode")
                return
            
            if self.dual_sensor_mode:
                self.log_message(f"Using Sensor 2 IP: {self.sensor_ip2}", "INFO")
                
            if not self.vin_entry.text():
                self.show_error("Please enter a VIN")
                return
                
            if not self.mileage_entry.text():
                self.show_error("Please enter vehicle mileage")
                return
            
            # Get SOC value (remove % sign)
            soc_value = self.soc_selector.currentText().replace("%", "")
                
        except ValueError:
            self.show_error("Please enter valid numeric values for all fields")
            return
        
        # Test sensor connections before starting
        sensor1_connected = self.test_sensor_connection(1)
        if not sensor1_connected:
            self.show_error(f"Cannot connect to Sensor 1 at {self.sensor_ip1}:8888")
            return
        
        if self.dual_sensor_mode:
            sensor2_connected = self.test_sensor_connection(2) 
            if not sensor2_connected:
                self.show_error(f"Cannot connect to Sensor 2 at {self.sensor_ip2}:8888")
                return
        
        # Create the configuration dictionary
        config = {
            'calibration_time': calibration_time,
            'sample_time': sample_time,
            'sensor_ip1': self.sensor_ip1,
            'sensor_ip2': self.sensor_ip2 if self.dual_sensor_mode else None,
            'dual_sensor_mode': self.dual_sensor_mode,
            'save_path': self.save_path,
            'file_prefix': self.file_prefix_entry.text(),
            'car_model': f"{self.make_selector.currentText()} {self.model_selector.currentText()}",
            'year': self.year_selector.currentText(),
            'vin': self.vin_entry.text(),
            'mileage': self.mileage_entry.text(),
            'soc': soc_value,
            'trim': self.trim_selector.currentText(),
            'test_number': test_number,
            'test_id': self.test_id
        }
        
        # Reset progress UI for data collection
        self.sensor_panel1.progress_bar.setValue(0)
        self.sensor_panel2.progress_bar.setValue(0)
        self.sensor_panel1.progress_bar.setFormat("Ready")  # Reset format
        self.sensor_panel2.progress_bar.setFormat("Ready")  # Reset format
        self.sensor_panel1.status_label.setText("Starting...")
        self.sensor_panel2.status_label.setText("Starting..." if self.dual_sensor_mode else "Disabled")
        self.overall_status_label.setText("Starting data collection...")
        
        # Generate a new test ID for this run
        self.test_id = self.generate_test_id()
        # Remove reference to test_number_entry which no longer exists
        # self.test_number_entry.setText(str(self.test_number))
        
        # Log start of collection
        self.log_message(f"Starting data collection", "INFO")
        self.log_message(f"Vehicle: {self.make_selector.currentText()} {self.model_selector.currentText()} ({self.year_selector.currentText()}), VIN: {self.vin_entry.text()}", "INFO")
        self.log_message(f"Trim: {self.trim_selector.currentText()}, Mileage: {self.mileage_entry.text()}, SOC: {self.soc_selector.currentText()}%", "INFO")
        self.log_message(f"Test ID: {self.test_id}", "INFO")
        
        # Reset redo tracking if this is the first test
        if test_number == 1:
            self.had_redos_in_sequence = False
        
        # Create and start worker with the config
        self.worker = DataCollectionWorker(config)
        
        # Connect signals
        self.worker.progress.connect(lambda msg, val: self.overall_status_label.setText(msg))
        self.worker.sensor_progress.connect(self.update_sensor_collection_progress)
        self.worker.battery_update.connect(self.update_battery_status)
        self.worker.error.connect(self.show_error)
        self.worker.sensor_error.connect(lambda sensor_id, msg: self.log_message(f"Sensor {sensor_id}: {msg}", "ERROR"))
        self.worker.data_saved.connect(lambda sensor_id, filename: self.log_message(f"Sensor {sensor_id} data saved to: {filename}", "SUCCESS"))
        self.worker.finished.connect(self.data_collection_finished)
        self.worker.need_redo.connect(self.auto_redo_test)
        self.worker.outliers_detected.connect(self.handle_outliers)  # New signal connection
        
        # Start worker in a new thread
        self.worker_thread = threading.Thread(target=self.worker.run)
        self.worker_thread.daemon = True
        self.worker_thread.start()
    
    def auto_redo_test(self):
        """Automatically redo test when timing issues are detected."""
        # Only trigger a redo if not already in redo mode
        if not self.redo_triggered:
            self.log_message("Timing issues detected - automatically redoing test", "WARNING")
            self.redo_triggered = True
            QTimer.singleShot(1000, self.redo_test)  # Slight delay before redoing
    
    def data_collection_finished(self):
        """Handle completion of data collection."""
        # Check for errors
        has_errors = hasattr(self.worker, 'error_occurred') and self.worker.error_occurred
        
        # We no longer check for timing issues
        # Get current test number from the internal property
        current_test = self.test_number
        # We no longer have tests_to_run, so we always consider it the last test
        is_last_test = True
        
        if has_errors:
            self.log_message("Data collection completed with errors", "ERROR")
            self.overall_status_label.setText("Data collection completed with errors")
            
            QMessageBox.warning(
                self,
                "Data Collection Completed with Errors",
                "Data collection has completed, but there were some errors. Please check the log for details.",
                QMessageBox.Ok
            )
        else:
            # Check if outliers were detected
            outliers_detected = hasattr(self.worker, 'outlier_detected') and self.worker.outlier_detected
            
            # Log completion but only show dialog if no outliers and not in redo mode
            self.log_message("Data collection complete", "SUCCESS")
            
            if outliers_detected or self.redo_triggered:
                self.overall_status_label.setText("Processing data - checking for timing issues...")
            else:
                self.overall_status_label.setText("Data collection complete")
                
                # Only show success dialog when all tests are complete and no outliers detected
                if is_last_test:
                    QMessageBox.information(
                        self,
                        "Data Collection Complete",
                        "All tests have been completed successfully.",
                        QMessageBox.Ok
                    )
        
        # We no longer need to check for the next test since we only do one at a time
    
    def update_file_path_display(self):
        """Update the full path display with the complete filename pattern."""
        # Get SOC value (remove % sign)
        soc_value = self.soc_selector.currentText().replace("%", "")
        
        # Create filename pattern based on current values
        file_pattern = (
            f"{self.vin_entry.text()}_{self.make_selector.currentText()}_{self.model_selector.currentText().replace(' ', '_')}_"
            f"{self.year_selector.currentText()}_{self.mileage_entry.text()}_"
            f"{self.trim_selector.currentText().replace(' ', '_')}_{soc_value}_"
            f"{self.file_prefix_entry.text()}_{self.test_id}_[timestamp]_sensor[1-2].csv"
        )
        
        # Update the display
        full_path = os.path.join(self.save_path, file_pattern)
        self.full_path_label.setText(f"Full save path pattern: {full_path}")

    def update_sensor_collection_progress(self, sensor_id, message, progress):
        """Update the progress display for a sensor during data collection."""
        if sensor_id == 1:
            self.sensor1_progress_bar.setValue(progress)
            self.sensor1_progress_bar.setFormat(message)
            self.sensor_panel1.status_label.setText(message)
        else:  # sensor_id == 2
            self.sensor2_progress_bar.setValue(progress)
            self.sensor2_progress_bar.setFormat(message)
            self.sensor_panel2.status_label.setText(message)
        
        self.log_message(message, f"SENSOR {sensor_id}")
    
    def show_warning_dialog(self, title, message):
        """Show a warning message box to the user."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()

    def save_to_aws(self):
        if self.save_path is None:
            self.log_message("Please set the save location first.", "ERROR")
            return

        # Check if any required field is empty
        if not (self.vin_entry.text().strip() and self.make_selector.currentText() and 
                self.model_selector.currentText() and self.year_selector.currentText() and
                self.mileage_entry.text() and self.soc_selector.currentText() and self.test_id):
            
            # Log error if any field is empty
            self.log_message("Failed to save: Please ensure all vehicle information are filled.", "ERROR")
            
            self.show_warning_dialog("Missing Information", "Please ensure all vehicle information are filled.")
        
            return

        # VIN_Make_Model_Year_Mileage_SoC_Code
        folder_name = self.vin_entry.text().strip() + '_' + self.make_selector.currentText() + '_' + \
            self.model_selector.currentText() + '_' + self.year_selector.currentText() + '_' + \
            self.mileage_entry.text() + '_' + self.soc_selector.currentText() + '_' + self.test_id
        
        zip_filename = os.path.join(self.save_path, f"{folder_name}.zip")
        
        if not os.access(self.save_path, os.W_OK):
            self.log_message("You don't have write permissions for this folder.", "ERROR")
            return

        # Remove existing ZIP file to avoid permission conflicts.
        if os.path.exists(zip_filename):
            try:
                os.remove(zip_filename)
            except PermissionError:
                self.log_message("Existing ZIP file cannot be removed. Check file permissions.", "ERROR")
                return

        try:
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Walk through the entire directory structure.
                for root, dirs, files in os.walk(self.save_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Skip the ZIP file itself to prevent including it inside the archive.
                        if os.path.abspath(file_path) == os.path.abspath(zip_filename):
                            continue
                        # Get the relative path for a clean folder structure in the archive.
                        relative_path = os.path.relpath(file_path, self.save_path)
                        zipf.write(file_path, arcname=relative_path)

            upload_result = self.upload_zip_to_aws(zip_filename)

            if upload_result:
                # Show success dialog if upload to AWS is successful
                self.show_warning_dialog("Upload Successful", f"Data uploaded to AWS successfully!")
            else:
                # Show error dialog if upload to AWS fails
                self.show_warning_dialog("Upload Failed", "Failed to upload data to AWS.")
        
        except PermissionError:
            self.log_message("Please check your folder permissions.", "ERROR")
            self.show_warning_dialog("Permission Error", "Please check your folder permissions.")
        except Exception as e:
            self.show_warning_dialog("Error", f"Error occurred while uploading data: {str(e)}")
            self.log_message(f"Error zipping files: {str(e)}", "ERROR")
        
        self.saved_to_aws = True
        os.remove(zip_filename)  # Delete the zip file

    def upload_zip_to_aws(self, zip_filename):
        """
        Uploads the generated zip file to AWS S3.
        """
        try:
            bucket_name = "evb-cloud-store"
            s3_key = os.path.basename(zip_filename)

            s3 = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )

            s3.upload_file(zip_filename, bucket_name, s3_key)
            self.log_message(f"Successfully uploaded {zip_filename} to {bucket_name}/{s3_key}", "SUCCESS")
            return True  # Return True if upload is successful
        except Exception as e:
            self.log_message(f"Error uploading to AWS: {str(e)}", "ERROR")
            return False  # Return False if there was an error

    def submit_email(self):
        """Submit the email address from the entry field."""
        email = self.email_entry.text().strip()
        
        # Email validation regex
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Check if email is valid
        if not re.match(email_regex, email):
            self.log_message("Please enter a valid email address", "ERROR")
            self.show_warning_dialog("Invalid Email", "Please enter a valid email address")
            return

        if email:
            if self.saved_to_aws is False:
                self.log_message("Please save to AWS first.", "ERROR")
                self.show_warning_dialog("Missing Save", "Please save to AWS first.")
                return
            
            # Send email via AWS SES
            result = self.send_email_via_aws(email)
            self.log_message(result, "INFO")
            
            # Show the result of sending the email
            if "success" in result.lower():
                self.show_warning_dialog("Email Sent", "Email sent successfully!")
            else:
                self.show_warning_dialog("Email Failed", "Failed to send email.")
        else:
            self.log_message("Please enter an email address", "ERROR")
            self.show_warning_dialog("Missing Email", "Please enter an email address") 

    def send_email_via_aws(self, recipient_email):
        SENDER = "EVident Battery <no-reply@batteryevidence.com>"  # Sender email address (must be verified in SES)
        AWS_REGION = "us-east-1"  # AWS SES region, adjust as needed
        SUBJECT = "Confidential Access Code to Your Data"
        BODY_TEXT = f"""\
Hi,

To securely access your data stored online, please use the confidential access code below:

**{self.test_id}**

This code is unique to you and should not be shared with anyone. Keeping this information secure ensures your data remains protected.

If you have any issues or need further assistance, please contact us at info@batteryevidence.com.

Best regards,  
EVident Battery Team
"""
        CHARSET = "UTF-8"

        # Create an AWS SES client
        client = boto3.client(
            'ses', 
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        try:
            # Use the send_email method to send the email
            response = client.send_email(
                Destination={
                    'ToAddresses': [recipient_email],
                },
                Message={
                    'Body': {
                        'Text': {
                            'Charset': CHARSET,
                            'Data': BODY_TEXT,
                        },
                    },
                    'Subject': {
                        'Charset': CHARSET,
                        'Data': SUBJECT,
                    },
                },
                Source=SENDER,
            )
        except ClientError as e:
            # Capture exceptions that occur during email sending and return the error message
            return f"Email sending failed: {e.response['Error']['Message']}"
        else:
            # Return the MessageId upon successful email sending
            return f"The retrieval code has been successfully sent to {recipient_email}."

    def test_sensor_connection(self, sensor_id):
        """Test connection to a sensor and report result."""
        ip = self.sensor_ip1 if sensor_id == 1 else self.sensor_ip2
        port = 8888  # Default port
        
        try:
            # Create a socket
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2.0)  # 2 second timeout
            
            # Try to connect
            result = s.connect_ex((ip, port))
            s.close()
            
            if result == 0:
                self.log_message(f"Sensor {sensor_id} ({ip}:{port}) is reachable", "INFO")
                return True
            else:
                self.log_message(f"Sensor {sensor_id} ({ip}:{port}) is not reachable, error code: {result}", "ERROR")
                return False
        except Exception as e:
            self.log_message(f"Error testing connection to sensor {sensor_id} ({ip}:{port}): {str(e)}", "ERROR")
            return False

    def handle_outliers(self, sensor_id, median_value, max_outlier):
        """Handle outliers detected in delta time data by automatically redoing the test."""
        self.log_message(f"Sensor {sensor_id}: Delta time outliers detected - median: {median_value:.6f}s, max outlier: {max_outlier:.6f}s", "WARNING")
        self.overall_status_label.setText(f"Outliers detected in Sensor {sensor_id} data. Auto-redoing test...")
        
        # Set flag that we had outliers
        self.had_outliers = True
        
        # Set the redo trigger to prevent multiple redos
        self.redo_triggered = True
        
        # Wait a moment before redoing the test to allow UI updates
        QTimer.singleShot(2000, self.redo_test)
    
    def redo_test(self):
        """Redo the test with same parameters."""
        # Check if we've already processed a redo to prevent multiple redos
        if not self.redo_triggered:
            return
        
        # If there were previously generated files, remove them
        for sensor_id, filename in self.worker.filenames.items():
            if filename and os.path.exists(filename):
                try:
                    os.remove(filename)
                    self.log_message(f"Removed file from failed test: {filename}", "INFO")
                except Exception as e:
                    self.log_message(f"Warning: Could not remove file: {str(e)}", "WARNING")
        
        # Reset the redo trigger before starting the collection
        self.redo_triggered = False
        
        self.log_message(f"Test will be redone due to timing outliers", "INFO")
        
        # Restart the data collection
        self.start_data_collection()

    def refresh_shaker_battery(self):
        """Refresh the shaker battery status."""
        self.log_message("Refreshing shaker battery status...", "INFO")
        # Start in a separate thread to avoid blocking UI
        threading.Thread(target=self._get_shaker_battery_status, daemon=True).start()

    def _get_shaker_battery_status(self):
        """Get the shaker battery status in a separate thread."""
        voltage = self.shaker_controller.get_battery_voltage()
        # Use signal to update UI from thread
        if voltage is not None:
            # Update UI in main thread
            QApplication.instance().postEvent(self, 
                UpdateShakerBatteryEvent(voltage))
            return True
        else:
            self.log_message("Failed to get shaker battery status", "WARNING")
            return False

    def update_shaker_battery_status(self, voltage):
        """Update the shaker battery status display."""
        # Update battery display through the shaker panel
        self.shaker_panel.update_battery_status(voltage)
        
        # Keep the logging in the main app
        self.log_message(f"Shaker battery voltage: {voltage:.2f}V", "BATTERY")

    def event(self, event):
        """Handle custom events."""
        if event.type() == UpdateShakerBatteryEvent.EVENT_TYPE:
            self.update_shaker_battery_status(event.voltage)
            return True
        return super().event(event)

    def closeEvent(self, event):
        """Ensure resources are released when the window closes."""
        self.log_message("Closing application...", "INFO")

        # Cleanup video panel resources
        if self.video_panel:
            self.video_panel.cleanup()

        # Stop worker thread if running (add this if not already handled)
        if self.worker and self.worker_thread and self.worker_thread.is_alive():
             self.log_message("Attempting to stop data collection worker...", "INFO")
             # Implement a safe stop mechanism in your worker if possible
             # self.worker.stop() # Example - you'd need to implement this
             # self.worker_thread.join(timeout=2) # Wait briefly

        # Add cleanup for other resources if needed (e.g., shaker controller)

        self.log_message("Cleanup complete. Exiting.", "INFO")
        event.accept() # Accept the close event