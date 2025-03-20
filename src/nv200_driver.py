import asyncio
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
    async def write(self, cmd: str):
        """
        Sends a command to the NV200 device asynchronously.

        Args:
            cmd (str): The command string to be sent to the device.

        Raises:
            Exception: If there is an error while sending the command.
        """

    @abstractmethod
    async def read(self, cmd: str) -> str:
        """
        Sends a command to the device and reads the response asynchronously.

        Args:
            cmd (str): The command string to send to the device.

        Returns:
            str: The response received from the device.
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
        response = await self.read('\r')
        return response.startswith(b"NV200")



class TelnetTransport(TransportProtocol):
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

    async def read(self, cmd: str) -> str:
        self.__writer.write(cmd)
        return await self.__reader.readuntil(b'\n')

    async def close(self):
        if self.__writer:
            self.__writer.close()
            self.__reader.close()



class SerialTransport(TransportProtocol):
    """
    A class to handle serial communication with an NV200 device using the AioSerial library.
    Attributes:
        port (str): The serial port to connect to. Defaults to None. If port is None, the class
        will try to auto detect rthe port.
        xonxoff (bool): Whether to enable software flow control. Defaults to True.
        baudrate (int): The baud rate for the serial connection. Defaults to 115200.
        serial (AioSerial): The AioSerial instance for asynchronous serial communication.
    """
    
    def __init__(self, port = None, xonxoff = True, baudrate = 115200):
        """
        Initializes the NV200 driver with the specified serial port settings.

        Args:
            port (str, optional): The serial port to connect to. Defaults to None.
            If port is None, the class will try to auto detect rthe port.
            xonxoff (bool, optional): Enables or disables software flow control (XON/XOFF). Defaults to True.
            baudrate (int, optional): The baud rate for the serial connection. Defaults to 115200.
        """
        self.serial = None
        self.port = port
        self.xonxoff = xonxoff
        self.baudrate = baudrate


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
            self.serial.close()
            self.serial.port = port.device
            self.serial.open()
            if self.detect_device():
                return port.device
            else:
                self.serial.close()
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
        self.serial = aioserial.AioSerial(port=self.port, xonxoff=self.xonxoff, baudrate=self.baudrate)
        if self.port is None:
            self.port = await self.detect_port()
        if self.port is None:
            raise RuntimeError("NV200 device not found")


    async def write(self, cmd: str):
        await self.serial.write_async(cmd.encode('utf-8'))

    async def read(self, cmd: str) -> str:
        await self.serial.write_async(cmd.encode('utf-8'))
        return await self.serial.readline_async()

    async def close(self):
        if self.serial:
            self.serial.close()


class DeviceClient:
    def __init__(self, transport: TransportProtocol):
        self.transport = transport

    async def connect(self):
        await self.transport.connect()

    async def write(self, cmd: str):
        await self.transport.write(cmd + "\r")

    async def read(self, cmd: str) -> str:
        return await self.transport.read(cmd + "\r")

    async def close(self):
        await self.transport.close()


async def client_telnet():
    transport = TelnetTransport(MAC="00:80:A3:79:C6:18")
    #transport = TelnetTransport()
    client = DeviceClient(transport)
    await client.connect()

    response = await client.read('')
    print(f"Telnet - Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Telnet - Server response: {response}")
    await client.close()


async def client_serial():
    transport = SerialTransport()
    client = DeviceClient(transport)
    await client.connect()

    response = await client.read('')
    print(f"Serial - Server response: {response}")    
    await client.write('modsrc,0')
    await client.write('cl,1')
    await client.write('set,40')
    await asyncio.sleep(0.1)
    response = await client.read('meas')
    print(f"Serial - Server response: {response}")
    await client.close()


asyncio.run(client_telnet())
#asyncio.run(client_serial())
