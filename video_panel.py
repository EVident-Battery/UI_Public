import sys
import platform
import vlc
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame, QMessageBox, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer

class VideoPanel(QWidget):
    """UI panel for displaying and controlling an RTSP video stream using VLC."""

    def __init__(self, default_rtsp_url="rtsp://10.1.10.152:8554/cam", parent=None):
        super().__init__(parent)
        self.default_rtsp_url = default_rtsp_url
        self.vlc_instance = None
        self.media_player = None
        self.is_playing = False

        # Initialize VLC
        self._initialize_vlc()

        # Create UI elements
        self._create_ui_elements()

        # Set initial state
        self._update_button_states()

    def _initialize_vlc(self):
        """Initializes the VLC instance and media player."""
        try:
            # VLC options can be added here if needed
            vlc_options = ["--no-xlib"] # Example option, might be needed on Linux
            self.vlc_instance = vlc.Instance(vlc_options)
            self.media_player = self.vlc_instance.media_player_new()
            print("VLC instance and media player created successfully.")
        except Exception as e:
            print(f"Error initializing VLC: {e}")
            QMessageBox.critical(self, "VLC Error", f"Failed to initialize VLC. Please ensure VLC is installed correctly.\nError: {e}")
            self.vlc_instance = None
            self.media_player = None

    def _create_ui_elements(self):
        """Creates the UI elements for the video panel."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0) # Use parent margins

        # --- URL Input and Controls ---
        control_layout = QHBoxLayout()

        url_label = QLabel("RTSP URL:")
        self.url_entry = QLineEdit()
        self.url_entry.setText(self.default_rtsp_url)
        self.url_entry.setPlaceholderText("Enter RTSP stream URL")

        self.connect_button = QPushButton("Connect")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("stopButton") # Use style from main app

        control_layout.addWidget(url_label)
        control_layout.addWidget(self.url_entry, 1) # Stretch URL entry
        control_layout.addWidget(self.connect_button)
        control_layout.addWidget(self.stop_button)

        # --- Video Display Area ---
        self.video_frame = QFrame()
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_frame.setMinimumSize(320, 240) # Set a minimum size
        self.video_frame.setStyleSheet("background-color: black;")
        # Ensure the frame can receive focus for embedding if needed, though winId is usually sufficient
        self.video_frame.setAttribute(Qt.WA_OpaquePaintEvent)

        # --- Add to Main Layout ---
        self.main_layout.addLayout(control_layout)
        self.main_layout.addWidget(self.video_frame, 1) # Allow video frame to expand

    def connect_signals(self):
        """Connects button signals to methods."""
        if self.media_player:
            self.connect_button.clicked.connect(self.start_stream)
            self.stop_button.clicked.connect(self.stop_stream)
        else:
            # Disable buttons if VLC failed to initialize
            self.connect_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.url_entry.setEnabled(False)

    def add_to_layout(self, parent_layout):
        """Adds this video panel widget to a parent layout."""
        # Since this class is already a QWidget, just add it directly
        parent_layout.addWidget(self)

    def start_stream(self):
        """Starts the video stream playback."""
        if not self.media_player:
            self.show_error_message("VLC Error", "Media player is not initialized.")
            return

        if self.is_playing:
            self.stop_stream() # Stop current stream before starting new one

        rtsp_url = self.url_entry.text().strip()
        if not rtsp_url:
            self.show_error_message("Input Error", "Please enter an RTSP URL.")
            return

        print(f"Attempting to play stream: {rtsp_url}")

        try:
            # Create new media object
            media = self.vlc_instance.media_new(rtsp_url)

            # Add options for low latency (adjust caching values as needed)
            # WARNING: Setting caching too low can cause instability.
            # Common values are 100-500ms. 0 might not work well.
            media.add_option(':network-caching=150')
            media.add_option(':live-caching=150')
            # media.add_option(':rtsp-tcp') # Uncomment if UDP causes issues

            self.media_player.set_media(media)

            # Embed the video output into the QFrame
            # This needs to happen *before* play() in some cases,
            # and *after* set_media().
            win_id = int(self.video_frame.winId())
            if platform.system() == "Linux":
                self.media_player.set_xwindow(win_id)
            elif platform.system() == "Windows":
                self.media_player.set_hwnd(win_id)
            elif platform.system() == "Darwin": # macOS
                # This might require specific versions/bindings.
                # Using set_nsobject is the typical approach.
                try:
                    self.media_player.set_nsobject(win_id)
                except Exception as e:
                    print(f"macOS embedding error: {e}. Video might not display.")
                    self.show_error_message("macOS Error", f"Could not embed video: {e}")
            else:
                 print(f"Unsupported platform: {platform.system()}. Video embedding might fail.")


            # Start playing
            play_result = self.media_player.play()
            if play_result == -1:
                self.show_error_message("VLC Playback Error", "Failed to start playback. Check URL and VLC setup.")
                self.is_playing = False
            else:
                print("Playback started.")
                self.is_playing = True
                # Give VLC a moment to start rendering
                # QTimer.singleShot(500, self._check_playback_state)


        except Exception as e:
            self.show_error_message("Error", f"An error occurred: {e}")
            self.is_playing = False

        self._update_button_states()

    def stop_stream(self):
        """Stops the video stream playback."""
        if not self.media_player:
            return

        if self.is_playing:
            print("Stopping playback...")
            self.media_player.stop()
            self.is_playing = False
            print("Playback stopped.")
        else:
            # Ensure player is stopped even if state tracking is off
             self.media_player.stop()

        self._update_button_states()

    def _update_button_states(self):
        """Updates the enabled/disabled state of buttons."""
        if not self.media_player: # VLC not initialized
             self.connect_button.setEnabled(False)
             self.stop_button.setEnabled(False)
             self.url_entry.setEnabled(False)
             return

        self.connect_button.setEnabled(not self.is_playing)
        self.stop_button.setEnabled(self.is_playing)
        self.url_entry.setEnabled(not self.is_playing) # Disable URL entry while playing

    def show_error_message(self, title, message):
        """Helper to display error messages."""
        print(f"ERROR [{title}]: {message}") # Also print to console
        QMessageBox.warning(self, title, message)

    def cleanup(self):
        """Releases VLC resources."""
        print("Cleaning up VideoPanel...")
        if self.media_player:
            if self.media_player.is_playing():
                self.media_player.stop()
            # Release the player itself
            try:
                self.media_player.release()
                print("VLC media player released.")
            except Exception as e:
                 print(f"Error releasing media player: {e}")
            self.media_player = None

        if self.vlc_instance:
            try:
                self.vlc_instance.release()
                print("VLC instance released.")
            except Exception as e:
                 print(f"Error releasing VLC instance: {e}")
            self.vlc_instance = None
        print("VideoPanel cleanup finished.")

    # Override closeEvent if this widget were a top-level window
    # def closeEvent(self, event):
    #     self.cleanup()
    #     super().closeEvent(event)
