import sys
from PyQt5.QtWidgets import QApplication, QDialog
from license_dialog import LicenseDialog
from evident_app import EVidentApp

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

if __name__ == '__main__':
    main() 