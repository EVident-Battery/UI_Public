from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QComboBox
from PyQt5.QtGui import QDoubleValidator

class SensorPanel:
    """UI panel for sensor configuration including hostname, IP, battery status and progress"""
    
    def __init__(self, sensor_id, hostname_default, ip_default):
        self.sensor_id = sensor_id
        self.hostname_default = hostname_default
        self.ip_default = ip_default
        
        # Create all UI components
        self.create_ui_elements()
        
    def create_ui_elements(self):
        """Create all UI elements for this sensor panel"""
        # Hostname row
        self.hostname_layout = QHBoxLayout()
        self.hostname_label = QLabel(f"Sensor {self.sensor_id} Hostname:")
        
        self.hostname_entry = QLineEdit()
        self.hostname_entry.setText(self.hostname_default)
        self.hostname_entry.setPlaceholderText(f"Sensor {self.sensor_id} Hostname")
        
        self.auto_find_button = QPushButton("Auto Find")
        
        # Add to hostname layout
        self.hostname_layout.addWidget(self.hostname_label)
        self.hostname_layout.addWidget(self.hostname_entry)
        self.hostname_layout.addWidget(self.auto_find_button)
        
        # IP row
        self.ip_layout = QHBoxLayout()
        self.ip_label = QLabel(f"Sensor {self.sensor_id} IP:")
        
        self.ip_entry = QLineEdit()
        self.ip_entry.setText(self.ip_default)
        self.ip_entry.setPlaceholderText(f"Sensor {self.sensor_id} IP Address")
        
        self.submit_ip_button = QPushButton("Submit IP")
        
        # Battery status indicator
        self.battery_icon = QLabel("🔋")
        self.battery_icon.setStyleSheet("font-size: 18px;")
        self.battery_value = QLabel("N/A")
        self.battery_value.setStyleSheet("font-weight: bold; color: #4caf50;")
        
        # Add to IP layout
        self.ip_layout.addWidget(self.ip_label)
        self.ip_layout.addWidget(self.ip_entry)
        self.ip_layout.addWidget(self.submit_ip_button)
        self.ip_layout.addWidget(self.battery_icon)
        self.ip_layout.addWidget(self.battery_value)
        
        # Progress bar for IP finder
        self.finder_progress = QProgressBar()
        self.finder_progress.setFixedHeight(20)
        self.finder_progress.setValue(0)
        self.finder_progress.setTextVisible(True)
        self.finder_progress.setFormat("Ready")
        
        # Collection progress elements
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #2962ff; font-weight: bold;")
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        
    def add_to_layout(self, parent_layout):
        """Add all panel elements to the provided parent layout"""
        parent_layout.addLayout(self.hostname_layout)
        parent_layout.addLayout(self.ip_layout)
        parent_layout.addWidget(self.finder_progress)
        
    def connect_signals(self, parent_func1, parent_func2, sensor_id):
        """Connect signals for this sensor panel"""
        self.auto_find_button.clicked.connect(lambda: parent_func1(sensor_id))
        self.submit_ip_button.clicked.connect(lambda: parent_func2(sensor_id))
        
    def get_all_ui_elements(self):
        """Return a list of all UI elements for this sensor"""
        return [
            self.hostname_label, self.hostname_entry, self.auto_find_button,
            self.ip_label, self.ip_entry, self.submit_ip_button, 
            self.battery_icon, self.battery_value, self.finder_progress
        ]
        
    def update_battery_status(self, percentage):
        """Update battery status display"""
        self.battery_value.setText(f"{percentage:.0f}%")
        
        # Update color based on level
        if percentage <= 20:
            self.battery_icon.setStyleSheet("font-size: 18px; color: #f44336;")  # Red
            self.battery_value.setStyleSheet("font-weight: bold; color: #f44336;")
        elif percentage <= 40:
            self.battery_icon.setStyleSheet("font-size: 18px; color: #ff9800;")  # Orange
            self.battery_value.setStyleSheet("font-weight: bold; color: #ff9800;")
        else:
            self.battery_icon.setStyleSheet("font-size: 18px; color: #4caf50;")  # Green
            self.battery_value.setStyleSheet("font-weight: bold; color: #4caf50;")

