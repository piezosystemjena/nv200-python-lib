import asyncio
import aioserial
import logging
from typing import List
import serial.tools.list_ports
from nv200.transport_protocol import TransportProtocol
from nv200.shared_types import DiscoverFlags

# Global module locker
logger = logging.getLogger(__name__)

class SerialProtocol(TransportProtocol):
    """
    A class to handle serial communication with an NV200 device using the AioSerial library.
    Attributes:
        port (str): The serial port to connect to. Defaults to None. If port is None, the class
        will try to auto detect the port.
        baudrate (int): The baud rate for the serial connection. Defaults to 115200.
        serial (AioSerial): The AioSerial instance for asynchronous serial communication.
    """
    __port : str
    __baudrate : int
    
    def __init__(self, port : str = None, baudrate : int = 115200):
        """
        Initializes the NV200 driver with the specified serial port settings.

        Args:
            port (str, optional): The serial port to connect to. Defaults to None.
                                  If port is None, the class will try to auto detect the port.
            baudrate (int, optional): The baud rate for the serial connection. Defaults to 115200.
        """
        self.__serial = None
        self.__port = port
        self.__baudrate = baudrate


    async def detect_port(self)-> str | None:
        """
        Asynchronously detects and configures the serial port for the NV200 device.

        This method scans through all available serial ports to find one with a 
        manufacturer matching "FTDI". If such a port is found, it attempts to 
        communicate with the device to verify if it is an NV200 device. If the 
        device is successfully detected, the port is configured and returned.

        Returns:
            str: The device name of the detected port if successful, otherwise None.
        """
        ports = serial.tools.list_ports.comports()
        for port in ports:
            if port.manufacturer != "FTDI":
                continue
            self.__serial.close()
            self.__serial.port = port.device
            self.__serial.open()
            if await self.detect_device():
                return port.device
            else:
                self.__serial.close()
        return None
    

    @staticmethod
    async def discover_devices(flags: DiscoverFlags)  -> List[str]:
        """
        Asynchronously discovers all devices connected via serial interface.

        Returns:
            list: A list of serial port strings where a device has been detected.
        """
        ports = serial.tools.list_ports.comports()
        valid_ports = [p.device for p in ports if p.manufacturer == "FTDI"]

        async def detect_on_port(port_name: str) -> str | None:
            protocol = SerialProtocol(port_name)
            try:
                await protocol.connect()
                detected = await protocol.detect_device()
                return port_name if detected else None
            except Exception as e:
                # We do ignore the exception - if it is not possible to connect to the device, we just return None
                print(f"Error on port {port_name}: {e.__class__.__name__} {e}")
                return None
            finally:
                await protocol.close()

        # Run all detections concurrently
        tasks = [detect_on_port(port) for port in valid_ports]
        results = await asyncio.gather(*tasks)

        # Filter out Nones
        return [port for port in results if port]

    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes an asynchronous connection to the NV200 device using the specified serial port settings.

        This method initializes the serial connection with the given port, baud rate, and flow control settings.
        If the port is not specified, it attempts to automatically detect the NV200 device's port. If the device
        cannot be found, a RuntimeError is raised.

        Raises:
            RuntimeError: If the NV200 device cannot be detected or connected to.
        """
        self.__serial = aioserial.AioSerial(port=self.__port, xonxoff=False, baudrate=self.__baudrate)
        if self.__port is None:
            self.__port = await self.detect_port()
        if self.__port is None:
            raise RuntimeError("NV200 device not found")

    async def flush_input(self):
        """
        Discard all available input within a short timeout window.
        """
        self.__serial.reset_input_buffer()

    async def write(self, cmd: str):
        await self.flush_input()
        await self.__serial.write_async(cmd.encode('utf-8'))

    async def read_until(self, expected: bytes = TransportProtocol.XON, timeout : float = TransportProtocol.DEFAULT_TIMEOUT_SECS) -> str:
        data = await asyncio.wait_for(self.__serial.read_until_async(expected), timeout)
        #return data.replace(TransportProtocol.XON, b'').replace(TransportProtocol.XOFF, b'') # strip XON and XOFF characters
        return data.decode('utf-8').strip("\x11\x13") # strip XON and XOFF characters

    async def close(self):
        if self.__serial:
            self.__serial.close()

    @property
    def port(self) -> str:
        """
        Returns the serial port the device is connected to
        """
        return self.__port
    