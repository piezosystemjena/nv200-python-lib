"""
WaveformGenerator module for controlling waveform generation on a connected NV200 device.

This module defines the `WaveformGenerator` class, which provides methods to configure and control waveform generation,
including the ability to generate sine waves, set cycles, adjust sampling times, and manage waveform buffers. It supports
asynchronous interaction with the device for real-time control of waveform generation.

Classes:
    - :class:`.WaveformGenerator`: Manages waveform generation and configuration on the NV200 device.
    - :class:`.WaveformData`: Represents waveform data with time, amplitude, and sample time.
"""
import math
import logging
import numpy as np
from typing import List, Union, Sequence, Optional
from enum import Enum

from nv200.nv200_device import NV200Device, ModulationSource
from nv200.shared_types import TimeSeries, ProgressCallback
from nv200.utils import wait_until

# Global module locker
logger = logging.getLogger(__name__)


def calculate_sampling_time_ms(time_samples: Union[Sequence[float], np.ndarray]) -> float:
    """
    Calculates the sampling time in milliseconds from a sequence of time samples.

    Args:
        time_samples (Union[Sequence[float], np.ndarray]): A list or NumPy array of time samples in milliseconds.

    Returns:
        float: The sampling time in milliseconds.

    Raises:
        ValueError: If the sequence has fewer than 2 time samples.
    """
    if len(time_samples) < 2:
        raise ValueError("At least two time samples are required to calculate sampling time.")
    return (time_samples[-1] - time_samples[0]) / (len(time_samples) - 1)      #


class WaveformType(Enum):
    """
    Enumeration for different waveform types supported by the generator.
    """
    SINE = 0
    TRIANGLE = 1
    SQUARE = 2


