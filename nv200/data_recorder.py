"""
This module provides access to the NV200 data recorder functionality.
"""
from nv200.device_interface import DeviceClient
import math
from typing import List
from enum import Enum
from collections import namedtuple


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
        """
        Return a string representation of the DataRecorderSource enum member for debugging.
        """
        return f"DataRecorderSource({self.name})"
    
    def __str__(self):
        """
        Return a human-readable string for the DataRecorderSource enum member.

        This method is used to provide a more user-friendly string representation for display,
        such as in a user interface or logs.
        """
        # Dictionary mapping enum names to human-readable strings
        human_readable = {
            "PIEZO_POSITION": "Piezo Position (μm or mrad)",
            "SETPOINT": "Setpoint (μm or mrad)",
            "PIEZO_VOLTAGE": "Piezo Voltage (V)",
            "POSITION_ERROR": "Position Error",
            "ABS_POSITION_ERROR": "Absolute Position Error",
            "PIEZO_CURRENT_1": "Piezo Current 1 (A)",
            "PIEZO_CURRENT_2": "Piezo Current 2 (A)"
        }
        return human_readable.get(self.name, self.name)  # Default to the enum name if not found
    

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
    BUFFER_READ_TIMEOUT_SECS = 6  # Timeout for reading data from the recorder buffer - it needs to be higher because it may take some time
    ALL_CHANNELS = -1  # Number of data recorder channels
    RecorderParam = namedtuple('RecorderParam', ['bufsize', 'stride', 'sample_freq'])
    ChannelRecordingData = namedtuple('ChannelRecordingData', ['source', 'data'])
    _dev : DeviceClient

    def __init__(self, device: DeviceClient):
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

    async def set_recording_duration_ms(self, milliseconds: float) -> RecorderParam:
        """
        Sets the recording duration in milliseconds and adjusts the recorder parameters accordingly.

        This method calculates the appropriate stride, sample rate, and buffer size based on the 
        specified recording duration and the recorder's configuration. It then updates the recorder 
        settings to match these calculated values.

        Args:
            milliseconds (float): The desired recording duration in milliseconds.

        Returns:
            RecorderParam: An object containing the updated buffer length, stride, and sample rate.

        Raises:
            ValueError: If the calculated buffer size or stride is invalid.
        """
        duration_s = milliseconds / 1000.0
        buffer_duration_s = 1 / self.NV200_RECORDER_SAMPLE_RATE_HZ * self.NV200_RECORDER_BUFFER_SIZE
        stride = int(duration_s / buffer_duration_s) + 1
        sample_rate = self.NV200_RECORDER_SAMPLE_RATE_HZ / stride
        buflen = math.ceil(sample_rate * duration_s)
        buflen = min(buflen, self.NV200_RECORDER_BUFFER_SIZE)
        await self.set_recorder_stride(stride)
        await self.set_sample_buffer_size(buflen)
        return self.RecorderParam(buflen, stride, sample_rate)

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

    async def read_recorded_data_of_channel(self, channel : int) -> ChannelRecordingData:
        """
        Asynchronously reads recorded data from a specified channel.

        Args:
            channel (int): The channel number from which to read the recorded data.

        Returns:
            ChannelRecordingData: An object containing the recording source as a string 
            and a list of floating-point numbers representing the recorded data.

        Raises:
            Any exceptions raised by the underlying device communication methods.
        """
        recsrc = DataRecorderSource(await self._dev.read_int_value(f"recsrc,{channel}"))
        number_strings = await self._dev.read_values(f'recoutf,{channel}', self.BUFFER_READ_TIMEOUT_SECS)
        return self.ChannelRecordingData(str(recsrc), [float(num) for num in number_strings])
    
    async def read_recorded_data(self) -> List[ChannelRecordingData]:
        """
        Asynchronously reads recorded data for two channels and returns it as a list.

        This method retrieves the recorded data for channel 0 and channel 1 by 
        calling `read_recorded_data_of_channel` for each channel. The results are 
        returned as a list of `ChannelRecordingData` objects.

        Returns:
            List[ChannelRecordingData]: A list containing the recorded data for 
            channel 0 and channel 1.
        """
        chan_data0 = await self.read_recorded_data_of_channel(0)
        chan_data1 = await self.read_recorded_data_of_channel(1)
        return [chan_data0, chan_data1]

