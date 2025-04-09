# EVident Battery Control Panel Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Key Components](#key-components)
4. [User Interface](#user-interface)
5. [Data Collection Process](#data-collection-process)
6. [Multithreading and Concurrency](#multithreading-and-concurrency)
7. [Hardware Communication](#hardware-communication)
8. [Error Handling](#error-handling)
9. [Data Processing and Analysis](#data-processing-and-analysis)
10. [File Management](#file-management)
11. [AWS Integration](#aws-integration)
12. [Security Considerations](#security-considerations)
13. [Performance Considerations](#performance-considerations)
14. [Future Enhancements](#future-enhancements)
15. [Technical Implementation Details](#technical-implementation-details)

## System Overview

The EVident Battery Control Panel is a PyQt5-based application designed for collecting and analyzing inertial measurement unit (IMU) data from sensors attached to electric vehicle batteries. The system interfaces with specialized sensor hardware and a shaker device to perform controlled vibration tests on battery packs while collecting accelerometer and gyroscope data.

The application supports both single and dual sensor configurations, with features for:

- Hardware discovery and connection
- Shaker control (frequency, movement, and calibration)
- Synchronized data collection
- Data validation and quality control
- CSV output formatting
- Data visualization and analysis
- AWS cloud integration

## Architecture

The application follows a modular architecture with clear separation of concerns:

1. **UI Layer** - PyQt5-based interface components
2. **Controller Layer** - Manages application logic and coordinates activities
3. **Service Layer** - Handles hardware communication and data processing
4. **Worker Layer** - Manages background processes and multithreading

### Key Files and Their Roles

- `uiqt5.py` - Application entry point and initialization
- `evident_app.py` - Main application window and core UI logic
- `license_dialog.py` - License verification screen
- `sensor_shaker_panel_widget.py` - UI components for sensor and shaker configuration
- `sensor_data_collector.py` - Handles sensor communication and data capture
- `data_collection_worker.py` - Manages threaded data collection processes
- `shaker_controller.py` - Interface to the shaker hardware
- `ip_finder.py` - Network scanning functionality
- `utils.py` - Utility functions
- `custom_events.py` - Custom PyQt event definitions

## Key Components

### EVidentApp

The main application class that manages the entire UI and coordinates all activities.

```python
class EVidentApp(QMainWindow):
    """Main application window for the EVident Battery Control Panel."""
    # ...
```

Key responsibilities:

- Building and managing the user interface
- Handling user interactions
- Coordinating data collection
- Managing hardware connections
- Processing and saving collected data
- Error handling and user feedback

### SensorDataCollector

Handles direct communication with sensor hardware via TCP/IP sockets.

```python
class SensorDataCollector:
    """Class for handling sensor data collection and processing."""

    def __init__(self, sensor_ip, port=8888, buffer_size=65536):
        # ...
```

Key responsibilities:

- Establishing TCP connections to sensors
- Streaming data from sensors
- Parsing raw sensor data packets
- Extracting battery status information
- Managing calibration and sampling periods
- Buffering and cleaning received data

### DataCollectionWorker

Manages threaded data collection and processing activities.

```python
class DataCollectionWorker(QObject):
    """Worker thread for data collection from sensors."""

    # Define signals
    progress = pyqtSignal(str, int)
    sensor_progress = pyqtSignal(int, str, int)  # sensor_id, message, progress_value
    # ...
```

Key responsibilities:

- Running sensor data collection in background threads
- Coordinating simultaneous data collection from multiple sensors
- Providing progress updates via Qt signals
- Processing and analyzing collected data
- Detecting data quality issues
- Saving data to files
- Handling errors during collection

### ShakerController

Manages communication with the shaker device through HTTP requests.

```python
class ShakerController:
    """Class to handle communication with the shaker controller."""

    def __init__(self, base_url="http://10.1.10.195"):
        # ...
```

Key responsibilities:

- Setting shaker frequency
- Controlling shaker movement
- Managing calibration
- Reading battery status
- Handling error conditions

### IPFinder

Facilitates discovery of devices on the network.

```python
class IPFinder(QObject):
    """Class for finding IP addresses of connected devices."""

    # Define signals
    progress = pyqtSignal(str, int)  # message, progress_value
    # ...
```

Key responsibilities:

- Running network scans in the background
- Identifying devices by hostname
- Providing progress updates
- Handling network errors

### SensorPanel and ShakerPanel

Encapsulate UI components for sensor and shaker configuration.

```python
class SensorPanel:
    """UI panel for sensor configuration including hostname, IP, battery status and progress"""
    # ...

class ShakerPanel:
    """UI panel for shaker controller configuration including battery status, frequency, and movement controls"""
    # ...
```

Key responsibilities:

- Organizing related UI elements
- Providing a clean interface for the main application
- Managing UI state for sensors and shaker
- Communicating user actions to parent components

## User Interface

The UI is structured into several functional panels:

1. **Configuration Panel** - Contains shaker and sensor configuration options
2. **Customer Info Panel** - Captures vehicle information like VIN, make, model, etc.
3. **Data Collection Panel** - Controls for starting collection and monitoring progress
4. **Log Panel** - Displays system activity and error messages

The interface uses PyQt5 widgets with custom styling for a modern appearance, including gradient backgrounds, rounded corners, and contextual color coding for status indicators.

### UI Component Hierarchy

```
EVidentApp (QMainWindow)
│
├── ScrollArea
│   │
│   └── ContentWidget
│       │
│       ├── Logo Container
│       │
│       ├── Configuration Panel
│       │   ├── Shaker Configuration Group
│       │   │   └── ShakerPanel
│       │   │
│       │   └── Sensor Configuration Group
│       │       ├── Sensor Count Selection
│       │       ├── SensorPanel 1
│       │       └── SensorPanel 2
│       │
│       ├── Customer Info Panel
│       │   └── Vehicle Information Group
│       │       ├── VIN Entry
│       │       ├── Make/Model/Year/Trim Selection
│       │       └── Mileage/SOC Selection
│       │
│       ├── Data Collection Panel
│       │   ├── Sample Time Entry
│       │   ├── Save Location Button
│       │   ├── AWS Upload Button
│       │   ├── Email Entry
│       │   ├── Start Collection Button
│       │   ├── Sensor 1 Progress
│       │   ├── Sensor 2 Progress
│       │   └── Overall Status Label
│       │
│       └── Log Panel
│           ├── Log Text Area
│           └── Clear Log Button
```

## Data Collection Process

The data collection process involves several coordinated steps:

1. **Preparation Phase**

   - Validate connection to sensors
   - Validate user input fields
   - Generate unique test ID
   - Prepare file paths

2. **Collection Phase**

   - Create worker object with configuration
   - Start worker thread for non-blocking operation
   - Connect worker signals to UI update methods
   - For each active sensor:
     - Establish socket connection
     - Check battery status
     - Calibrate (initial warm-up period)
     - Collect data for specified sample time
     - Monitor for errors or data quality issues

3. **Processing Phase**

   - Calculate time deltas between samples
   - Check for timing outliers
   - Format data for CSV output
   - Save data to files
   - Optionally upload to AWS

4. **Quality Control Phase**
   - Analyze data for timing issues
   - Detect outliers using statistical methods
   - Automatically retry collection if quality issues detected
   - Notify user of data quality status

### Data Flow Diagram

```
User Input → Configuration → DataCollectionWorker
                                    │
                                    ▼
                               Thread Creation
                                    │
                                    ▼
                      ┌─────────────┴────────────┐
                      │                          │
                      ▼                          ▼
              Sensor 1 Thread              Sensor 2 Thread
                      │                          │
                      ▼                          ▼
              SensorDataCollector         SensorDataCollector
                      │                          │
                      ▼                          ▼
                TCP Connection              TCP Connection
                      │                          │
                      ▼                          ▼
               Data Collection             Data Collection
                      │                          │
                      ▼                          ▼
                Data Processing             Data Processing
                      │                          │
                      ▼                          ▼
                 CSV Output                  CSV Output
                      │                          │
                      └─────────────┬────────────┘
                                    │
                                    ▼
                            Quality Analysis
                                    │
                                    ▼
                          AWS Upload (Optional)
```

## Multithreading and Concurrency

The application uses Python's threading module to handle concurrent operations without blocking the UI.

### Threading Strategy

1. **Main Thread**

   - Handles UI rendering and user interactions
   - Coordinates worker threads
   - Processes UI update signals from workers

2. **Collection Worker Threads**

   - One thread per active sensor for parallel data collection
   - Use thread-safe signal mechanisms to communicate with main thread
   - Join with timeout to allow checking for cancellation

3. **Network Discovery Thread**
   - Runs network scanning operations in background
   - Updates UI with progress information
   - Emits signals when devices are found

### Thread Communication

Communication between threads is handled through PyQt's signal-slot mechanism:

```python
# In DataCollectionWorker class
progress = pyqtSignal(str, int)
sensor_progress = pyqtSignal(int, str, int)
battery_update = pyqtSignal(int, float)
error = pyqtSignal(str)
# ... etc.

# In EVidentApp class
self.worker.progress.connect(lambda msg, val: self.overall_status_label.setText(msg))
self.worker.sensor_progress.connect(self.update_sensor_collection_progress)
self.worker.battery_update.connect(self.update_battery_status)
# ... etc.
```

For cases where direct signal-slot connection is inadequate, custom events are used:

```python
class UpdateShakerBatteryEvent(QEvent):
    """Custom event for updating shaker battery status."""
    EVENT_TYPE = QEvent.registerEventType()

    def __init__(self, voltage):
        super().__init__(UpdateShakerBatteryEvent.EVENT_TYPE)
        self.voltage = voltage
```

## Hardware Communication

### Sensor Communication

Sensors are communicated with via TCP/IP sockets:

```python
def connect(self):
    """Establish connection to the sensor."""
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    self.socket.settimeout(1.0)
    try:
        self.socket.connect((self.sensor_ip, self.port))
        return True
    except Exception as e:
        return str(e)
```

The application uses non-blocking socket operations with timeouts to maintain UI responsiveness:

```python
try:
    data = self.socket.recv(self.buffer_size)
    if not data:
        break

    data_str = data_fragment + data.decode()
    # ... process data
except socket.timeout:
    continue
except Exception:
    break
```

Data is streamed continuously and parsed line-by-line from the socket buffer:

```python
lines = data_str.split('\n')
data_fragment = lines[-1]

for line in lines[:-1]:
    if not line.strip():
        continue

    if line.startswith("BATTERY:"):
        # ... process battery info

    parts = line.split(',')
    if len(parts) == 7:
        # ... process IMU data
```

### Shaker Communication

The shaker controller is communicated with via HTTP requests:

```python
def set_frequency(self, frequency):
    """Set the shaker frequency."""
    try:
        response = requests.get(f"{self.base_url}/move?value={frequency}", timeout=2)
        return response.status_code == 200
    except:
        return False
```

Timeout handling is implemented to prevent UI blocking:

```python
try:
    # Use a longer timeout for calibration (10 seconds)
    response = requests.get(f"{self.base_url}/calibrate", timeout=10)
    return response.status_code == 200
except Exception as e:
    return False
```

## Error Handling

The application implements robust error handling at multiple levels:

1. **UI Level**

   - Input validation
   - Confirmation dialogs
   - Error message boxes
   - Status indicators
   - Log messages

2. **Network Level**

   - Connection timeouts
   - Retry mechanisms
   - Graceful disconnection
   - Socket error handling

3. **Data Collection Level**

   - Exception catching
   - Error reporting
   - Graceful abortion
   - Thread cleanup

4. **Data Quality Level**
   - Automatic detection of data issues
   - Statistical analysis for outliers
   - Auto-retry capabilities
   - Comprehensive logging

### Error Propagation

Errors are propagated through the signal system to maintain separation of concerns:

```python
# In worker thread, capture and emit errors
try:
    # ... operation that might fail
except Exception as e:
    self.error.emit(f"Error in data collection: {str(e)}")
    self.error_occurred = True

# In UI thread, handle the error signal
self.worker.error.connect(self.show_error)

def show_error(self, message):
    """Display error message in the UI."""
    self.log_message(message, "ERROR")
    self.overall_status_label.setText(f"Error: {message}")
```

## Data Processing and Analysis

### IMU Data Format

The collected IMU data has the following format:

```
Time, Accel_X, Accel_Y, Accel_Z, Gyro_X, Gyro_Y, Gyro_Z, Delta_Time
```

Where:

- `Time` is the timestamp (seconds)
- `Accel_X/Y/Z` are accelerometer readings (m/s²)
- `Gyro_X/Y/Z` are gyroscope readings (rad/s)
- `Delta_Time` is the time between consecutive samples (calculated)

### Outlier Detection

The application uses statistical methods to detect timing outliers:

```python
# Calculate median delta time
median_delta = np.median(deltas)

# Threshold for outliers (anything greater than 5% of median is an outlier)
outlier_threshold = 1.05

# Find outliers
outliers = [delta for delta in deltas if delta > (median_delta * outlier_threshold)]

if outliers:
    max_outlier = max(outliers)
    self.outliers_detected.emit(sensor_id, median_delta, max_outlier)
    self.outlier_detected = True
```

When outliers are detected, the application automatically triggers a retry:

```python
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
```

## File Management

### File Naming Convention

Files are named according to a detailed convention that incorporates vehicle information and test parameters:

```
{VIN}_{Make}_{Model}_{Year}_{Mileage}_{Trim}_{SOC}_{FilePrefix}_{TestNumber}_{TestID}_{Timestamp}_sensor{SensorID}.csv
```

Example:

```
WBAFW5C52CD123456_Tesla_Model_Y_2023_15000_All_Wheel_Drive_80_imu_data_001_A1B2C3D4_20230615_120530_sensor1.csv
```

### CSV Format

Data is saved in CSV format with the following header:

```
Time, Accel_X, Accel_Y, Accel_Z, Gyro_X, Gyro_Y, Gyro_Z, Delta_Time
```

Sample data rows:

```
1623765530.123, 0.015, -0.023, 9.812, 0.001, 0.002, -0.001, 0.01
1623765530.133, 0.014, -0.025, 9.815, 0.001, 0.003, -0.001, 0.01
```

## AWS Integration

The application includes functionality to upload collected data to AWS S3:

```python
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

    except Exception as e:
        self.log_message(f"Error uploading to AWS: {str(e)}", "ERROR")
```

The process involves:

1. Creating a ZIP archive of all data files
2. Connecting to AWS S3 using boto3
3. Uploading the ZIP file to a predefined bucket
4. Providing feedback to the user about upload status

## Security Considerations

### AWS Credentials

The application currently embeds AWS credentials directly in the code. In a production environment, this should be modified to:

1. Use IAM roles when deployed on AWS infrastructure
2. Store credentials in environment variables or secure credential storage
3. Use temporary credentials with limited permissions

### Network Security

The application communicates with sensors and shaker hardware on the local network. Considerations include:

1. Ensuring the application is used on a secure, isolated network
2. Validating all incoming data from sensors
3. Implementing secure communication protocols for hardware interactions

## Performance Considerations

### Data Collection Optimization

The application is optimized for real-time data collection through:

1. **Parallel Processing** - Concurrent collection from multiple sensors
2. **Buffered I/O** - Efficient data reading and processing
3. **Non-blocking Operations** - Maintaining UI responsiveness during collection

### Memory Management

For long collection sessions with high-frequency IMU data:

1. Data is streamed directly to CSV files to avoid excessive memory usage
2. Only essential data is kept in memory during processing
3. System resources are monitored and managed during collection

## Future Enhancements

Potential areas for further development include:

### Data Analysis Features

- Real-time frequency spectrum analysis
- Advanced outlier detection algorithms
- Machine learning-based vibration pattern recognition
- Comparative analysis between test runs

### Hardware Support

- Integration with additional sensor types
- Support for wireless IMU sensors
- Expanded shaker controller capabilities
- Battery health estimation features

### User Experience

- Customizable dashboard views
- Interactive data visualization
- Remote monitoring capabilities
- Multi-language support

## Technical Implementation Details

### Sensor Data Collection Protocol

The application implements a specialized protocol for communicating with IMU sensors:

#### Protocol Format

Sensors transmit data in a standardized format over TCP:

```
<timestamp>,<accel_x>,<accel_y>,<accel_z>,<gyro_x>,<gyro_y>,<gyro_z>
```

Battery status is transmitted separately as:

```
BATTERY:<percentage>%
```

#### Calibration Period Implementation

The calibration period serves two critical purposes:

1. **Sensor Warm-up**: Allows MEMS components to stabilize as well as establish a strong wifi connection
2. **Sample Rate Verification**: Establishes timing baseline

The implementation divides collection into distinct phases:

```python
# Simplified calibration phase handling
if in_calibration and elapsed > calibration_time:
    in_calibration = False
    if callback:
        callback("phase_change")

if callback:
    if in_calibration:
        progress = int((elapsed/calibration_time) * 100)
        callback("calibration_progress", progress, elapsed, calibration_time)
    else:
        effective_elapsed = elapsed - calibration_time
        progress = int((effective_elapsed/sample_time) * 100)
        callback("recording_progress", progress, effective_elapsed, sample_time)
```

### Data Processing Algorithms

#### Delta Time Calculation

The application performs precise timing analysis between consecutive samples:

```python
# Calculate delta times between consecutive samples
modified_data = []
prev_time = None
timestamps = []
deltas = []

for row in data:
    current_time = row[0]
    delta = 0.0 if prev_time is None else current_time - prev_time
    modified_data.append(list(row) + [delta])
    prev_time = current_time

    timestamps.append(current_time)
    if prev_time is not None:
        deltas.append(delta)
```

#### Statistical Outlier Detection

The system uses robust statistical methods to identify sampling irregularities:

1. **Median-based Analysis**: Uses median rather than mean to reduce sensitivity to extreme outliers
2. **Percentage-based Thresholding**: Identifies samples deviating by >5% from expected timing
3. **Automatic Recovery**: Triggers data recollection when timing anomalies exceed thresholds

```python
# Implementation details of outlier detection
median_delta = np.median(deltas)
outlier_threshold = 1.05  # 5% deviation threshold
outliers = [delta for delta in deltas if delta > (median_delta * outlier_threshold)]

if outliers:
    max_outlier = max(outliers)
    self.outliers_detected.emit(sensor_id, median_delta, max_outlier)
    self.outlier_detected = True
```

### Multithreading Implementation

#### Thread Management Strategy

The application employs a sophisticated threading model to maintain responsiveness:

```python
# Thread creation for each sensor
if self.config['sensor_ip1']:
    thread1 = threading.Thread(
        target=self.collect_from_sensor,
        args=(1, self.config['sensor_ip1'], base_filename)
    )
    threads.append(thread1)
    thread1.start()

# Thread monitoring with timeout for responsive cancellation
for thread in threads:
    while thread.is_alive():
        thread.join(0.1)  # Join with 100ms timeout to check stop_requested
        if self.stop_requested:
            self.error.emit("Data collection aborted by user")
            self.error_occurred = True
            break
```

#### Signal-Slot Connection Management

The application implements a comprehensive signal-slot network to coordinate thread communication:

```python
# Setup signal connections for worker thread
self.worker.progress.connect(self.update_overall_progress)
self.worker.sensor_progress.connect(self.update_sensor_collection_progress)
self.worker.battery_update.connect(self.update_battery_status)
self.worker.error.connect(self.handle_worker_error)
self.worker.sensor_error.connect(self.handle_sensor_error)
self.worker.finished.connect(self.handle_collection_finished)
self.worker.data_saved.connect(self.handle_data_saved)
self.worker.need_redo.connect(self.handle_collection_redo)
self.worker.outliers_detected.connect(self.handle_outliers)
```

#### Threaded Battery Status Updates

Battery status updates from the shaker controller are implemented in a non-blocking manner:

```python
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
```

### Network Discovery Implementation

The IP finder implements a sophisticated network scanning approach:

#### PowerShell Integration

The application uses PowerShell to perform efficient network discovery:

```python
# Run PowerShell script to find devices
script_path = os.path.join(os.path.dirname(__file__), 'computers_on_network.ps1')

if not os.path.exists(script_path):
    self.error.emit(f"PowerShell script not found: {script_path}")
    self.finished.emit()
    return

process = os.popen(f'powershell -ExecutionPolicy Bypass -File "{script_path}"')
```

#### Progress Tracking

The IP finder provides detailed progress feedback during different scanning phases:

```python
if line.startswith('PROGRESS:'):
    progress_info = line.strip().replace('PROGRESS:', '')

    if progress_info == 'PHASE1':
        self.progress.emit("Step 1/2: Pinging addresses...", 0)
    elif progress_info == 'PHASE2':
        self.progress.emit("Step 2/2: Scanning ARP entries...", 0)
    elif progress_info == 'DONE':
        self.progress.emit("Search complete.", 100)
    elif progress_info.startswith('PING:'):
        try:
            current, total = map(int, progress_info.split(':')[1].split('/'))
            progress = int((current / total) * 100)
            self.progress.emit(f"Step 1/2: Pinging addresses: {current}/{total}", progress)
        except:
            pass
```

### UI State Management

#### Dual Mode Sensor Management

The application intelligently handles UI state based on sensor mode:

```python
def toggle_sensor_mode(self):
    """Toggle between single and dual sensor mode."""
    self.dual_sensor_mode = not self.dual_sensor_mode

    # Update UI based on mode
    if self.dual_sensor_mode:
        self.sensor_mode_button.setText("Dual Sensor Mode")
        self.sensor_panel2.setVisible(True)
        for element in self.sensor_panel2.get_all_ui_elements():
            element.setEnabled(True)
    else:
        self.sensor_mode_button.setText("Single Sensor Mode")
        self.sensor_panel2.setVisible(False)
        for element in self.sensor_panel2.get_all_ui_elements():
            element.setEnabled(False)
```

#### Dynamic UI Updates

The application dynamically updates UI elements based on collection state:

```python
def update_ui_during_collection(self, collecting=True):
    """Enable or disable UI elements based on collection state."""

    # Disable inputs during collection
    self.start_collection_button.setEnabled(not collecting)
    self.calibration_time_spinner.setEnabled(not collecting)
    self.sample_time_spinner.setEnabled(not collecting)
    self.save_location_button.setEnabled(not collecting)

    # Disable/enable sensor config during collection
    self.sensor_mode_button.setEnabled(not collecting)

    # Disable/enable vehicle info fields
    self.vin_entry.setEnabled(not collecting)
    self.make_selector.setEnabled(not collecting)
    # ... and so on for other UI elements

    # Show/hide abort button
    self.abort_button.setVisible(collecting)
```

### Shaker Control Logic

#### Frequency Management

The shaker controller supports both preset and direct frequency settings:

```python
def set_shaker_frequency(self):
    """Set the shaker frequency from the dropdown."""
    selected = self.shaker_panel.freq_selector.currentText()
    frequency = float(selected.split()[0])  # Extract numeric part
    self.set_frequency_value(frequency)

def set_direct_frequency(self):
    """Set a direct frequency value from the text input."""
    freq_text = self.shaker_panel.direct_freq_entry.text()
    try:
        frequency = float(freq_text)
        self.set_frequency_value(frequency)
    except ValueError:
        self.log_message("Invalid frequency value", "ERROR")
```

#### Movement Control

The shaker provides sophisticated movement control options:

```python
def calibrate_shaker(self):
    """Calibrate the shaker and set its home position."""
    self.log_message("Calibrating shaker...", "INFO")
    result = self.shaker_controller.calibrate()

    if result:
        self.log_message("Shaker calibration complete", "SUCCESS")
        # Enable the auto-raise button once calibration is done
        self.shaker_panel.auto_raise_button.setEnabled(True)
    else:
        self.log_message("Failed to calibrate shaker", "ERROR")

def auto_raise_shaker(self):
    """Start the auto raise function of the shaker."""
    self.log_message("Starting auto-raise...", "INFO")
    result = self.shaker_controller.auto_raise()

    if result:
        self.log_message("Shaker auto-raise initiated", "SUCCESS")
    else:
        self.log_message("Failed to start auto-raise", "ERROR")
```

### Data File Management

#### Test ID Generation

The application creates unique test identifiers to ensure data traceability:

```python
def generate_test_id(self, length=8):
    """Generate a unique test ID."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
```

#### ZIP File Creation

Data is packaged into ZIP archives for easy management and upload:

```python
def save_to_aws(self):
    # ...

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
        self.log_message(f"Successfully created zip file: {zip_filename}", "INFO")
        self.upload_zip_to_aws(zip_filename)
    except PermissionError:
        self.log_message("Please check your folder permissions.", "ERROR")
    except Exception as e:
        self.log_message(f"Error zipping files: {str(e)}", "ERROR")
```

### Application Initialization Flow

The application follows a carefully designed initialization sequence:

1. **License Verification**

   ```python
   def main():
       """Main application entry point."""
       app = QApplication(sys.argv)

       # Show license dialog first
       license_dialog = LicenseDialog()
       result = license_dialog.exec_()

       if result == QDialog.Accepted:
           # License verified, show main application
           window = EVidentApp()
           window.show()
           sys.exit(app.exec_())
       else:
           # License verification failed or dialog was closed
           sys.exit(0)
   ```

2. **Main Application Initialization**

   ```python
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

       # Setup UI
       self.initUI()
   ```

3. **UI Construction**
   ```python
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
           /* Additional styling */
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

       # Add logo and UI elements
       # ...
   ```

### Advanced Sensor Data Collection Techniques

#### Data Buffering Strategy

The sensor data collector implements an efficient buffering strategy to handle continuous data streams:

```python
def collect_data(self, calibration_time, sample_time, callback=None):
    """Collect data from sensor with calibration and sampling periods."""
    if not self.socket:
        return [], None

    raw_data = []
    battery_percentage = None
    data_fragment = ""  # Buffer for incomplete lines
    total_time = calibration_time + sample_time
    start_time = time.time()
    in_calibration = True

    while time.time() - start_time < total_time:
        try:
            data = self.socket.recv(self.buffer_size)
            if not data:
                break

            # Append new data to any remaining fragment
            data_str = data_fragment + data.decode()
            lines = data_str.split('\n')

            # The last line might be incomplete, save it for next iteration
            data_fragment = lines[-1]

            # Process all complete lines
            for line in lines[:-1]:
                if not line.strip():
                    continue

                if line.startswith("BATTERY:"):
                    try:
                        battery_value = float(line.replace("BATTERY:", "").replace("%", ""))
                        battery_percentage = battery_value
                    except:
                        continue

                parts = line.split(',')
                if len(parts) == 7:
                    try:
                        client_elapsed = time.time() - start_time
                        timestamp = float(parts[0])
                        ax, ay, az = map(float, parts[1:4])
                        gx, gy, gz = map(float, parts[4:7])
                        raw_data.append((client_elapsed, [timestamp, ax, ay, az, gx, gy, gz]))
                    except:
                        continue
        except socket.timeout:
            continue
        except Exception:
            break

    return raw_data, battery_percentage
```

#### Timestamp Processing

The application performs precise timestamp management for accurate measurements:

```python
# Calculate client-side elapsed time
client_elapsed = time.time() - start_time

# Extract timestamp from sensor data
timestamp = float(parts[0])

# Both timestamps are used - client time for phase tracking,
# sensor time for precise measurement intervals
raw_data.append((client_elapsed, [timestamp, ax, ay, az, gx, gy, gz]))
```

#### Socket Timeout Handling

The collector implements careful timeout handling for robustness:

```python
# Socket initialization with timeout
self.socket.settimeout(1.0)

# Timeout handling in data collection loop
try:
    data = self.socket.recv(self.buffer_size)
    # Process data...
except socket.timeout:
    # Just continue the loop, this is normal operation
    continue
except Exception:
    # Break on other socket errors
    break
```

### Comprehensive Testing and Quality Control

The application implements multiple layers of data quality verification:

#### Timing Analysis

```python
# Multiple timing checks are performed:
# 1. Overall sample count validation
# 2. Sample rate consistency verification
# 3. Statistical outlier detection

# After collecting data
if len(data) < expected_samples:
    self.log_message(f"Warning: Received fewer samples than expected: {len(data)} vs {expected_samples}", "WARNING")

# During delta time analysis
if outliers:
    self.log_message(f"Timing outliers detected - median: {median_delta:.6f}s, max: {max_outlier:.6f}s", "WARNING")
    # Trigger automatic redo
    self.need_redo.emit()
```

#### Data Integrity Verification

```python
# Validate data integrity during parsing
try:
    timestamp = float(parts[0])
    ax, ay, az = map(float, parts[1:4])
    gx, gy, gz = map(float, parts[4:7])
    raw_data.append((client_elapsed, [timestamp, ax, ay, az, gx, gy, gz]))
except ValueError:
    # Skip invalid lines
    self.log_message(f"Skipping invalid data line: {line}", "WARNING")
    continue
```

#### Automatic Recovery

```python
# When outliers are detected, data collection is automatically redone
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
```

## Technical Implementation Details

### Socket Communication Protocol

The sensor hardware communicates with the application using a TCP-based protocol. The data protocol format follows this structure:

1. **Battery Status Messages**:

   ```
   BATTERY:85%
   ```

2. **IMU Data Messages**:
   ```
   timestamp,accel_x,accel_y,accel_z,gyro_x,gyro_y,gyro_z
   ```

Example:

```
1623765530.123,0.015,-0.023,9.812,0.001,0.002,-0.001
```

The `SensorDataCollector` class handles parsing this protocol:

```python
for line in lines[:-1]:
    if not line.strip():
        continue

    if line.startswith("BATTERY:"):
        try:
            battery_value = float(line.replace("BATTERY:", "").replace("%", ""))
            return battery_value
        except:
            continue

    parts = line.split(',')
    if len(parts) == 7:
        try:
            client_elapsed = time.time() - start_time
            timestamp = float(parts[0])
            ax, ay, az = map(float, parts[1:4])
            gx, gy, gz = map(float, parts[4:7])
            raw_data.append((client_elapsed, [timestamp, ax, ay, az, gx, gy, gz]))
        except:
            continue
```

### Multi-Threaded Data Collection Design

The application uses a sophisticated threading model to handle simultaneous data collection from multiple sensors. The diagram below illustrates the thread communication architecture:

```
Main UI Thread <---------> DataCollectionWorker (QObject with Signals)
      ^                        |
      |                        v
      |             ┌──────────┴──────────┐
      |             |                     |
      |     Thread 1 (Sensor 1)    Thread 2 (Sensor 2)
PyQt Signals          |                     |
      |               v                     v
      |        SensorDataCollector    SensorDataCollector
      |               |                     |
      |               v                     v
      └───────> Signal Updates       Signal Updates
```

This architecture is implemented through several key mechanisms:

1. **Thread Creation and Management**

   ```python
   def run(self):
       """Main worker method to collect data from sensors."""
       try:
           # Generate timestamp and base filename
           timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

           # Use the test ID from config
           test_id = self.config['test_id']

           # Base filename creation
           # ...

           # Start threads for each active sensor
           threads = []

           # Sensor 1 thread
           if self.config['sensor_ip1']:
               thread1 = threading.Thread(
                   target=self.collect_from_sensor,
                   args=(1, self.config['sensor_ip1'], base_filename)
               )
               threads.append(thread1)
               thread1.start()

           # Sensor 2 thread (if in dual mode)
           if self.config['dual_sensor_mode'] and self.config['sensor_ip2']:
               thread2 = threading.Thread(
                   target=self.collect_from_sensor,
                   args=(2, self.config['sensor_ip2'], base_filename)
               )
               threads.append(thread2)
               thread2.start()

           # Wait for all threads to complete
           for thread in threads:
               while thread.is_alive():
                   thread.join(0.1)  # Join with timeout to check stop_requested
                   if self.stop_requested:
                       self.error.emit("Data collection aborted by user")
                       self.error_occurred = True
                       break
               if self.stop_requested:
                   break
   ```

2. **Signal-Based Progress Reporting**

   ```python
   # Define callback to update progress
   def progress_callback(event_type, *args):
       if event_type == "phase_change":
           self.sensor_progress.emit(sensor_id, f"Starting recording for sensor {sensor_id}", 0)
       elif event_type == "calibration_progress":
           progress, elapsed, total = args
           self.sensor_progress.emit(
               sensor_id,
               f"Calibrating sensor {sensor_id}: {elapsed:.1f}/{total}s",
               progress
           )
       elif event_type == "recording_progress":
           progress, elapsed, total = args
           self.sensor_progress.emit(
               sensor_id,
               f"Recording sensor {sensor_id}: {elapsed:.1f}/{total}s",
               progress
           )
   ```

3. **Thread-Safe Data Storage**
   ```python
   # Each thread stores data in thread-safe dictionary slots
   self.sensor_data[sensor_id] = data
   self.battery_values[sensor_id] = battery_update
   self.filenames[sensor_id] = filename
   ```

### HTTP-Based Shaker Control Protocol

The shaker controller uses a REST-like HTTP API for hardware communication:

```python
def set_frequency(self, frequency):
    """Set the shaker frequency."""
    try:
        response = requests.get(f"{self.base_url}/move?value={frequency}", timeout=2)
        return response.status_code == 200
    except:
        return False

def stop(self):
    """Stop the shaker."""
    try:
        response = requests.get(f"{self.base_url}/move?value=0", timeout=2)
        return response.status_code == 200
    except:
        return False
```

This API design provides several advantages:

1. **Simplicity** - REST-like APIs are easy to implement and debug
2. **Statelessness** - Each command is self-contained
3. **Compatibility** - Works with any controller that can handle HTTP requests
4. **Network Transparency** - Easy to route over networks and through firewalls

### Custom Event System

The application extends Qt's event system with custom events:

```python
class UpdateShakerBatteryEvent(QEvent):
    """Custom event for updating shaker battery status."""
    EVENT_TYPE = QEvent.registerEventType()

    def __init__(self, voltage):
        super().__init__(UpdateShakerBatteryEvent.EVENT_TYPE)
        self.voltage = voltage
```

These custom events are used in scenarios where direct signal connections are insufficient:

```python
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

def event(self, event):
    """Handle custom events."""
    if event.type() == UpdateShakerBatteryEvent.EVENT_TYPE:
        self.update_shaker_battery_status(event.voltage)
        return True
    return super().event(event)
```

This approach allows for thread-safe communication patterns in complex scenarios where signals and slots might introduce race conditions.

### Network Discovery Implementation

The IP finder component leverages PowerShell scripting to discover devices on the network:

```python
def run(self):
    """Main worker method to find device IP."""
    try:
        # Run PowerShell script to find devices
        script_path = os.path.join(os.path.dirname(__file__), 'computers_on_network.ps1')

        if not os.path.exists(script_path):
            self.error.emit(f"PowerShell script not found: {script_path}")
            self.finished.emit()
            return

        process = os.popen(f'powershell -ExecutionPolicy Bypass -File "{script_path}"')

        # Read output line by line to track progress
        target_found = False

        while True:
            if self.stop_requested:
                break

            line = process.readline()
            if not line:
                break

            if line.startswith('PROGRESS:'):
                # Handle progress updates
                # ...
            elif line.strip() and not line.startswith('Computername'):
                # Parse computer entries
                parts = [part for part in line.split() if part]
                if len(parts) >= 2:
                    computername = parts[0]
                    ip = parts[1]

                    if computername == self.device_name:
                        self.found_ip.emit(ip)
                        target_found = True
```

This enables automatic discovery of sensor hardware without manual IP configuration, improving user experience in complex network environments.

### Statistical Analysis Algorithms

The system uses statistical techniques to analyze sensor data quality:

```python
# Calculate delta times between consecutive samples
modified_data = []
prev_time = None
timestamps = []
deltas = []

for row in data:
    current_time = row[0]
    delta = 0.0 if prev_time is None else current_time - prev_time
    modified_data.append(list(row) + [delta])
    prev_time = current_time

    timestamps.append(current_time)
    if prev_time is not None:
        deltas.append(delta)

# Calculate median delta time
median_delta = np.median(deltas)

# Threshold for outliers (anything greater than 5% of median is an outlier)
outlier_threshold = 1.05

# Find outliers
outliers = [delta for delta in deltas if delta > (median_delta * outlier_threshold)]
```

Key statistical techniques employed:

1. **Median Calculation** - More robust to outliers than mean
2. **Threshold-Based Detection** - Uses percentages rather than fixed values
3. **Delta Time Analysis** - Focuses on inter-sample timing rather than absolute values

### UI State Management

The application implements a sophisticated state management system for UI elements:

```python
def update_ui_state(self, state):
    """Update UI elements based on the current application state."""
    if state == "idle":
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.sample_time_entry.setEnabled(True)
        self.save_path_button.setEnabled(True)
        # Enable configuration controls
        for panel in [self.sensor_panel1, self.sensor_panel2]:
            for element in panel.get_all_ui_elements():
                element.setEnabled(True)
    elif state == "collecting":
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.sample_time_entry.setEnabled(False)
        self.save_path_button.setEnabled(False)
        # Disable configuration controls during collection
        for panel in [self.sensor_panel1, self.sensor_panel2]:
            for element in panel.get_all_ui_elements():
                element.setEnabled(False)
    elif state == "completed":
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.sample_time_entry.setEnabled(True)
        self.save_path_button.setEnabled(True)
        # Re-enable configuration controls
        for panel in [self.sensor_panel1, self.sensor_panel2]:
            for element in panel.get_all_ui_elements():
                element.setEnabled(True)
```

This pattern centralizes state changes and ensures consistency across the entire interface, preventing issues like conflicting UI states during critical operations.

### Logging System

The application includes a comprehensive logging system for troubleshooting and diagnostics:

```python
def log_message(self, message, level="INFO"):
    """Log message to the log panel with timestamp and level."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Format the log entry with color based on level
    if level == "ERROR":
        formatted_msg = f"<span style='color: #f44336;'>[{timestamp}] ERROR: {message}</span>"
    elif level == "WARNING":
        formatted_msg = f"<span style='color: #ff9800;'>[{timestamp}] WARNING: {message}</span>"
    elif level == "SUCCESS":
        formatted_msg = f"<span style='color: #4caf50;'>[{timestamp}] SUCCESS: {message}</span>"
    elif level == "BATTERY":
        formatted_msg = f"<span style='color: #2196f3;'>[{timestamp}] BATTERY: {message}</span>"
    else:
        formatted_msg = f"<span style='color: #424242;'>[{timestamp}] INFO: {message}</span>"

    # Append to log and scroll to bottom
    self.log_text.append(formatted_msg)
    self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    # Also print to console for terminal-based debugging
    print(f"[{level}] {message}")
```

This multi-level logging system serves several purposes:

1. **User Feedback** - Contextual colors help users identify important messages
2. **Debugging Support** - Comprehensive logging for development and support
3. **Audit Trail** - Complete record of application activities
4. **Error Diagnosis** - Clear error messaging for troubleshooting

## Advanced Configuration and Extensibility

### Dynamic UI Creation

The application uses programmatic UI creation to maintain flexibility and extensibility:

```python
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
    # ...
```

This approach allows for:

1. **Runtime Customization** - UI elements can be modified based on configuration
2. **Maintainability** - Centralized UI creation logic
3. **Consistency** - Similar elements share creation patterns
4. **Modularity** - UI components can be easily reused and refactored

### Testing and Validation Infrastructure

The application includes built-in hardware testing functions:

```python
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
```

These testing functions provide:

1. **Pre-Collection Validation** - Verify hardware connectivity before test start
2. **Diagnostics** - Detailed error reporting for troubleshooting
3. **User Confidence** - Clear confirmation of operational hardware

## Conclusion

The EVident Battery Control Panel represents a sophisticated integration of hardware control, data acquisition, and user interface design. The modular architecture and careful attention to multithreading and error handling result in a robust application capable of reliably collecting high-precision IMU data while maintaining a responsive user experience.

Key technical highlights include:

- Scalable support for multiple simultaneous sensors
- Sophisticated data quality validation
- Automatic recovery from data collection issues
- Comprehensive error handling
- Network discovery and hardware control
- Intuitive user interface with real-time feedback
- Secure data storage and cloud integration

This application demonstrates best practices in scientific instrumentation software, combining precision data collection with an accessible user experience suitable for field testing environments.