class WaveformUnit(Enum):
    """
    Enumeration for different waveform units used in the generator.
    """
    PERCENT = 0 # Percentage of the range (0-100%)
    POSITION = 1  # Length units (e.g., micrometers, millimeters)
    VOLTAGE = 2  # Voltage units (e.g., volts)


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
        

    def __init__(self, device: NV200Device):
        """
        Initializes the WaveformGenerator instance with the specified device client.

        Args:
            device (DeviceClient): The device client used for communication with the hardware.
        """
        self._dev = device
        self._waveform : WaveformGenerator.WaveformData = None


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

    async def stop(self):
        """
        Stops the waveform generator.
        This is equivalent to calling start(False).
        """
        await self._dev.write(f"grun,{0}")


    async def set_loop_start_index(self, start_index: int):
        """
        Sets the start index for the waveform generator loop. 
        If you use multiple cycles, the loop start index is the index defines the index
        where the waveform generator starts in the next cycle.
        """
        await self._dev.write(f"gsarb,{start_index}")


    async def set_loop_end_index(self, end_index: int):
        """
        Sets the end index for arbitrary waveform generator output.
        The loop end index is the index where the waveform generator jumps to the next
        cycle or finishes if only one cycle is used.
        """
        await self._dev.write(f"gearb,{end_index}")

    async def set_start_index(self, index: int):
        """
        Sets the offset index when arbitrary waveform generator 
        gets started. That means after the start() function is called, the arbitrary 
        waveform generator starts at the index defined by set_start_index() and runs 
        until the index defined by set_loop_end_index(). In all successive cycles, the arbitrary 
        waveform generator starts at set_loop_start_index(). This is repeated until the number 
        of cycles reaches the value given by set_cycles().
        """
        await self._dev.write(f"goarb,{index}")


    async def set_cycles(self, cycles: int = 0):
        """
        Sets the number of cycles to run.
        - WaveformGenerator.NV200_INFINITE_CYCLES - 0 = infinitely
        - 1…65535
        """
        await self._dev.write(f"gcarb,{cycles}")


    async def configure_waveform_loop(self, start_index: int, loop_start_index: int, loop_end_index: int):
        """
        Sets the start and end indices for the waveform loop.
        The start index is the index where the waveform generator starts when it is started.
        The loop start index is the index where the waveform generator starts in the next cycle
        and the loop end index is the index where the waveform generator jumps to the next cycle.
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

        Note: Normally you do not need to set the sampling time manually because it is set automatically
        calculated when the waveform is generated.
        """
        rounded_sampling_time = round(sampling_time / 50) * 50
        factor = rounded_sampling_time // 50
        factor = max(1, min(factor, 65535))
        await self._dev.write(f"gtarb,{factor}")
        return rounded_sampling_time
   


    async def set_waveform_value_percent(self, index : int, percent : float):
        """
        Sets the value of the waveform at the specified index in percent from 0 - 100%
        In closed loop mode, the value is interpreted as a percentage of the position range (i.e. 0 - 80 mra)
        and in open loop mode, the value is interpreted as a percentage of the voltage range (i.e. -20 - 130 V).
        """
        if not 0 <= index < self.NV200_WAVEFORM_BUFFER_SIZE:
            raise ValueError(f"Buffer index must be in the range from 0 to {self.NV200_WAVEFORM_BUFFER_SIZE} , got {index}")
        if not 0 <= percent <= 100:
            raise ValueError(f"Waveform value must be in the range from 0 to 100%, got {percent}")
        await self._dev.write(f"gbarb,{index},{percent}")


    async def set_waveform_buffer(self, buffer: list[float], unit: WaveformUnit = WaveformUnit.PERCENT, on_progress: Optional[ProgressCallback] = None):
        """
        Writes a full waveform buffer to the device by setting each value
        using set_waveform_value.
        The buffer should contain waveform values in percent (0-100).
        In closed loop mode, the value is interpreted as a percentage of the position range (i.e. 0 - 80 mra)
        and in open loop mode, the value is interpreted as a percentage of the voltage range (i.e. -20 - 130 V).

        Parameters:
            buffer (list of float): The waveform values in percent (0-100).
            unit (WaveformUnit): The unit of the waveform values. Defaults to WaveformUnit.PERCENT.
            on_progress (Optional[ProgressCallback]): Optional callback for progress updates.

        Raises:
            ValueError: If the buffer size exceeds the maximum buffer length.
        """
        if len(buffer) > self.NV200_WAVEFORM_BUFFER_SIZE:
            raise ValueError(
                f"Buffer too large: max size is {self.NV200_WAVEFORM_BUFFER_SIZE}, got {len(buffer)}"
            )
        
        value_range = None
        if unit == WaveformUnit.POSITION:
            value_range = await self._dev.get_position_range()
        elif unit == WaveformUnit.VOLTAGE:
            value_range = await self._dev.get_voltage_range()

        if value_range is not None:
            # Scale values to to percent
            buffer = [100 * (value - value_range[0]) / (value_range[1] - value_range[0]) for value in buffer]


        total = len(buffer)
        for index, percent in enumerate(buffer):
            await self.set_waveform_value_percent(index, percent)
            if on_progress:
                await on_progress(index + 1, total)

    async def set_waveform(
        self,
        waveform: WaveformData,
        unit: WaveformUnit = WaveformUnit.PERCENT,
        adjust_loop: bool = True,
        on_progress: Optional[ProgressCallback] = None,
    ):
        """
        Sets the waveform data in the device.
        The WaveformData object should contain the waveform values and the sample time.

        Parameters:
            waveform (WaveformData): The waveform data to be set.
            unit (WaveformUnit): The unit of the waveform values. Defaults to WaveformUnit.PERCENT.
            adjust_loop (bool): If True, adjusts the loop indices based on the
                                waveform data, if false, the loop indices are not adjusted.
                                If the loop indices are adjusted, then they will be set to
                                the following value:
                                - start_index = 0 (first waveform value)
                                - loop_start_index = 0 (first waveform value)
                                - loop_end_index = last waveform value
            on_progress (Optional[ProgressCallback]): Optional callback for progress updates.

        Raises:
            ValueError: If the waveform data is invalid.
        """
        await self.set_waveform_buffer(waveform.values, unit=unit, on_progress=on_progress)
        self._waveform = waveform
        await self.set_output_sampling_time(int(waveform.sample_time_ms * 1000))
        if not adjust_loop:
            return
        # Adjust loop indices based on the waveform data
        await self.configure_waveform_loop(
            start_index=0,
            loop_start_index=0,
            loop_end_index=len(waveform.values) - 1,
        )

    async def set_waveform_from_samples(
        self,
        time_samples: Union[Sequence[float], np.ndarray],
        values: Union[Sequence[float], np.ndarray],
        unit: WaveformUnit = WaveformUnit.PERCENT,
        adjust_loop: bool = True
    ):
        """
        Sets the waveform data in the device from separate time samples and values.
        The waveform data should contain the time samples in milliseconds and the corresponding
        amplitude values. in percent (0-100).
        In closed loop mode, the value is interpreted as a percentage of the position range (i.e. 0 - 80 mra)
        and in open loop mode, the value is interpreted as a percentage of the voltage range (i.e. -20 - 130 V).

        Args:
            time_samples (Sequence[float] or np.ndarray): Time samples in milliseconds.
            values (Sequence[float] or np.ndarray): Corresponding waveform amplitude values in percent (0-100).
            unit (WaveformUnit, optional): The unit of the waveform values. Defaults to WaveformUnit.PERCENT.
            adjust_loop (bool): If True, adjusts loop indices based on data length.

        Raises:
            ValueError: If inputs are invalid or lengths mismatch.
        """
        if len(time_samples) != len(values):
            raise ValueError("Time samples and values must have the same length.")
        if len(time_samples) == 0:
            raise ValueError("Input arrays cannot be empty.")
        
        # Calculate sample_time_ms from time_samples
        sample_time_ms = calculate_sampling_time_ms(time_samples)

        # Create WaveformData object (assuming it takes values and sample_time_ms)
        waveform = self.WaveformData(values=list(values), sample_time_ms=sample_time_ms)

        # Use existing set_waveform method to actually send data
        await self.set_waveform(waveform, unit=unit, adjust_loop=adjust_loop)


    async def is_running(self) -> bool:
        """
        Checks if the waveform generator is currently running.

        Returns:
            bool: True if the waveform generator is running, False otherwise.
        """
        return bool(await self._dev.read_int_value('grun'))
    
    async def wait_until_finished(self, timeout_s: float = 10.0):
        """
        Waits until the waveform generator is finished running.

        Args:
            timeout_s (float): The maximum time to wait in seconds. Defaults to 10 seconds.

        Returns:
            bool: True if the waveform generator finished running, False if timed out.
        """
        return await wait_until(
            self.is_running,
            check_func=lambda x: not x,
            poll_interval_s=0.1,
            timeout_s=timeout_s
        )
    
    @classmethod
    def generate_time_samples_list(cls, freq_hz: float) -> List[float]:
        """
        Generates a list of time samples (in milliseconds) for one period of a waveform at the specified frequency.
        Sampling is adjusted based on hardware base sample time and buffer constraints.

        Args:
            freq_hz (float): The frequency of the waveform in Hertz.

        Returns:
            List[float]: Time samples (in milliseconds).
        """
        if freq_hz <= 0:
            raise ValueError("Frequency must be greater than zero.")

        buf_size = cls.NV200_WAVEFORM_BUFFER_SIZE
        base_sample_time_us = cls.NV200_BASE_SAMPLE_TIME_US

        period_us = 1_000_000 / freq_hz
        ideal_sample_time_us = period_us / buf_size

        sample_factor = math.ceil(ideal_sample_time_us / base_sample_time_us)
        sample_time_us = sample_factor * base_sample_time_us
        sample_time_s = sample_time_us / 1_000_000

        required_buffer = int(period_us / sample_time_us)
        return [i * sample_time_s * 1000 for i in range(required_buffer)]
    

    @classmethod
    def generate_time_samples_array(cls, freq_hz: float) -> np.ndarray:
        """
        Generates a NumPy array of time samples (in milliseconds) for one period of a waveform at the specified frequency.

        Args:
            freq_hz (float): The frequency of the waveform in Hertz.

        Returns:
            np.ndarray: Time samples (in milliseconds).
        """
        return np.array(cls.generate_time_samples_list(freq_hz))

    @classmethod
    def generate_sine_wave(
        cls,
        freq_hz: float,
        low_level: float,
        high_level: float,
        phase_shift_rad: float = 0.0,
    ) -> WaveformData:
        """
        Generates a sine wave based on the specified frequency and amplitude levels.

        Args:
            freq_hz (float): The frequency of the sine wave in Hertz (Hz).
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
        times_ms = cls.generate_time_samples_list(freq_hz)

        amplitude = (high_level - low_level) / 2.0
        offset = (high_level + low_level) / 2.0
        values: List[float] = [
            offset + amplitude * math.sin(2 * math.pi * freq_hz * (t_ms / 1000) + phase_shift_rad)
            for t_ms in times_ms
        ]

        return cls.WaveformData(
            values=values,
            sample_time_ms=calculate_sampling_time_ms(times_ms)
        )


    @classmethod
    def generate_triangle_wave(
        cls,
        freq_hz: float,
        low_level: float,
        high_level: float,
        phase_shift_rad: float = 0.0,
    ) -> WaveformData:
        """
        Generates a triangle wave based on the specified frequency and amplitude levels.

        Args:
            freq_hz (float): The frequency of the triangle wave in Hertz (Hz).
            low_level (float): The minimum value (low level) of the triangle wave.
            high_level (float): The maximum value (high level) of the triangle wave.
            phase_shift_rad (float, optional): Phase shift in radians. Defaults to 0.0.

        Returns:
            WaveformData: An object containing the generated triangle wave data, including:
                - values (List[float]): A list of amplitude values for the triangle wave at each time point.
                - sample_time_ms (float): The time interval between samples in milliseconds (ms).

        Notes:
            - The method calculates an optimal sample time based on the desired frequency and the
            hardware's base sample time.
            - The waveform is normalized between -1 and 1, then scaled and offset to fit between
            low_level and high_level.
            - The waveform is generated over one full period.
        """
        times_ms = cls.generate_time_samples_array(freq_hz)  # NumPy array in ms
        t = times_ms / 1000.0  # Convert to seconds

        amplitude = (high_level - low_level) / 2.0
        offset = (high_level + low_level) / 2.0
        period_s = 1.0 / freq_hz

        # Apply phase shift in time domain
        phase_shift_t = phase_shift_rad / (2 * np.pi * freq_hz)
        t_shifted = t + phase_shift_t

        # Generate normalized triangle wave in [-1, 1]
        normalized_t = ((t_shifted / period_s) - 0.25) % 1.0
        triangle = 4 * np.abs(normalized_t - 0.5) - 1

        y = offset + amplitude * triangle

        return cls.WaveformData(
            values=y.tolist(),
            sample_time_ms=calculate_sampling_time_ms(times_ms)
        )


    @classmethod
    def generate_square_wave(
        cls,
        freq_hz: float,
        low_level: float,
        high_level: float,
        phase_shift_rad: float = 0.0,
        duty_cycle: float = 0.5,
    ) -> WaveformData:
        """
        Generates a square wave (or PWM waveform) using NumPy for efficient computation.

        Args:
            freq_hz (float): Frequency of the waveform in Hz.
            low_level (float): Output level during the "low" part of the cycle.
            high_level (float): Output level during the "high" part of the cycle.
            duty_cycle (float, optional): Duty cycle as a fraction between 0.0 and 1.0.
                                        Defaults to 0.5 (i.e., 50%).
            phase_shift_rad (float, optional): Phase shift in radians. Defaults to 0.0.

        Returns:
            WaveformData: An object containing:
                - values (List[float]): Amplitude values of the waveform.
                - sample_time_ms (float): Time between samples in milliseconds.
        """
        if not (0.0 < duty_cycle <= 1.0):
            raise ValueError("Duty cycle must be between 0.0 (exclusive) and 1.0 (inclusive).")

        times_ms = cls.generate_time_samples_array(freq_hz)  # NumPy array (ms)
        t = times_ms / 1000.0  # Convert to seconds
        period_s = 1.0 / freq_hz

        # Apply phase shift in time domain
        phase_shift_t = phase_shift_rad / (2 * np.pi * freq_hz)
        t_shifted = t + phase_shift_t

        # Time within the period (0 to 1)
        normalized_t = (t_shifted / period_s) % 1.0

        # Generate square wave with duty cycle
        values = np.where(normalized_t < duty_cycle, high_level, low_level)

        return cls.WaveformData(
            values=values.tolist(),
            sample_time_ms=calculate_sampling_time_ms(times_ms)
        )
    

    @classmethod
    def generate_waveform(
        cls,
        waveform_type: WaveformType,
        freq_hz: float,
        low_level: float,
        high_level: float,
        phase_shift_rad: float = 0.0,
        duty_cycle: float = 0.5,
    ) -> WaveformData:
        """
        Generates a waveform based on the specified type and parameters.

        Args:
            waveform_type (Waveform): The type of waveform to generate (SINE, TRIANGLE, SQUARE).
            freq_hz (float): Frequency of the waveform in Hertz.
            low_level (float): Minimum value of the waveform.
            high_level (float): Maximum value of the waveform.
            phase_shift_rad (float, optional): Phase shift in radians. Defaults to 0.0.
            duty_cycle (float, optional): Duty cycle for square wave. Defaults to 0.5.

        Returns:
            WaveformData: The generated waveform data.
        """
        if waveform_type == WaveformType.SINE:
            return cls.generate_sine_wave(freq_hz, low_level, high_level, phase_shift_rad)
        elif waveform_type == WaveformType.TRIANGLE:
            return cls.generate_triangle_wave(freq_hz, low_level, high_level, phase_shift_rad)
        elif waveform_type == WaveformType.SQUARE:
            return cls.generate_square_wave(freq_hz, low_level, high_level, phase_shift_rad, duty_cycle)
        else:
            raise ValueError(f"Unsupported waveform type: {waveform_type}")
