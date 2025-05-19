# This Python file uses the following encoding: utf-8
import sys
import asyncio

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import Qt, QDir, QCoreApplication
from PySide6.QtGui import QColor, QIcon
import qtinter
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from nv200.device_types import DetectedDevice, PidLoopMode
from nv200.device_discovery import discover_devices
from nv200.device_interface import DeviceClient, create_device_client
from nv200.data_recorder import DataRecorder, DataRecorderSource, RecorderAutoStartMode
from qt_material import apply_stylesheet
from pathlib import Path


# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_mainwindow import Ui_MainWindow


class MainWindow(QMainWindow):
    """
    Main application window for the PySoWorks UI, providing asynchronous device discovery, connection, and control features.
    Attributes:
        _device (DeviceClient): The currently connected device client, or None if not connected.
        _recorder (DataRecorder): The data recorder associated with the connected device, or None if not initialized
    """

    _device: DeviceClient = None
    _recorder : DataRecorder = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        ui = self.ui
        ui.setupUi(self)
        ui.searchDevicesButton.clicked.connect(qtinter.asyncslot(self.search_devices))
        ui.devicesComboBox.currentIndexChanged.connect(self.on_device_selected)
        ui.connectButton.clicked.connect(qtinter.asyncslot(self.connect_to_device))
        ui.moveButton.clicked.connect(qtinter.asyncslot(self.start_move))
        ui.openLoopButton.clicked.connect(qtinter.asyncslot(self.on_pid_mode_button_clicked))
        ui.closedLoopButton.clicked.connect(qtinter.asyncslot(self.on_pid_mode_button_clicked))
        ui.moveProgressBar.set_duration(5000)
        ui.moveProgressBar.set_update_interval(20)
        self.setWindowTitle("PySoWorks")


    async def search_devices(self):
        """
        Asynchronously searches for available devices and updates the UI accordingly.
        """
        self.ui.searchDevicesButton.setEnabled(False)
        self.ui.connectButton.setEnabled(False)
        self.ui.easyModeGroupBox.setEnabled(False)
        self.ui.statusbar.showMessage("Searching for devices...")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        if self._device is not None:
            await self._device.close()
            self._device = None
        
        print("Searching...")
        try:
            print("Discovering devices...")
            devices = await discover_devices(full_info=True)    
            
            if not devices:
                print("No devices found.")
            else:
                print(f"Found {len(devices)} device(s):")
                for device in devices:
                    print(device)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            QApplication.restoreOverrideCursor()
            self.ui.searchDevicesButton.setEnabled(True)
            self.ui.statusbar.clearMessage()
            print("Search completed.")
            self.ui.devicesComboBox.clear()
            if devices:
                for device in devices:
                    self.ui.devicesComboBox.addItem(f"{device}", device)
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


    async def on_pid_mode_button_clicked(self):
        """
        Handles the event when the PID mode button is clicked.

        Determines the desired PID loop mode (closed or open loop) based on the state of the UI button,
        sends the mode to the device asynchronously, and updates the UI status bar with any errors encountered.
        """
        ui = self.ui
        pid_mode = PidLoopMode.CLOSED_LOOP if ui.closedLoopButton.isChecked() else PidLoopMode.OPEN_LOOP
        try:
            await self._device.set_pid_mode(pid_mode)
            print(f"PID mode set to {pid_mode}.")
        except Exception as e:
            print(f"Error setting PID mode: {e}")
            self.ui.statusbar.showMessage(f"Error setting PID mode: {e}", 2000)
            return


    def selected_device(self) -> DetectedDevice:
        """
        Returns the currently selected device from the devicesComboBox.
        """
        index = self.ui.devicesComboBox.currentIndex()
        if index == -1:
            return None
        return self.ui.devicesComboBox.itemData(index, role=Qt.UserRole)
    

    async def initialize_easy_mode_ui(self):
        """
        Asynchronously initializes the UI elements for easy mode UI.
        """
        dev = self._device
        ui = self.ui
        ui.targetPosSpinBox.setValue(await dev.get_setpoint())
        pid_mode = await dev.get_pid_mode()
        if pid_mode == PidLoopMode.OPEN_LOOP:
            ui.openLoopButton.setChecked(True)
        else:
            ui.closedLoopButton.setChecked(True)


    async def disconnect_from_device(self):
        """
        Asynchronously disconnects from the currently connected device.
        """
        if self._device is None:
            print("No device connected.")
            return

        await self._device.close()
        self._device = None       
        self._recorder = None
            


    async def connect_to_device(self):
        """
        Asynchronously connects to the selected device.
        """
        detected_device = self.selected_device()
        self.ui.statusbar.showMessage(f"Connecting to {detected_device.identifier}...", 2000)
        print(f"Connecting to {detected_device.identifier}...")
        try:
            await self.disconnect_from_device()
            self._device = create_device_client(detected_device)
            await self._device.connect()
            self.ui.easyModeGroupBox.setEnabled(True)
            await self.initialize_easy_mode_ui()
            self.ui.statusbar.showMessage(f"Connected to {detected_device.identifier}.", 2000)
            print(f"Connected to {detected_device.identifier}.")
        except Exception as e:
            self.ui.statusbar.showMessage(f"Connection failed: {e}", 2000)
            print(f"Connection failed: {e}")
            return


    def recorder(self) -> DataRecorder:
        """
        Returns the DataRecorder instance associated with the device.
        """
        if self._device is None:
            return None

        if self._recorder is None:
            self._recorder = DataRecorder(self._device)
        return self._recorder	


    async def start_move(self):
        """
        Asynchronously starts the move operation.
        """
        if self._device is None:
            print("No device connected.")
            return
        
        ui = self.ui
        ui.moveButton.setEnabled(False)
        ui.moveProgressBar.start()
        try:
            recorder = self.recorder()
            await recorder.set_data_source(0, DataRecorderSource.PIEZO_POSITION)
            await recorder.set_data_source(1, DataRecorderSource.PIEZO_VOLTAGE)
            await recorder.set_autostart_mode(RecorderAutoStartMode.START_ON_SET_COMMAND)
            await recorder.set_recording_duration_ms(120)
            await recorder.start_recording()

            # Implement the move logic here
            # For example, you might want to send a command to the device to start moving.
            # await self._device.start_move()
            print("Starting move operation...")
            await self._device.move(ui.targetPosSpinBox.value())
            ui.statusbar.showMessage("Move operation started.")
            await recorder.wait_until_finished()
            ui.statusbar.showMessage("Reading recorded data from device...")
            rec_data = await recorder.read_recorded_data_of_channel(0)
            ui.mplCanvasWidget.canvas.plot_data(rec_data, QColor(0, 255, 0))
            rec_data = await recorder.read_recorded_data_of_channel(1)
            ui.mplCanvasWidget.canvas.add_line(rec_data,  QColor('orange'))
            ui.moveProgressBar.stop(success=True)
        except Exception as e:
            ui.statusbar.showMessage(f"Error during move operation: {e}", 4000)
            ui.moveProgressBar.reset()
            print(f"Error during move operation: {e}")
            return
        finally:
            ui.moveButton.setEnabled(True)
            ui.statusbar.clearMessage()

            

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('fusion')
    app_path = Path(__file__).resolve().parent
    app.setWindowIcon(QIcon(str(app_path) + '/app_icon.ico'))
    apply_stylesheet(app, theme='dark_teal.xml')
    widget = MainWindow()
    widget.show()
    #sys.exit(app.exec())
    with qtinter.using_asyncio_from_qt():
        app.exec()
