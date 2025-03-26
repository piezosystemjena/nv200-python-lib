import nv200_driver	
from enum import Enum


class DataRecorderSource(Enum):
    """
    Enum representing the source of data to be stored in the data recorder channel,
    ignoring the buffer (A or B) distinction.
    """
    PIEZO_POSITION = 0  # Piezo position (μm or mrad)
    SETPOINT = 1        # Setpoint (μm or mrad)
    PIEZO_VOLTAGE = 2   # Piezo voltage (V)
    POSITION_ERROR = 3  # Position error
    ABS_POSITION_ERROR = 4  # Absolute position error
    PIEZO_CURRENT_1 = 6  # Piezo current 1 (A)
    PIEZO_CURRENT_2 = 7  # Piezo current 2 (A)

    def __init__(self, src: int):
        self.src = src

    @classmethod
    def get_source(cls, value: int) -> 'DataRecorderSource':
        """
        Given a source value, return the corresponding RecSrc enum.
        """
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Invalid recsrc value: {value}")

    def __repr__(self):
        return f"RecSrc(SRC{self.src})"
    

class RecorderAutoStartMode(Enum):
    """
    Enum representing the autostart mode of the data recorder.
    """
    OFF = 0               # Autostart off
    START_ON_SET_COMMAND = 1  # Start on set-command
    START_ON_GRUN_COMMAND = 2  # Start on grun-command

    def __init__(self, mode: int):
        self.mode = mode

    @classmethod
    def get_mode(cls, value: int) -> 'Recast':
        """
        Given a mode value, return the corresponding Recast enum.
        """
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Invalid recast value: {value}")

    def __repr__(self):
        return f"Recast(MODE{self.mode})"
    

class DataRecorder:
    NV200_RECORDER_SAMPLE_RATE_HZ = 20000  # Sample frequency of the NV200 data recorder in Hz
    NV200_RECORDER_BUFFER_SIZE = 6144  # Size of a single NV200 data recorder buffer
    """
    Data recorder class provides an interface for NV200 data recorder.
    The data recorder consists of two memory banks that are written to in parallel. 
    In this way, two individual signals can be stored synchronously.
    """
    def __init__(self, device: nv200_driver.DeviceClient):
        self._dev = device


    async def set_data_source(self, channel: int, source: DataRecorderSource):
        """
        Sets the channel and the source of data to be stored in the data recorder channel.
        """
        await self._dev.write(f"recsrc,{channel},{source.value}")


    async def set_autostart_mode(self, mode: RecorderAutoStartMode):
        """
        Sets the autostart mode of the data recorder.
        """
        await self._dev.write(f"recast,{mode.value}")

    async def set_recorder_stride(self, stride: int):
        """
        Sets the recorder stride.
        """
        await self._dev.write(f"recstr,{stride}")

    async def set_recording_duration(self, milliseconds: float):
        duration_s = milliseconds / 1000.0
        buffer_duration_s = 1 / self.NV200_RECORDER_SAMPLE_RATE_HZ * self.NV200_RECORDER_BUFFER_SIZE
        print(f"Buffer duration: {buffer_duration_s}")
        stride = int(duration_s / buffer_duration_s) + 1
        print(f"Setting stride to {stride}")

    async def start_recording(self, start : bool = True):
        """
        Starts / stops the data recorder.
        """
        await self._dev.write(f"recrun,{int(start)}")

    async def read_recorded_data(self, channel : int) -> list[float]:
        """
        Reads the recorded data from the data recorder.
        """
        number_strings = await self._dev.read_values(f'recoutf,{channel}')
        return [float(num) for num in number_strings]
