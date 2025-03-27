import nv200_driver	
import math
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
    """
    Data recorder class provides an interface for NV200 data recorder.
    The data recorder consists of two memory banks that are written to in parallel. 
    In this way, two individual signals can be stored synchronously.
    """
    NV200_RECORDER_SAMPLE_RATE_HZ = 20000  # Sample frequency of the NV200 data recorder in Hz
    NV200_RECORDER_BUFFER_SIZE = 6144  # Size of a single NV200 data recorder buffer
    INFINITE_RECORDING_DURATION = 0  # Infinite recording duration
    BUFFER_READ_TIMEOUT_SECS = 4  # Timeout for reading data from the recorder buffer - it needs to be higher because it may take some time

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

    async def set_sample_buffer_size(self, buffer_size: int):
        """
        Sets the sample buffer size for each of the two data recorder channels (0..6144)
        A value of 0 means infinite loop over maximum length until recorder is stopped manually.
        If you would like to have an infinite loop, use the constant `INFINITE_RECORDING_DURATION`.
        """
        if not 1 <= buffer_size <= self.NV200_RECORDER_BUFFER_SIZE:
            raise ValueError(f"buffer_size must be between 0 and {self.NV200_RECORDER_BUFFER_SIZE}, got {buffer_size}")
        await self._dev.write(f"reclen,{buffer_size}")

    async def set_recording_duration_ms(self, milliseconds: float):
        """
        Sets the recording duration in milliseconds.

        This method calculates the appropriate stride and buffer length based on the 
        desired recording duration and the recorder's sample rate and buffer size. 
        It then configures the recorder with these calculated values.

        Args:
            milliseconds (float): The desired recording duration in milliseconds.

        Raises:
            ValueError: If the calculated buffer length exceeds the maximum buffer size.

        Notes:
            - The stride determines how often the recorder processes data.
            - The buffer length is the number of samples to store for the given duration.
            - The method ensures the buffer length does not exceed the recorder's maximum buffer size.
        """
        duration_s = milliseconds / 1000.0
        buffer_duration_s = 1 / self.NV200_RECORDER_SAMPLE_RATE_HZ * self.NV200_RECORDER_BUFFER_SIZE
        stride = int(duration_s / buffer_duration_s) + 1
        sample_rate = self.NV200_RECORDER_SAMPLE_RATE_HZ / stride
        buflen = math.ceil(sample_rate * duration_s)
        buflen = min(buflen, self.NV200_RECORDER_BUFFER_SIZE)
        await self.set_recorder_stride(stride)
        await self.set_sample_buffer_size(buflen)

    async def start_recording(self, start : bool = True):
        """
        Starts / stops the data recorder.
        """
        await self._dev.write(f"recrun,{int(start)}")

    async def stop_recording(self):
        """
        Stops the recording process by invoking the `start_recording` method with `False`.
        """
        await self.start_recording(False)

    async def read_recorded_data(self, channel : int) -> list[float]:
        """
        Reads the recorded data from the data recorder.
        """
        number_strings = await self._dev.read_values(f'recoutf,{channel}', self.BUFFER_READ_TIMEOUT_SECS)
        return [float(num) for num in number_strings]
