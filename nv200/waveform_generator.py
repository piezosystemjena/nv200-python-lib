"""
This module provides access to the NV200 arbitrary waveform generator
"""
import math
from typing import List, Tuple, NamedTuple

from nv200.device_interface import DeviceClient, ModulationSource
from nv200.utils import TimeSeries


class WaveformGenerator:
    """
    WaveformGenerator is a class responsible for generating waveforms using a connected device.
    """
    NV200_WAVEFORM_BUFFER_SIZE = 1024  # Size of the data buffer for waveform generator
    NV200_BASE_SAMPLE_TIME_US = 50  # Base sample time in microseconds
    NV200_INFINITE_CYCLES = 0  # Infinite cycles constant for the waveform generator
    
    class WaveformData(TimeSeries):
        """
        WaveformData is a NamedTuple that represents waveform data.

        Attributes:
            x_time (List[float]): A list of time values (in seconds) corresponding to the waveform.
            y_values (List[float]): A list of amplitude values corresponding to the waveform.
            sample_time_us (int): The sampling time in microseconds.
            sample_factor (int): A factor used to calculate the sample time from the base sample time.
        """

        @property
        def sample_factor(self):
            """
            Returns the sample factor used to calculate the sample time from the base sample time.
            """
            return (self.sample_time_ms * 1000) // WaveformGenerator.NV200_BASE_SAMPLE_TIME_US
        
        @property
        def cycle_time_ms(self):
            """
            Returns the cycle of a single cycle in milliseconds.
            """
            return len(self.values) * self.sample_time_ms
        
    _dev : DeviceClient = None
    _waveform : WaveformData = None

    def __init__(self, device: DeviceClient):
        """
        Initializes the WaveformGenerator instance with the specified device client.

        Args:
            device (DeviceClient): The device client used for communication with the hardware.
        """
        self._dev = device


    async def start(self, start : bool = True, cycles: int = -1, start_index: int = -1):
        """
        Starts / stops the waveform generator

        Args:
            start (bool, optional): If True, starts the waveform generator. If False, stops it. Defaults to True.
            cycles (int, optional): The number of cycles to run the waveform generator. 
                        If set to -1, the value configured via set_cycles() will be used.
        """
        if cycles > -1:
            await self.set_cycles(cycles)
        if start_index > -1:
            await self.set_start_index(start_index)
        await self._dev.set_modulation_source(ModulationSource.WAVEFORM_GENERATOR)
        await self._dev.write(f"grun,{int(start)}")


    async def set_loop_start_index(self, start_index: int):
        """
        Sets the start index for arbitrary waveform generator output
        """
        await self._dev.write(f"gsarb,{start_index}")


    async def set_loop_end_index(self, end_index: int):
        """
        Sets the end index for arbitrary waveform generator output
        """
        await self._dev.write(f"gearb,{end_index}")

    async def set_start_index(self, index: int):
        """
        Sets the offset index when arbitrary waveform generator 
        gets started. That means after the start() function is called, the arbitrary 
        waveform generator starts at the index defined by set_start_offset() and runs 
        until the index defined by set_end_index(). In all successive cycles, the arbitrary 
        waveform generator starts at set_start_index(). This is repeated until the number 
        of cycles reaches the value given by set_cycles().
        """
        await self._dev.write(f"goarb,{index}")


    async def set_cycles(self, cycles: int = 0):
        """
        Sets the number of cycles to run.
        - 0 = infinitely
        - 1…65535
        """
        await self._dev.write(f"gcarb,{cycles}")


    async def configure_waveform_loop(self, start_index: int, loop_start_index: int, loop_end_index: int):
        """
        Sets the start and end indices for the waveform loop.
        """
        await self.set_start_index(start_index)
        await self.set_loop_start_index(loop_start_index)
        await self.set_loop_end_index(loop_end_index)

    async def set_output_sampling_time(self, sampling_time: int):
        """
        Sets the output sampling time for the waveform generator.
        The output sampling time can be given in multiples of 50 µs from
        1 * 50µs to 65535 * 50µs. If the sampling time is not a multiple
        of 50, it will be rounded to the nearest multiple of 50µs.
        The calculated sampling time is returned in microseconds.

        Returns:
            int: The set sampling time in microseconds.
        """
        rounded_sampling_time = round(sampling_time / 50) * 50
        factor = rounded_sampling_time // 50
        factor = max(1, min(factor, 65535))
        await self._dev.write(f"gtarb,{factor}")
        return rounded_sampling_time
   
    async def set_waveform_value(self, index : int, value : float):
        """
        Sets the value of the waveform at the specified index
        in length units (μm or mrad).
        """
        if not 0 <= index < self.NV200_WAVEFORM_BUFFER_SIZE:
            raise ValueError(f"Buffer index must be in the range from 0 to {self.NV200_WAVEFORM_BUFFER_SIZE} , got {value}")
        await self._dev.write(f"gparb,{index},{value}")

    async def set_waveform_buffer(self, buffer: list[float]):
        """
        Writes a full waveform buffer to the device by setting each value
        using set_waveform_value.

        Parameters:
            buffer (list of float): The waveform values in length units (μm or mrad).

        Raises:
            ValueError: If the buffer size exceeds the maximum buffer length.
        """
        if len(buffer) > self.NV200_WAVEFORM_BUFFER_SIZE:
            raise ValueError(
                f"Buffer too large: max size is {self.NV200_WAVEFORM_BUFFER_SIZE}, got {len(buffer)}"
            )

        for index, value in enumerate(buffer):
            await self.set_waveform_value(index, value)

    async def set_waveform(self, waveform: WaveformData, adjust_loop: bool = True):
        """
        Sets the waveform data in the device.

        Parameters:
            waveform (WaveformData): The waveform data to be set.
            adjust_loop (bool): If True, adjusts the loop indices based on the 
                                waveform data, if false, the loop indices are not adjusted.

        Raises:
            ValueError: If the waveform data is invalid.
        """
        await self.set_waveform_buffer(waveform.y_values)
        self._waveform = waveform
        await self.set_output_sampling_time(waveform.sample_time_us)
        if not adjust_loop:
            return
        # Adjust loop indices based on the waveform data
        await self.configure_waveform_loop(
            start_index=0,
            loop_start_index=0,
            loop_end_index=len(waveform.y_values) - 1,
        )

    async def is_running(self) -> bool:
        """
        Checks if the waveform generator is currently running.

        Returns:
            bool: True if the waveform generator is running, False otherwise.
        """
        response = await self._dev.read_int_value('grun')
        return response == "1"


    def generate_sine_wave(
        self,
        freq_hz: float,
        low_level: float,
        high_level: float,
        phase_shift_rad: float = 0.0,
    ) -> WaveformData:
        """
        Generates a sine wave based on the specified frequency and amplitude levels.
        Args:
            frequency (float): The frequency of the sine wave in Hertz (Hz).
            low_level (float): The minimum value (low level) of the sine wave.
            high_level (float): The maximum value (high level) of the sine wave.
        Returns:
            WaveformData: An object containing the generated sine wave data, including:
                - x_time (List[float]): A list of time points in ms corresponding to the sine wave samples.
                - y_values (List[float]): A list of amplitude values for the sine wave at each time point.
                - sample_time_us (float): The time interval between samples in microseconds (µs).
        Notes:
            - The method calculates an optimal sample time based on the desired frequency and the
              hardware's base sample time.
            - The buffer size is adjusted to ensure the generated waveform fits within one period
              of the sine wave.
            - The sine wave is scaled and offset to match the specified low and high levels.
        """
        BUFFER_SIZE = self.NV200_WAVEFORM_BUFFER_SIZE
        BASE_SAMPLE_TIME_US = self.NV200_BASE_SAMPLE_TIME_US

        period_us = 1_000_000 / freq_hz
        ideal_sample_time_us = period_us / BUFFER_SIZE

        sample_factor = math.ceil(ideal_sample_time_us / BASE_SAMPLE_TIME_US)
        sample_time_us = sample_factor * BASE_SAMPLE_TIME_US
        sample_time_s = sample_time_us / 1_000_000
        required_buffer = int(period_us / sample_time_us)
        amplitude = (high_level - low_level) / 2.0
        offset = (high_level + low_level) / 2.0

        times_ms: List[float] = [i * sample_time_s * 1000 for i in range(required_buffer)]
        values: List[float] = [
            offset + amplitude * math.sin(2 * math.pi * freq_hz * (t_ms / 1000) + phase_shift_rad)
            for t_ms in times_ms
        ]

        print(f"Optimal sample time: {sample_time_us} µs, "
              f"Buffer size: {len(values)}, "
              f"Frequency: {freq_hz} Hz, "
              f"Scale factor: {sample_factor}")

        return self.WaveformData(
            values=values,
            sample_time_ms=sample_time_us / 1000
        )
