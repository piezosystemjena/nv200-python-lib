"""
This module defines the transport protocols for communicating with NV200 devices, including Telnet and Serial interfaces.

Classes:
    - :class:`.TransportProtocol`: Abstract base class for transport protocols.
    - :class:`.TelnetProtocol`: Implements Telnet-based communication with NV200 devices.
    - :class:`.SerialProtocol`: Implements serial communication with NV200 devices.

Example:
    .. code-block:: python

        import asyncio
        from nv200.device_interface import DeviceClient
        from nv200.transport_protocols import SerialProtocol

        async def serial_port_auto_detect():
            transport = SerialProtocol()
            client = DeviceClient(transport)
            await client.connect()
            print(f"Connected to device on serial port: {transport.port}")
            await client.close()

        if __name__ == "__main__":
            asyncio.run(serial_port_auto_detect())

"""

import asyncio
import logging
from typing import List, Dict
from abc import ABC, abstractmethod
import telnetlib3
import aioserial
import serial.tools.list_ports
import nv200.lantronix_xport as xport


# Global module locker
logger = logging.getLogger(__name__)


class TransportProtocol(ABC):
    """
    Abstract base class representing a transport protocol interface for a device.
    """
    @abstractmethod
    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes an asynchronous connection to the NV200 device.

        This method is intended to handle the initialization of a connection
        to the NV200 device. The implementation should include the necessary
        steps to ensure the connection is successfully established.

        Raises:
            Exception: If the connection fails or encounters an error.
        """

    @abstractmethod
    async def read_response(self) -> str:
        """
        Asynchronously reads and returns a response as a string.

        Returns:
            str: The response read from the source.
        """

    @abstractmethod
    async def write(self, cmd: str):
        """
        Sends a command to the NV200 device asynchronously.

        Args:
            cmd (str): The command string to be sent to the device.

        Raises:
            Exception: If there is an error while sending the command.
        """

    @abstractmethod
    async def close(self):
        """
        Asynchronously closes the connection or resource associated with this instance.

        This method should be used to release any resources or connections
        that were opened during the lifetime of the instance. Ensure that this
        method is called to avoid resource leaks.

        Raises:
            Exception: If an error occurs while attempting to close the resource.
        """

    async def detect_device(self) -> bool:
        """
        Detects if the connected device is an NV200.

        This asynchronous method sends a command to the device and checks the response
        to determine if the device is an NV200. The detection is based on whether the
        response starts with the byte sequence "NV200".

        Returns:
            bool: True if the device is detected as an NV200, False otherwise.
        """
        await self.write('\r')
        response = await self.read_response()
        return response.startswith(b"NV200")



class TelnetProtocol(TransportProtocol):
    """
    TelnetTransport is a class that implements a transport protocol for communicating
    with piezosystem devices over Telnet. It provides methods to establish a connection,
    send commands, read responses, and close the connection.
    """
    __host : str
    __MAC : str
    __port : int
    
    def __init__(self, host: str = None, port: int = 23, MAC: str = None):
        """
        Initializes thetransport protocol.

        Args:
            host (str, optional): The hostname or IP address of the NV200 device. Defaults to None.
            port (int, optional): The port number to connect to. Defaults to 23.
            MAC (str, optional): The MAC address of the NV200 device. Defaults to None.
        """
        self.__host = host
        self.__port = port
        self.__MAC = MAC
        self.__reader = None
        self.__writer = None


    async def __connect_telnetlib(self):
        """
        Connect to telnetlib3 library
        """
        self.__reader, self.__writer = await asyncio.wait_for(
            telnetlib3.open_connection(self.__host, self.__port),
            timeout=5
        )        


    async def is_xon_xoff_forwared_to_host(self) -> bool:
        """
        Checks if XON/XOFF flow control is forwarded to the host.

        This method sends a command to the device and checks the response to determine
        if XON/XOFF flow control is enabled. The detection is based on whether the
        response starts with the byte sequence "XON/XOFF".

        Returns:
            bool: True if XON/XOFF flow control is forwarded to the host, False otherwise.
        """
        await self.write('\r\n')
        await asyncio.sleep(0.1)
        response = await self.__reader.read(1024)
        return response.startswith('\x13')
    
    @staticmethod
    async def configure_flow_control_mode(host: str) -> bool:
        """
        Configures the flow control mode for the device to pass XON/XOFF characters to host
        """
        return await xport.configure_flow_control(host)

    async def connect(self, auto_adjust_comm_params: bool = True):
        """
        Establishes a connection to a Lantronix device.

        This asynchronous method attempts to connect to a Lantronix device using
        either the provided MAC address or by discovering devices on the network.

        - If self.host is None and self.MAC is provided, it discovers the
          device's IP address using the MAC address.
        - If both self.host and self.MAC are None, it discovers all available
          Lantronix devices on the network and selects the first one.

        Once the device's IP address is determined, it establishes a Telnet
        connection to the device using the specified host and port.

        Raises:
            RuntimeError: If no devices are found during discovery.
        """
        if self.__host is None and self.__MAC is not None:
            self.__host = await xport.discover_lantronix_device_async(self.__MAC)
            if self.__host is None:
                raise RuntimeError(f"Device with MAC address {self.__MAC} not found")
        elif self.__host is None and self.__MAC is None:
            devices = await xport.discover_lantronix_devices_async()
            if not devices:
                raise RuntimeError("No devices found")
            self.__host = devices[0]['IP']
            self.__MAC = devices[0]['MAC']

        try:
            logger.debug("Connecting to device %s", self.__host)
            config_changed : bool = False
            await self.__connect_telnetlib()
            logger.debug("Connected to device %s", self.__host)
            # ensure that flow control XON and XOFF chars are forwarded to host
            if auto_adjust_comm_params:
                config_changed = await TelnetProtocol.configure_flow_control_mode(self.__host)
                # If flow control config changed, we need to reconnect
                if config_changed:
                    await self.__connect_telnetlib()
        except asyncio.TimeoutError as exc:
            raise RuntimeError(f"Device with host address {self.__host} not found") from exc
    
    async def write(self, cmd: str):
        self.__writer.write(cmd)
        
    async def read_response(self) -> str:
        data = await self.__reader.readuntil(b'\x11')
        return data.replace(b'\x11', b'').replace(b'\x13', b'') # strip XON and XOFF characters
    

    async def close(self):
        if self.__writer:
            self.__writer.close()
            self.__writer = None
            self.__reader.close()
            self.__reader = None

    @property
    def host(self) -> str:
        """
        Returns the host address.
        """
        return self.__host
    
    @property
    def MAC(self) -> str:
        """
        Returns the MAC address.
        """
        return self.__MAC
    
    @staticmethod
    async def discover_devices()  -> List[Dict[str, str]]:
        """
        Asynchronously discovers all devices connected via ethernet interface

        Returns:
            list: A list of dictionaries containing device information (IP and MAC addresses).
        """
        return await xport.discover_lantronix_devices_async()



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
    async def discover_devices()  -> List[str]:
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
                print(f"Error on port {port_name}: {e}")
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


    async def write(self, cmd: str):
        await self.__serial.write_async(cmd.encode('utf-8'))

    async def read_response(self) -> str:
        data = await self.__serial.read_until_async(serial.XON)
        return data.replace(serial.XON, b'').replace(serial.XOFF, b'') # strip XON and XOFF characters

    async def close(self):
        if self.__serial:
            self.__serial.close()

    @property
    def port(self) -> str:
        """
        Returns the serial port the device is connected to
        """
        return self.__port