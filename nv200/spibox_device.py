import asyncio
from typing import Optional, List
from nv200.device_base import PiezoDeviceBase
from nv200.serial_protocol import SerialProtocol
from nv200.transport_protocol import TransportProtocol
import numpy as np


def parse_hex_to_floats_percent(data: str) -> List[float]:
    """
    Parses a comma-separated string of 4-character hexadecimal values into a list of floats.
    
    The hex values are interpreted as unsigned 16-bit integers and converted to floats.

    Args:
        data (str): A string of comma-separated 4-character hex values (e.g., "0000,FFFD,FFFD").

    Returns:
        List[float]: A list of float representations of the parsed unsigned integers.
    """
    MAX_VALID_HEX = 0xFFFE
    hex_values = data.split(',')
    percents = []

    for hex_val in hex_values:
        int_val = int(hex_val, 16)
        if int_val > MAX_VALID_HEX:
            int_val = MAX_VALID_HEX  # Clip to max valid value
        percent = (int_val / MAX_VALID_HEX) * 100.0
        percents.append(percent)

    return percents


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
        return "usbdata" if self.__is_connected_via_usb() else "ethdata"
    
    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes a connection using the transport layer.
        """
        self.transport_protocol.rx_delimiter = TransportProtocol.LF
        await super().connect(auto_adjust_comm_params)


    async def set_setpoints_percent(
        self,
        ch1: float = 0,
        ch2: float = 0,
        ch3: float = 0,
    ) -> List[float]:
        """
        Set device setpoints as percentages (0.0 to 100.0) for 3 channels.

        Converts percent values to 16-bit hex strings and sends them as a formatted command.
        """
        cmd = self.__get_data_cmd()
        hex1 = percent_to_hex(ch1)
        hex2 = percent_to_hex(ch2)
        hex3 = percent_to_hex(ch3)

        full_cmd = f"{cmd},{hex1},{hex2},{hex3}"
        print(f"Sending command: {full_cmd}")
        response : str
        response = await self.read_response_string(full_cmd)

        # This is a workaround to ensure the command is processed correctly and we get the
        # expected response - normally sending 4 times ensures, that wie get the correct SPI
        # response
        for i in range(3):
            await asyncio.sleep(0.1)  # Allow some time for the device to process the command
            response = await super().read_stripped_response_string(full_cmd)
        return parse_hex_to_floats_percent(response)

    async def set_waveforms(
        self,
        ch1: Optional[np.ndarray],
        ch2: Optional[np.ndarray],
        ch3: Optional[np.ndarray],
    ) -> List[np.ndarray]:
        """
        Set waveforms for the device channels.
        
        Each channel can be set to a waveform represented as a numpy array of floats.
        The values are expected to be in the range [0.0, 100.0].
        
        Args:
            ch1 (Optional[np.ndarray]): Waveform for channel 1.
            ch2 (Optional[np.ndarray]): Waveform for channel 2.
            ch3 (Optional[np.ndarray]): Waveform for channel 3.
        
        Returns:
            str: Response from the device after setting the waveforms.
        """
        # Determine number of samples from available channel or default to 0
        lengths = [len(ch) for ch in (ch1, ch2, ch3) if ch is not None]
        if not lengths:
            raise ValueError("At least one channel must be provided.")
        num_samples = max(lengths)

        # Helper to get hex or fill with 0000
        def channel_value(ch, i):
            if ch is None or i >= len(ch):
                return "0000"
            else:
                return percent_to_hex(ch[i])
            
        triplets = [
            f"{channel_value(ch1, i)},{channel_value(ch2, i)},{channel_value(ch3, i)}"
            for i in range(num_samples)
        ]

        tp = self.transport_protocol
        #await tp.flush_input()
        await tp.write(f'totalsamplex,{len(ch1) if ch1 is not None else 0}\r\n')
        await tp.write(f'totalsampley,{len(ch2) if ch2 is not None else 0}\r\n')
        await tp.write(f'totalsamplez,{len(ch3) if ch3 is not None else 0}\r\n')
     
        cmd = self.__get_data_cmd()
        full_cmd = cmd  + "," + "\r".join(triplets)
        response = await super().read_stripped_response_string(full_cmd, 200)
        
        # Split by commas
        hex_values = response.strip().split(',')

        if len(hex_values) % 3 != 0:
            raise ValueError("Response length is not a multiple of 3.")

        # Number of samples
        num_samples = len(hex_values) // 3

        # Convert hex strings to floats
        floats = [parse_hex_to_floats_percent(h) for h in hex_values]

        # Split floats into channels
        ch1 = np.array(floats[0::3])
        ch2 = np.array(floats[1::3])
        ch3 = np.array(floats[2::3])

        return [ch1, ch2, ch3]