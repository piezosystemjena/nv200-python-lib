# This Python file uses the following encoding: utf-8
import sys


from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt
import qtinter
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from nv200.device_types import DetectedDevice
from nv200.device_discovery import discover_devices
from nv200.device_interface import DeviceClient, create_device_client


# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_mainwindow import Ui_MainWindow



class MainWindow(QMainWindow):

    _device: DeviceClient = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.searchDevicesButton.clicked.connect(qtinter.asyncslot(self.search_devices))
        self.ui.devicesComboBox.currentIndexChanged.connect(self.on_device_selected)
        self.ui.connectButton.clicked.connect(qtinter.asyncslot(self.connect_to_device))

    async def search_devices(self):
        """
        Asynchronously searches for available devices and updates the UI accordingly.
        """
        self.ui.searchDevicesButton.setEnabled(False)
        self.ui.connectButton.setEnabled(False)
        self.ui.statusbar.showMessage("Searching for devices...", 2000)
        print("Searching...")
        try:
            print("Discovering devices...")
            devices = await discover_devices()
            
            if not devices:
                print("No devices found.")
            else:
                print(f"Found {len(devices)} device(s):")
                for device in devices:
                    print(device)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.ui.searchDevicesButton.setEnabled(True)
            self.ui.statusbar.showMessage("Search completed.", 2000)
            print("Search completed.")
            self.ui.devicesComboBox.clear()
            if devices:
                for device in devices:
                    self.ui.devicesComboBox.addItem(f"{device.transport} @ {device.identifier}", device)
            else:
                self.ui.devicesComboBox.addItem("No devices found.")
            
    def on_device_selected(self, index):
        """
        Handles the event when a device is selected from the devicesComboBox.
        """
        if index == -1:
            print("No device selected.")
            return

        device = self.ui.devicesComboBox.itemData(index, role=Qt.UserRole)
        if device is None:
            print("No device data found.")
            return
        
        print(f"Selected device: {device}")
        self.ui.connectButton.setEnabled(True)


    def selected_device(self) -> DetectedDevice:
        """
        Returns the currently selected device from the devicesComboBox.
        """
        index = self.ui.devicesComboBox.currentIndex()
        if index == -1:
            return None
        return self.ui.devicesComboBox.itemData(index, role=Qt.UserRole)


    async def connect_to_device(self):
        """
        Asynchronously connects to the selected device.
        """
        detected_device = self.selected_device()
        self.ui.statusbar.showMessage(f"Connecting to {detected_device.identifier}...", 2000)
        print(f"Connecting to {detected_device.identifier}...")
        self._device = create_device_client(detected_device)
        try:
            await self._device.connect()
        except Exception as e:
            self.ui.statusbar.showMessage(f"Connection failed: {e}", 2000)
            print(f"Connection failed: {e}")
            return

        # Implement the connection logic here
        # For example, you might want to use the device's transport and identifier
        # to establish a connection.
        # await device.connect()
        self.ui.statusbar.showMessage(f"Connected to {detected_device.identifier}.", 2000)
        print(f"Connected to {detected_device.identifier}.")
            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    widget = MainWindow()
    widget.show()
    #sys.exit(app.exec())
    with qtinter.using_asyncio_from_qt():
        app.exec()
