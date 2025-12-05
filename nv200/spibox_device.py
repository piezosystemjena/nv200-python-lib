import asyncio
from typing import Optional, List
from nv200.device_base import PiezoDeviceBase
from nv200.serial_protocol import SerialProtocol
from nv200.transport_protocol import TransportProtocol
from nv200.waveform_generator import WaveformGenerator
import numpy as np
from enum import Enum


def parse_hex_to_floats_percent(data: str) -> List[float]:
    """
    Parses a string of 4-character hexadecimal values into a float.
    
    The hex values are interpreted as unsigned 16-bit integers and converted to floats.

    Args:
        data (str): A string of comma-separated 4-character hex values (e.g., "0000,FFFD,FFFD").

    Returns:
        List[float]: A list of float representations of the parsed unsigned integers.
    """
    MAX_VALID_HEX = 0xFFFE
    int_val = int(data, 16)

    if int_val > MAX_VALID_HEX:
        int_val = MAX_VALID_HEX  # Clip to max valid value

    percent = (int_val / MAX_VALID_HEX) * 100.0
    return percent


def percent_to_hex(value: float) -> str:
    """
    Converts a percentage value (0.0 to 100.0) to a 4-digit hexadecimal string.
    """
    # Clip value to range [0.0, 100.0]
    value = max(0.0, min(value, 100.0))
    # Scale to [0x0000, 0xFFFE]
    int_val = int(round(value / 100 * 0xFFFE))
    return f"{int_val:04x}"



