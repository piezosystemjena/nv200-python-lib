import telnetlib3
from abc import ABC, abstractmethod
import aioserial
import serial.tools.list_ports
import lantronix_device_discovery_async as ldd

class TransportProtocol(ABC):
    """
    Abstract base class representing a transport protocol interface for a device.
    """
    @abstractmethod
    async def connect(self):
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

    async def connect(self):
        """
        Establishes a connection to a Lantronix device.

        This asynchronous method attempts to connect to a Lantronix device using
        either the provided MAC address or by discovering devices on the network.

        - If `self.host` is `None` and `self.MAC` is provided, it discovers the
          device's IP address using the MAC address.
        - If both `self.host` and `self.MAC` are `None`, it discovers all available
          Lantronix devices on the network and selects the first one.

        Once the device's IP address is determined, it establishes a Telnet
        connection to the device using the specified host and port.

        Raises:
            RuntimeError: If no devices are found during discovery.

        Returns:
            None
        """
        if self.__host is None and self.__MAC is not None:
            self.__host = await ldd.discover_lantronix_device(self.__MAC)
            if self.__host is None:
                raise RuntimeError(f"Device with MAC address {self.__MAC} not found")
        elif self.__host is None and self.__MAC is None:
            devices = await ldd.discover_lantronix_devices()
            if not devices:
                raise RuntimeError("No devices found")
            self.__host = devices[0]['IP']
            self.__MAC = devices[0]['MAC']
        self.__reader, self.__writer = await telnetlib3.open_connection(self.__host, self.__port)
    
    async def write(self, cmd: str):
        self.__writer.write(cmd)
        
    async def read_response(self) -> str:
        return await self.__reader.readuntil(b'\n')

    async def close(self):
        if self.__writer:
            self.__writer.close()
            self.__reader.close()

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



class SerialProtocol(TransportProtocol):
    """
    A class to handle serial communication with an NV200 device using the AioSerial library.
    Attributes:
        port (str): The serial port to connect to. Defaults to None. If port is None, the class
        will try to auto detect rthe port.
        xonxoff (bool): Whether to enable software flow control. Defaults to True.
        baudrate (int): The baud rate for the serial connection. Defaults to 115200.
        serial (AioSerial): The AioSerial instance for asynchronous serial communication.
    """
    __port : str
    __xonxoff : bool
    __baudrate : int
    
    def __init__(self, port : str = None, xonxoff : bool = True, baudrate : int = 115200):
        """
        Initializes the NV200 driver with the specified serial port settings.

        Args:
            port (str, optional): The serial port to connect to. Defaults to None.
            If port is None, the class will try to auto detect rthe port.
            xonxoff (bool, optional): Enables or disables software flow control (XON/XOFF). Defaults to True.
            baudrate (int, optional): The baud rate for the serial connection. Defaults to 115200.
        """
        self.__serial = None
        self.__port = port
        self.__xonxoff = xonxoff
        self.__baudrate = baudrate


    async def detect_port(self):
        """
        Asynchronously detects and configures the serial port for the NV200 device.

        This method scans through all available serial ports to find one with a 
        manufacturer matching "FTDI". If such a port is found, it attempts to 
        communicate with the device to verify if it is an NV200 device. If the 
        device is successfully detected, the port is configured and returned.

        Returns:
            str: The device name of the detected port if successful, otherwise None.

        Raises:
            Any exceptions raised during serial communication or port configuration 
            are not explicitly handled and will propagate to the caller.
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

    async def connect(self):
        """
        Establishes an asynchronous connection to the NV200 device using the specified serial port settings.

        This method initializes the serial connection with the given port, baud rate, and flow control settings.
        If the port is not specified, it attempts to automatically detect the NV200 device's port. If the device
        cannot be found, a RuntimeError is raised.

        Raises:
            RuntimeError: If the NV200 device cannot be detected or connected to.
        """
        self.__serial = aioserial.AioSerial(port=self.__port, xonxoff=self.__xonxoff, baudrate=self.__baudrate)
        if self.__port is None:
            self.__port = await self.detect_port()
        if self.__port is None:
            raise RuntimeError("NV200 device not found")


    async def write(self, cmd: str):
        await self.__serial.write_async(cmd.encode('utf-8'))

    async def read_response(self) -> str:
        return await self.__serial.readline_async()

    async def close(self):
        if self.__serial:
            self.__serial.close()

    @property
    def port(self) -> str:
        """
        Returns the serial port the device is connected to
        """
        return self.__port