# This Python file uses the following encoding: utf-8
import sys


from PySide6.QtWidgets import QApplication, QMainWindow
import qtinter
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure
from nv200.lantronix_xport import discover_lantronix_devices_async


# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_mainwindow import Ui_MainWindow



class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.searchDevicesButton.clicked.connect(qtinter.asyncslot(self.search_devices))

    async def search_devices(self):
        self.ui.statusbar.showMessage("Searching for devices...", 2000)
        # Simulate search logic
        print("Searching...")
        try:
            devices = await discover_lantronix_devices_async()
            if devices:
                for d in devices:
                    print(f"Found: {d['MAC']} @ {d['IP']}")
            else:
                print("No devices found.")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    #sys.exit(app.exec())
    with qtinter.using_asyncio_from_qt():
        app.exec()
