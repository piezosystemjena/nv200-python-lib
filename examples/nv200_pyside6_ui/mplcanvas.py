from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from PySide6.QtGui import QPalette, QColor, QIcon
from PySide6.QtWidgets import QVBoxLayout, QWidget, QApplication
from nv200.data_recorder import DataRecorder


class MplCanvas(FigureCanvas):
    '''
    Class to represent the FigureCanvas widget
    '''
    _fig: Figure = None

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        plt.style.use('dark_background')
        self._fig = Figure(figsize=(width, height), dpi=dpi)
        self._fig.tight_layout()
        self.axes = self._fig.add_subplot(111)
        self._fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.axes.set_xlabel('Time (ms)')
        self.axes.set_ylabel('Value (ms)')
        self.axes.grid(True, color='darkgray', linestyle='--', linewidth=0.5)
        ax = self.axes
        ax.spines['top'].set_color('darkgray')
        ax.spines['right'].set_color('darkgray')
        ax.spines['bottom'].set_color('darkgray')
        ax.spines['left'].set_color('darkgray')

        # Set tick parameters for dark grey color
        ax.tick_params(axis='x', colors='darkgray')
        ax.tick_params(axis='y', colors='darkgray')

        palette = QApplication.palette()
        bg_color = palette.color(QPalette.Window)
        #self.axes.set_facecolor(bg_color.name())
        #self._fig.set_facecolor(bg_color.name())
        super().__init__(self._fig)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fig.tight_layout()
        self.draw()


    def plot_data(self, rec_data : DataRecorder.ChannelRecordingData, color : QColor = QColor('orange')):
        """Plots the data and stores the line object for later removal."""
        self.remove_all_lines()  # Remove all previous lines before plotting new data
        self.add_line(rec_data, color)  # Add the new line to the plot


    def add_line(self, rec_data : DataRecorder.ChannelRecordingData, color : QColor = QColor('orange')):
        """
        Adds a new line plot to the canvas using the provided channel recording data.
        """
        # Plot the data and add a label for the legend
        ax = self.axes
        ax.plot(
            rec_data.sample_times_ms, rec_data.values, 
            linestyle='-', color=color.name(), label=rec_data.source
        )

        # Autoscale the axes after plotting the data
        ax.relim()
        ax.autoscale_view()
        
        # Show the legend with custom styling
        ax.legend(
            facecolor='darkgray', 
            edgecolor='darkgray', 
            frameon=True, 
            loc='best', 
            fontsize=10
        )

        # Redraw the canvas
        self.draw()


    def remove_all_lines(self):
        """Removes all lines from the axes."""
        # Iterate over all lines in the axes and remove them
        for line in self.axes.get_lines():
            line.remove()

        # Redraw the canvas to reflect the change
        self.draw()



class LightIconToolbar(NavigationToolbar2QT):
    def __init__(self, canvas, parent):
        super().__init__(canvas, parent)

        # Define a mapping from action name to your custom icon file
        icon_paths = {
            'home': '/path/to/light-theme-icons/home.png',
            'back': '/path/to/light-theme-icons/back.png',
            'forward': '/path/to/light-theme-icons/forward.png',
            'pan': '/path/to/light-theme-icons/pan.png',
            'zoom': '/path/to/light-theme-icons/zoom.png',
            'filesave': '/path/to/light-theme-icons/save.png',
            'subplots': '/path/to/light-theme-icons/subplots.png',  # Optional if subplot config is shown
        }

        # Replace icons if paths are valid
        for action_name, icon_path in icon_paths.items():
            action = self._actions.get(action_name)
            print(f"Action: {action_name}, Icon Path: {icon_path}")
            if action:
                action.setIcon(QIcon())




class MplWidget(QWidget):
    '''
    Widget promoted and defined in Qt Designer
    '''
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.canvas = MplCanvas()
        # Create the navigation toolbar linked to the canvas
        self.toolbar = LightIconToolbar(self.canvas, self)
        self.vbl = QVBoxLayout()
        self.vbl.addWidget(self.toolbar)
        self.vbl.addWidget(self.canvas)
        self.vbl.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.vbl)
        self.setContentsMargins(0, 0, 0, 0)


    
