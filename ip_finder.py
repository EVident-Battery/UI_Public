import os
from PyQt5.QtCore import QObject, pyqtSignal

class IPFinder(QObject):
    """Class for finding IP addresses of connected devices."""
    
    # Define signals
    progress = pyqtSignal(str, int)  # message, progress_value
    found_ip = pyqtSignal(str)       # ip_address
    error = pyqtSignal(str)          # error_message
    finished = pyqtSignal()
    
    def __init__(self, device_name):
        super().__init__()
        self.device_name = device_name
        self.stop_requested = False
    
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
                    elif progress_info.startswith('ARP:'):
                        try:
                            current, total = map(int, progress_info.split(':')[1].split('/'))
                            progress = int((current / total) * 100)
                            self.progress.emit(f"Step 2/2: Scanning ARP entries: {current}/{total}", progress)
                        except:
                            pass
                elif line.strip() and not line.startswith('Computername'):
                    # Parse computer entries
                    parts = [part for part in line.split() if part]
                    if len(parts) >= 2:
                        computername = parts[0]
                        ip = parts[1]
                        
                        if computername == self.device_name:
                            self.found_ip.emit(ip)
                            target_found = True
            
            if not target_found:
                self.error.emit(f"Could not find {self.device_name} on the network")
                
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(f"Error finding IP: {str(e)}")
            self.finished.emit()
    
    def stop(self):
        """Stop the IP finder."""
        self.stop_requested = True
