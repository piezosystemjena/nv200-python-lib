"""
This module provides access to the NV200 data recorder functionality.
"""
import logging
from nv200.nv200_device import NV200Device
from nv200.utils import TimeSeries, wait_until
import math
from typing import List
from enum import Enum
from collections import namedtuple
from nv200._internal._reentrant_lock import _ReentrantAsyncLock


# Global module locker
logger = logging.getLogger(__name__)


class DataRecorderSource(Enum):
    """
    Enum representing the source of data to be stored in the data recorder channel,
    ignoring the buffer (A or B) distinction.

    """
    PIEZO_POSITION = 0 
    "Piezo position (μm or mrad)"

    SETPOINT = 1        
    "Setpoint (μm or mrad)"

    PIEZO_VOLTAGE = 2
    "Piezo voltage (V)"

    POSITION_ERROR = 3
    "Position error"

    ABS_POSITION_ERROR = 4
    "Absolute position error"

    PIEZO_CURRENT_1 = 6
    "Piezo current 1 (A)"

    PIEZO_CURRENT_2 = 7
    "Piezo current 2 (A)"

    @classmethod
    def from_value(cls, value : int):
        if value in cls._value2member_map_:
            return cls(value)
        else:
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
            DataRecorderSource.PIEZO_POSITION: "Piezo Position (μm or mrad)",
            DataRecorderSource.SETPOINT: "Setpoint (μm or mrad)",
            DataRecorderSource.PIEZO_VOLTAGE: "Piezo Voltage (V)",
            DataRecorderSource.POSITION_ERROR: "Position Error",
            DataRecorderSource.ABS_POSITION_ERROR: "Absolute Position Error",
            DataRecorderSource.PIEZO_CURRENT_1: "Piezo Current 1 (A)",
            DataRecorderSource.PIEZO_CURRENT_2: "Piezo Current 2 (A)"
        }
        return human_readable.get(self, self.name)  # Fallback to enum name if not found
    

class RecorderAutoStartMode(Enum):
    """
    Enum representing the autostart mode of the data recorder.
    """
    OFF = 0
    "Autostart off - start recording manually with recorder start command"

    START_ON_SET_COMMAND = 1
    "Start on set-command"
    
    START_ON_WAVEFORM_GEN_RUN = 2
    "Start on waveform generator run"

    @classmethod
    def get_mode(cls, value: int) -> 'RecorderAutoStartMode':
        """
        Given a mode value, return the corresponding RecorderAutoStartMode enum.
        """
        for item in cls:
            if item.value == value:
                return item
        raise ValueError(f"Invalid RecorderAutoStartMode value: {value}")

    def __repr__(self):
        return f"{self.__class__.__name__}.{self.name}"
    


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

    class ChannelRecordingData(TimeSeries):
        """
        WaveformData is a NamedTuple that represents waveform data.

        Attributes:
            x_time (List[float]): A list of time values (in seconds) corresponding to the waveform.
            y_values (List[float]): A list of amplitude values corresponding to the waveform.
            sample_time_us (int): The sampling time in microseconds.
            sample_factor (int): A factor used to calculate the sample time from the base sample time.
        """
        _source : DataRecorderSource = None

        def __init__(self, values: list, sample_time_ms: int, source: DataRecorderSource):
            """
            Initialize the ChannelData instance with amplitude values, sample time, and source.
            
            Args:
                values (list): The amplitude values corresponding to the waveform.
                sample_time_ms (int): The sample time in milliseconds (sampling interval).
                source (str): The data recorder source
            """
            # Call the parent constructor (TimeSeries) to initialize the values and sample time
            super().__init__(values, sample_time_ms)
            self._source = source  # Private member for source
        
        @property
        def source(self) -> DataRecorderSource:
            """
            Read-only property to get the maximum sample buffer size for the data recorder.
            """
            return self._source


    _dev : NV200Device
    _sample_rate : int = None

    @property
    def max_sample_buffer_size(self) -> int:
        """
        Read-only property to get the maximum sample buffer size for the data recorder.
        """
        return self.NV200_RECORDER_BUFFER_SIZE

    def __init__(self, device: NV200Device):
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
        self._sample_rate = self.NV200_RECORDER_SAMPLE_RATE_HZ / stride

    async def set_sample_buffer_size(self, buffer_size: int):
        """
        Sets the sample buffer size for each of the two data recorder channels (0..6144)
        A value of 0 means infinite loop over maximum length until recorder is stopped manually.
        If you would like to have an infinite loop, use the constant `DataRecorder.INFINITE_RECORDING_DURATION`.
        You can get the maximum buffer size using the `max_sample_buffer_size` property.
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
        Stops the recording process by invoking the `start_recording` method with False.
        """
        await self.start_recording(False)

    async def is_recording(self) -> bool:
        """
        Check if the recoder is currently recording.
        """
        return bool(await self._dev.read_int_value('recrun'))
    
    async def wait_until_finished(self, timeout_s: float = 10.0):
        """
        Waits asynchronously until the recording process has finished or the specified timeout is reached.

        Args:
            timeout_s (float): The maximum time to wait in seconds. Defaults to 10.0.

        Returns:
            bool: True if the recording process finished within the timeout, False otherwise.

        Raises:
            asyncio.TimeoutError: If the timeout is reached before the recording process finishes.
        """
        return await wait_until(
            self.is_recording,
            check_func=lambda recoding_active: not recoding_active,
            poll_interval_s=0.1,
            timeout_s=timeout_s
        )

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
        async with self._dev.lock:
            recsrc = DataRecorderSource.from_value(await self._dev.read_int_value(cmd = f"recsrc,{channel}", param_index = 1))
            number_strings = await self._dev.read_values(f'recoutf,{channel}', self.BUFFER_READ_TIMEOUT_SECS)
            if self._sample_rate is None:
                stride = await self._dev.read_int_value("recstr")
                self._sample_rate = self.NV200_RECORDER_SAMPLE_RATE_HZ / stride

        numbers = []
        for num in number_strings[1:]:  # starts from the second element
            numbers.append(float(num))
        return self.ChannelRecordingData(numbers, 1000 / self._sample_rate, recsrc)
    
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
    