class SpiBoxDevice(PiezoDeviceBase):
    """
    A high-level asynchronous client for communicating with NV200 piezo controllers.
    This class extends the `PiezoDeviceBase` base class and provides high-level methods
    for setting and getting various device parameters, such as PID mode, setpoint,
    """
    DEVICE_ID = "SPI Controller Box"

    class WaveformState(Enum):
        STOPPED          = 0
        RUNNING          = 1
        RUNNING_INFINITE = 2

    def __init__(self, transport):
        super().__init__(transport)

    def __is_connected_via_usb(self) -> bool:
        """
        Check if the device is connected via USB.
        This method is a placeholder and should be implemented based on actual connection checks.
        """
        return isinstance(self._transport, SerialProtocol)
    
    def __get_data_cmd(self) -> str:
        """
        Returns the command to get data based on the connection type.
        This method is a placeholder and should be implemented based on actual connection checks.
        """
        return "set"
    
    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes a connection using the transport layer.
        """
        self.transport_protocol.rx_delimiter = TransportProtocol.LF
        await super().connect(auto_adjust_comm_params)

    async def set_waveform_sample_factors(self, 
        ch1_factor: int, 
        ch2_factor: int, 
        ch3_factor: int
    ):
        """
        Set the waveform sample factors for each channel.

        Args:
            ch1_factor (int): Sample factor for channel 1.
            ch2_factor (int): Sample factor for channel 2.
            ch3_factor (int): Sample factor for channel 3.
        """
        await self.write(f'wfsfactor,{ch1_factor},{ch2_factor},{ch3_factor}')

    async def get_waveform_sample_factors(self) -> List[int]:
        """
        Get the waveform sample factors for each channel.

        Returns:
            List[int]: A list containing the sample factors for each channel.
        """
        command, parameters = await self.write('wfsfactor')
        factors = [int(param) for param in parameters]
        return factors

    async def get_setpoints_percent(self) -> List[float]:
        """
        Get device setpoints as percentages (0.0 to 100.0) for 3 channels.

        Returns:
            List[float]: A list containing the setpoints for each channel as percentages.
        """
        cmd = self.__get_data_cmd()
        parameters = []

        # Read the setpoints 3 times to ensure we get the correct SPI response
        for i in range(3):
            command, parameters = await self.write(cmd)

        return self.__parse_hex_set(parameters)

    async def set_setpoints_percent(
        self,
        ch1: float = 0,
        ch2: float = 0,
        ch3: float = 0,
    ) -> List[float]:
        """
        Set device setpoints as percentages (0.0 to 100.0) for 3 channels.

        Converts percent values to 16-bit hex strings and sends them as a formatted command.

        Args:
            ch1 (float): Setpoint for channel 1 (0.0 to 100.0).
            ch2 (float): Setpoint for channel 2 (0.0 to 100.0).
            ch3 (float): Setpoint for channel 3 (0.0 to 100.0).
        """
        cmd = self.__get_data_cmd()
        hex1 = percent_to_hex(ch1)
        hex2 = percent_to_hex(ch2)
        hex3 = percent_to_hex(ch3)

        full_cmd = f"{cmd},{hex1},{hex2},{hex3}"
        await self.write(full_cmd)

        return await self.get_setpoints_percent()
    
    async def set_waveform_cycles(
        self,
        ch1_cycles: int,
        ch2_cycles: int,
        ch3_cycles: int
    ):
        """
        Set the number of waveform cycles for each channel.

        Args:
            ch1_cycles (int): Number of cycles for channel 1.
            ch2_cycles (int): Number of cycles for channel 2.
            ch3_cycles (int): Number of cycles for channel 3.
        """
        await self.write(f'wfcycle,{ch1_cycles},{ch2_cycles},{ch3_cycles}')

    async def get_waveform_cycles(self) -> List[int]:
        """
        Get the number of waveform cycles for each channel.

        Returns:
            List[int]: A list containing the number of cycles for each channel.
        """
        command, parameters = await self.write('wfcycle')
        cycles = [int(param) for param in parameters]
        return cycles
    
    async def upload_waveform_samples(
        self,
        ch1: np.ndarray,
        ch2: np.ndarray,
        ch3: np.ndarray,
        on_progress: Optional[callable] = None
    ):
        """
        Upload waveform samples for each channel.

        Uploads the samples to the device after setting the sample counts.

        Args:
            ch1 (np.ndarray): Waveform samples for channel 1.
            ch2 (np.ndarray): Waveform samples for channel 2.
            ch3 (np.ndarray): Waveform samples for channel 3.
            on_progress (callable, optional): A callback function that receives progress updates.
        """

        lengths = [len(ch) if ch is not None else 0 for ch in (ch1, ch2, ch3)]

        await self.write(f'wfscount,{lengths[0]},{lengths[1]},{lengths[2]}')
        await self.set_waveform_samples(
            ch1 if ch1 is not None else np.array([]),
            ch2 if ch2 is not None else np.array([]),
            ch3 if ch3 is not None else np.array([]),
            on_progress=on_progress
        )

    async def start_waveforms(self):
        """
        Start the waveform playback.
        """
        await self.write('wfrun,1')

    async def stop_waveforms(self):
        """
        Stop any running waveforms on the device.
        """
        await self.write('wfrun,0')
    
    async def set_waveform_samples(
        self,
        ch1: np.ndarray,
        ch2: np.ndarray,
        ch3: np.ndarray,
        on_progress: Optional[callable] = None
    ):
        """
        Add waveform samples for each channel.
        """
        max_samples = max(len(ch1), len(ch2), len(ch3))

        for i in range(max_samples):
            hex1 = percent_to_hex(ch1[i]) if i < len(ch1) else "0000"
            hex2 = percent_to_hex(ch2[i]) if i < len(ch2) else "0000"
            hex3 = percent_to_hex(ch3[i]) if i < len(ch3) else "0000"

            cmd = f"wfset,{i},{hex1},{hex2},{hex3}"
            await self.write(cmd)

            if on_progress:
                on_progress(i + 1, max_samples)
                

    def __parse_wave_response(self, response: List[str]) -> List[np.ndarray]:
        """
        Parse a waveform response string from the device into three numpy arrays for each channel.

        The response string is expected to be a comma-separated list of hexadecimal values,
        where each set of three values corresponds to the readings from channels 1, 2 and 3.

        Args:
            response_str (str): The response string from the device.
        """

        values = self.__parse_hex_set(response)
        return values

    def __parse_hex_set(self, hex_set: List[str]) -> List[float]:
        """
        Parse a single set of comma-separated hexadecimal values into a list of floats.

        Args:
            hex_set (List[str]): A list of hexadecimal strings.

        Returns:
            List[float]: A list of float values parsed from the hex strings.
        """
        output = []

        for hex_val in hex_set:
            output.append(parse_hex_to_floats_percent(hex_val))

        return output

    async def get_waveform_response(
        self, 
        step_size: int = 1,
        max_samples: Optional[int] = None,
        on_progress: Optional[callable] = None,
    ) -> Optional[List[WaveformGenerator.WaveformData]]:
        """
        Get the current waveform response from the device.

        Args:
            step_size (int): The step size for sampling the waveform response.
            max_samples (int, optional): The maximum number of samples to retrieve. If None, retrieves all available samples.
            on_progress (callable, optional): A callback function that receives progress updates.

        Returns:
            A list containing three numpy arrays, one for each channel, with the waveform data. 
            If no samples are available, returns None.
        """

        response = [
            [],
            [],
            []
        ]
        
        # Get the number of samples
        available_sample_count = await self.get_response_samples_count()

        if available_sample_count == 0:
            return None
        
        sample_count = 0

        max_samples = min(max_samples, available_sample_count) if max_samples is not None else available_sample_count

        # Start from 2 because of delayed spi data
        for i in range(2, available_sample_count, step_size):
            values = await self.get_response_sample(i)

            response[0].append(values[0])
            response[1].append(values[1])
            response[2].append(values[2])

            if on_progress:
                on_progress(sample_count, max_samples)

            sample_count += 1

            # Respect max samples limit if provided
            if sample_count >= max_samples:
                break

        return [
            WaveformGenerator.WaveformData(
                values = response[0],
                sample_time_ms = step_size * WaveformGenerator.NV200_BASE_SAMPLE_TIME_US / 1000
            ),
            WaveformGenerator.WaveformData(
                values = response[1],
                sample_time_ms = step_size * WaveformGenerator.NV200_BASE_SAMPLE_TIME_US / 1000
            ),
            WaveformGenerator.WaveformData(
                values = response[2],
                sample_time_ms = step_size * WaveformGenerator.NV200_BASE_SAMPLE_TIME_US / 1000
            )
        ]
    
    async def get_response_samples_count(self) -> int:
        """
        Get the number of available response samples from the device.

        Returns:
            int: The number of available response samples.
        """
        command, parameters = await self.write('wfrcount')
        sample_count = int(parameters[0])
        return sample_count
    
    async def get_response_sample(self, index: int) -> List[float]:
        """
        Get a single response sample at the specified index.

        Args:
            index (int): The index of the sample to retrieve.

        Returns:
            List[float]: A list containing the waveform data for each channel at the specified index.
        """
        command, parameters = await self.write(f'wfget,{index}')
        values = self.__parse_wave_response(parameters)
        return values
    
    async def await_waveform_completion(self):
        """
        Waits until the waveform has completed.
        """
        while True:
            command, parameters = await self.write('wfrun')

            is_running = int(parameters[0]) == 1

            if not is_running:
                break

            await asyncio.sleep(0.1)
    
    async def get_waveform_status(self):
        """
        Get the current waveform status.
        """
        command, parameters = await self.write('wfrun')

        # Check if waveform is stopped
        if parameters[0] == '0':
            return SpiBoxDevice.WaveformState.STOPPED
        
        # If waveform is running, check if it's infinite or finite
        command, parameters = await self.write('wfcycle')

        if parameters[0] == '0' and parameters[1] == '0' and parameters[2] == '0':
            return SpiBoxDevice.WaveformState.RUNNING_INFINITE
        
        return SpiBoxDevice.WaveformState.RUNNING
