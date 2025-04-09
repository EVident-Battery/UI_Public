from PyQt5.QtCore import QEvent

class UpdateShakerBatteryEvent(QEvent):
    """Custom event for updating shaker battery status."""
    EVENT_TYPE = QEvent.registerEventType()
    
    def __init__(self, voltage):
        super().__init__(UpdateShakerBatteryEvent.EVENT_TYPE)
        self.voltage = voltage
