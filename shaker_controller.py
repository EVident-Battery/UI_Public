import requests

class ShakerController:
    """Class to handle communication with the shaker controller."""
    
    def __init__(self, base_url="http://10.1.10.195"):
        self.base_url = base_url
    
    # TODO: Add a function to check if the shaker is connected (ping)
    def ping(self):
        """Ping the shaker controller."""
        try:
            response = requests.get(f"{self.base_url}", timeout=2)
            return response.status_code == 404
        except Exception as e:
            return False
    
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
    
    def home(self):
        """Return the shaker to home position."""
        try:
            response = requests.get(f"{self.base_url}/reset", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def calibrate(self):
        """Calibrate the shaker."""
        try:
            # Use a longer timeout for calibration (10 seconds)
            response = requests.get(f"{self.base_url}/calibrate", timeout=10)
            return response.status_code == 200
        except Exception as e:
            return False
    
    def set_home(self):
        """Set the current position as home."""
        try:
            response = requests.get(f"{self.base_url}/set_home", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def auto_raise(self):
        """Start the auto raise function."""
        try:
            response = requests.get(f"{self.base_url}/start", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def lower(self, active=True):
        """Activate or deactivate the lower function."""
        try:
            value = "true" if active else "false"
            response = requests.get(f"{self.base_url}/lower?value={value}", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def get_battery_voltage(self):
        """Get the battery voltage of the shaker controller."""
        try:
            response = requests.get(f"{self.base_url}/voltage", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get("voltage")
            return None
        except:
            return None 