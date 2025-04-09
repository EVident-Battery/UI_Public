import numpy as np
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime
import os
import threading
from sensor_data_collector import SensorDataCollector
import csv

class DataCollectionWorker(QObject):
    """Worker thread for data collection from sensors."""
    
    # Define signals
    progress = pyqtSignal(str, int)
    sensor_progress = pyqtSignal(int, str, int)  # sensor_id, message, progress_value
    battery_update = pyqtSignal(int, float)      # sensor_id, battery_percentage
    error = pyqtSignal(str)
    sensor_error = pyqtSignal(int, str)          # sensor_id, error_message
    finished = pyqtSignal()
    data_saved = pyqtSignal(int, str)            # sensor_id, filename
    need_redo = pyqtSignal()                     # Signal to trigger automatic redo
    outliers_detected = pyqtSignal(int, float, float)  # New signal: Sensor ID, median value, max outlier
    
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.stop_requested = False
        self.sensor_data = {1: None, 2: None}
        self.battery_values = {1: None, 2: None}
        self.filenames = {1: None, 2: None}
        self.error_occurred = False
        self.timing_issue_detected = False
        self.outlier_detected = False  # New flag to track outlier detection
    
    def run(self):
        """Main worker method to collect data from sensors."""
        try:
            # Generate timestamp and base filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Use the test ID from config
            test_id = self.config['test_id']
            
            base_filename = (f"{self.config['vin']}_{self.config['car_model'].replace(' ', '_')}_"
                            f"{self.config['year']}_{self.config['mileage']}_"
                            f"{self.config['trim'].replace(' ', '_')}_{self.config['soc']}_"
                            f"{self.config['file_prefix']}_{self.config['test_number']:03d}_"
                            f"{test_id}_{timestamp}")
            
            # Create save directory if it doesn't exist
            if self.config['save_path']:
                os.makedirs(self.config['save_path'], exist_ok=True)
            
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
            
            # Wait for all threads to complete or until stop is requested
            for thread in threads:
                while thread.is_alive():
                    thread.join(0.1)  # Join with timeout to check stop_requested
                    if self.stop_requested:
                        self.error.emit("Data collection aborted by user")
                        self.error_occurred = True
                        break
                if self.stop_requested:
                    break
            
            # Check if we have data from all expected sensors
            if self.config['dual_sensor_mode']:
                expected_sensors = 2
            else:
                expected_sensors = 1
                
            active_sensors = sum(1 for data in self.sensor_data.values() if data is not None)
            
            if self.stop_requested:
                self.progress.emit("Data collection aborted", 100)
            elif active_sensors < expected_sensors:
                self.error.emit("Data collection failed for one or more sensors")
                self.error_occurred = True
            else:
                self.progress.emit("Data collection complete", 100)
                
            self.finished.emit()
            
            # Process collected data
            if not self.stop_requested and active_sensors == expected_sensors:
                self.process_collected_data()
            
        except Exception as e:
            self.error.emit(f"Error in data collection: {str(e)}")
            self.error_occurred = True
            self.finished.emit()
    
    def process_collected_data(self):
        """Process the collected data and check for timing issues."""
        try:
            # Check for timing issues in each sensor's data
            for sensor_id, data in self.sensor_data.items():
                if data is None or len(data) < 2:
                    continue
                    
                # Calculate delta times between consecutive samples
                timestamps = [row[0] for row in data]
                deltas = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
                
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
                    
            # If outliers were detected in any sensor, signal for a redo
            if self.outlier_detected:
                self.need_redo.emit()
                
        except Exception as e:
            self.error.emit(f"Error analyzing data: {str(e)}")
            self.error_occurred = True
    
    def collect_from_sensor(self, sensor_id, sensor_ip, base_filename):
        """Collect data from a specific sensor."""
        try:
            self.sensor_progress.emit(sensor_id, f"Connecting to sensor {sensor_id}", 0)
            
            # Initialize sensor collector
            collector = SensorDataCollector(sensor_ip)
            
            # Connect to sensor
            connection_result = collector.connect()
            
            # Check if connection result is a string (error message) or True (success)
            if connection_result is not True:
                error_msg = f"Failed to connect to sensor {sensor_id}: {connection_result}"
                self.sensor_error.emit(sensor_id, error_msg)
                self.error_occurred = True  # Mark that an error occurred
                return
                
            self.sensor_progress.emit(sensor_id, f"Getting battery status for sensor {sensor_id}", 5)
            
            # Get battery status
            battery = collector.get_battery_status()
            if battery is not None:
                #keep battery between 0 and 100%
                battery = max(0, min(battery, 100))
                self.battery_update.emit(sensor_id, battery)
            
            self.sensor_progress.emit(sensor_id, f"Starting data collection for sensor {sensor_id}", 10)
            
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
            
            # Collect data
            data, battery_update = collector.collect_data(
                self.config['calibration_time'],
                self.config['sample_time'],
                progress_callback
            )
            
            # Close connection
            collector.close()
            
            if not data:
                self.sensor_error.emit(sensor_id, f"No data collected from sensor {sensor_id}")
                self.error_occurred = True  # Mark that an error occurred
                return
                
            # Update battery if we got a newer value
            if battery_update is not None:
                self.battery_update.emit(sensor_id, battery_update)
                self.battery_values[sensor_id] = battery_update
            
            # Save the data
            filename = self.save_sensor_data(data, sensor_id, base_filename)
            if filename:
                self.filenames[sensor_id] = filename
                self.data_saved.emit(sensor_id, filename)
            
            # Store the data
            self.sensor_data[sensor_id] = data
            
            self.sensor_progress.emit(
                sensor_id,
                f"Sensor {sensor_id} data collection complete",
                100
            )
            
        except Exception as e:
            self.sensor_error.emit(sensor_id, f"Error collecting data from sensor {sensor_id}: {str(e)}")
            self.error_occurred = True  # Mark that an error occurred
    
    def save_sensor_data(self, data, sensor_id, base_filename):
        """Save sensor data to CSV file and analyze for timing issues."""
        try:
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
            
            # Create filename
            if self.config['save_path']:
                filename = os.path.join(self.config['save_path'], f"{base_filename}_sensor{sensor_id}.csv")
            else:
                filename = f"{base_filename}_sensor{sensor_id}.csv"
            
            # Save to CSV
            with open(filename, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Time", "Accel_X", "Accel_Y", "Accel_Z", "Gyro_X", "Gyro_Y", "Gyro_Z", "Delta_Time"])
                writer.writerows(modified_data)
            
            # Check for outliers if we have enough data
            if len(deltas) > 1:
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
            
            return filename
                
        except Exception as e:
            self.sensor_error.emit(sensor_id, f"Error saving data for sensor {sensor_id}: {str(e)}")
            self.error_occurred = True  # Mark that an error occurred
            return None