class ShakerPanel:
    """UI panel for shaker controller configuration including battery status, frequency, and movement controls"""
    
    def __init__(self, controller):
        self.controller = controller
        
        # Create all UI components
        self.create_ui_elements()
        
    def create_ui_elements(self):
        """Create all UI elements for the shaker panel"""
        # Shaker battery status indicator
        self.battery_layout = QHBoxLayout()
        self.battery_label = QLabel("Shaker Battery:")
        self.battery_icon = QLabel("🔋")
        self.battery_icon.setStyleSheet("font-size: 18px; color: #4caf50;")
        self.battery_value = QLabel("N/A")
        self.battery_value.setStyleSheet("font-weight: bold; color: #4caf50;")
        self.refresh_battery_button = QPushButton("Refresh")
        self.refresh_battery_button.setMaximumWidth(100)
        
        # Add widgets to battery layout
        self.battery_layout.addWidget(self.battery_label)
        self.battery_layout.addWidget(self.battery_icon)
        self.battery_layout.addWidget(self.battery_value)
        self.battery_layout.addWidget(self.refresh_battery_button)
        self.battery_layout.addStretch()
        
        # Frequency controls
        self.freq_layout = QHBoxLayout()
        
        # Frequency dropdown
        self.freq_selector = QComboBox()
        self.freq_selector.addItems(["10 RPS", "10.33 RPS", "10.66 RPS", "11 RPS", "11.33 RPS", "11.66 RPS"])
        
        # Direct frequency input
        self.direct_freq_entry = QLineEdit()
        self.direct_freq_entry.setPlaceholderText("Direct Frequency (RPS)")
        self.direct_freq_entry.setValidator(QDoubleValidator(0, 2000, 2))
        
        # Control buttons
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton")
        self.home_button = QPushButton("Home")
        
        # Add widgets to frequency layout
        self.freq_layout.addWidget(self.freq_selector)
        self.freq_layout.addWidget(self.direct_freq_entry)
        self.freq_layout.addWidget(self.start_button)
        self.freq_layout.addWidget(self.stop_button)
        self.freq_layout.addWidget(self.home_button)
        
        # Controller settings
        self.controller_layout = QHBoxLayout()
        
        # Controller IP
        self.controller_ip_label = QLabel("Controller IP:")
        self.controller_ip_entry = QLineEdit()
        self.controller_ip_entry.setText(self.controller.base_url.replace("http://", ""))
        self.controller_ip_entry.setPlaceholderText("Controller IP Address")
        
        # Auto-find and submit buttons
        self.auto_find_controller_button = QPushButton("Auto Find")
        self.submit_controller_button = QPushButton("Submit IP")
        
        # Controller buttons
        self.calibrate_button = QPushButton("Calibrate/Set Home")
        self.auto_raise_button = QPushButton("Auto Up")
        self.auto_raise_button.setEnabled(False)  # Disabled initially until calibration
        self.lower_button = QPushButton("Down")
        
        # Add widgets to controller layout
        self.controller_layout.addWidget(self.controller_ip_label)
        self.controller_layout.addWidget(self.controller_ip_entry)
        self.controller_layout.addWidget(self.auto_find_controller_button)
        self.controller_layout.addWidget(self.submit_controller_button)
        self.controller_layout.addWidget(self.calibrate_button)
        self.controller_layout.addWidget(self.auto_raise_button)
        self.controller_layout.addWidget(self.lower_button)
        
        # Progress bar for controller IP finder
        self.controller_progress = QProgressBar()
        self.controller_progress.setFixedHeight(20)
        self.controller_progress.setValue(0)
        self.controller_progress.setTextVisible(True)
        self.controller_progress.setFormat("Ready")
        
    def add_to_layout(self, parent_layout):
        """Add all panel elements to the provided parent layout"""
        parent_layout.addLayout(self.battery_layout)
        parent_layout.addSpacing(20)
        parent_layout.addLayout(self.freq_layout)
        parent_layout.addLayout(self.controller_layout)
        parent_layout.addWidget(self.controller_progress)
    
    def connect_signals(self, parent):
        """Connect signals for this shaker panel"""
        # Connect buttons to parent methods
        self.start_button.clicked.connect(parent.start_shaker)
        self.stop_button.clicked.connect(parent.stop_shaker)
        self.home_button.clicked.connect(parent.home_shaker)
        self.calibrate_button.clicked.connect(parent.calibrate_shaker)
        
        self.auto_find_controller_button.clicked.connect(parent.auto_find_controller)
        self.submit_controller_button.clicked.connect(parent.submit_controller_ip)
        
        self.auto_raise_button.clicked.connect(parent.auto_raise_shaker)
        self.lower_button.pressed.connect(parent.lower_shaker_pressed)
        self.lower_button.released.connect(parent.lower_shaker_released)
        
        self.direct_freq_entry.returnPressed.connect(parent.set_direct_frequency)
        self.refresh_battery_button.clicked.connect(parent.refresh_shaker_battery)
    
    def update_battery_status(self, voltage):
        """Update the battery status display"""
        self.battery_value.setText(f"{voltage:.2f}V")
        
        # Update color based on voltage level
        if voltage <= 14.0:
            self.battery_icon.setStyleSheet("font-size: 18px; color: #f44336;")  # Red
            self.battery_value.setStyleSheet("font-weight: bold; color: #f44336;")
        elif voltage <= 15.0:
            self.battery_icon.setStyleSheet("font-size: 18px; color: #ff9800;")  # Orange
            self.battery_value.setStyleSheet("font-weight: bold; color: #ff9800;")
        else:
            self.battery_icon.setStyleSheet("font-size: 18px; color: #4caf50;")  # Green
            self.battery_value.setStyleSheet("font-weight: bold; color: #4caf50;")