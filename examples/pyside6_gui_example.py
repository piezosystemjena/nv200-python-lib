import sys
import asyncio
from typing import List, Dict
from nv200.lantronix_xport import discover_lantronix_devices_async

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit)

#import PySide6.QtAsyncio as QtAsyncio
import qtinter
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.figure import Figure


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super().__init__(fig)



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Lantronix Discovery")
        self.resize(400, 300)

        self.button = QPushButton("Discover Devices")
        self.output = QTextEdit()
        self.output.setReadOnly(True)

        self.button.clicked.connect(qtinter.asyncslot(self.start_discovery))

        # Create the matplotlib FigureCanvas object,
        # which defines a single set of axes as self.axes.
        self.sc = MplCanvas(self)
        self.sc.axes.plot([0,1,2,3,4], [10,1,20,3,40])

        layout = QVBoxLayout()
        layout.addWidget(self.button)
        layout.addWidget(self.output)
        layout.addWidget(self.sc)
        self.setLayout(layout)

    async def start_discovery(self):
        self.output.clear()
        self.output.append("Starting discovery...")
        try:
            devices = await discover_lantronix_devices_async()
            if devices:
                for d in devices:
                    self.output.append(f"Found: {d['MAC']} @ {d['IP']}")
            else:
                self.output.append("No devices found.")
        except Exception as e:
            self.output.append(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('windowsvista')
    main_window = MainWindow()
    main_window.show()
    with qtinter.using_asyncio_from_qt():
        app.exec()

    #QtAsyncio.run(handle_sigint=True)
