import socket
import time

class SensorDataCollector:
    """Class for handling sensor data collection and processing."""
    
    def __init__(self, sensor_ip, port=8888, buffer_size=65536):
        self.sensor_ip = sensor_ip
        self.port = port
        self.buffer_size = buffer_size
        self.socket = None
    
    def connect(self):
        """Establish connection to the sensor."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.settimeout(1.0)
        try:
            self.socket.connect((self.sensor_ip, self.port))
            return True
        except Exception as e:
            # Return the exception message to provide better error reporting
            return str(e)
            
    def close(self):
        """Close the sensor connection."""
        if self.socket:
            self.socket.close()
            self.socket = None
    
    def get_battery_status(self, timeout=5):
        """Get battery status from the sensor."""
        if not self.socket:
            return None
            
        data_fragment = ""
        battery_percentage = None
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                data = self.socket.recv(self.buffer_size)
                if not data:
                    break
                
                data_str = data_fragment + data.decode()
                lines = data_str.split('\n')
                data_fragment = lines[-1]
                
                for line in lines[:-1]:
                    if not line.strip():
                        continue
                    
                    if line.startswith("BATTERY:"):
                        try:
                            battery_value = float(line.replace("BATTERY:", "").replace("%", ""))
                            return battery_value
                        except:
                            continue
            except socket.timeout:
                continue
            except Exception:
                break
                
        return None
    
    def collect_data(self, calibration_time, sample_time, callback=None):
        """Collect data from sensor with calibration and sampling periods."""
        if not self.socket:
            return [], None
            
        raw_data = []
        battery_percentage = None
        data_fragment = ""
        total_time = calibration_time + sample_time
        start_time = time.time()
        in_calibration = True
        
        while time.time() - start_time < total_time:
            try:
                data = self.socket.recv(self.buffer_size)
                if not data:
                    break
                    
                data_str = data_fragment + data.decode()
                lines = data_str.split('\n')
                data_fragment = lines[-1]
                
                for line in lines[:-1]:
                    if not line.strip():
                        continue
                        
                    if line.startswith("BATTERY:") and battery_percentage is None:
                        try:
                            battery_percentage = float(line.replace("BATTERY:", "").replace("%", ""))
                        except:
                            pass
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
                
                elapsed = time.time() - start_time
                
                # Check for phase transition
                if in_calibration and elapsed > calibration_time:
                    in_calibration = False
                    if callback:
                        callback("phase_change")
                
                # Update progress
                if callback:
                    if in_calibration:
                        progress = int((elapsed/calibration_time) * 100)
                        callback("calibration_progress", progress, elapsed, calibration_time)
                    else:
                        effective_elapsed = elapsed - calibration_time
                        progress = int((effective_elapsed/sample_time) * 100)
                        callback("recording_progress", progress, effective_elapsed, sample_time)
                        
            except socket.timeout:
                continue
            except Exception:
                break
        
        # Filter data to only include samples after calibration period
        filtered_data = [sample[1] for sample in raw_data if sample[0] >= calibration_time]
        
        return filtered_data, battery_percentage