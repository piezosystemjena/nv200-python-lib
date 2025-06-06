from typing import Optional
from nv200.device_base import PiezoDeviceBase
from nv200.serial_protocol import SerialProtocol


class SpiBoxDevice(PiezoDeviceBase):
    """
    A high-level asynchronous client for communicating with NV200 piezo controllers.
    This class extends the `PiezoController` base class and provides high-level methods
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

    async def set_setpoints_percent(
        self,
        ch1: float = 0,
        ch2: float = 0,
        ch3: float = 0,
    ) -> None:
        """
        Set device setpoints as percentages (0.0 to 100.0) for 3 channels.

        Converts percent values to 16-bit hex strings and sends them as a formatted command.
        """
        def percent_to_hex(value: float) -> str:
            # Clip value to range [0.0, 100.0]
            value = max(0.0, min(value, 100.0))
            # Scale to [0x0000, 0xFFFE]
            int_val = int(round(value / 100 * 0xFFFE))
            return f"{int_val:04x}"

        cmd = self.__get_data_cmd()
        hex1 = percent_to_hex(ch1)
        hex2 = percent_to_hex(ch2)
        hex3 = percent_to_hex(ch3)

        full_cmd = f"{cmd},{hex1},{hex2},{hex3}"
        print(f"Sending command: {full_cmd}")

